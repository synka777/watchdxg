"""watchdxg-core
Copyright (c) 2025 Mathieu BARBE-GAYET
All Rights Reserved.
"""

from main.db import setup_db, register_get_uid, get_default_connection
from main.infra import enforce_login, AsyncBrowserManager
from main.extract import get_user_handles, get_user_data
from main.transform import transform_user_data
from config import env, parse_args
from tools.logger import logger
from config import settings
from yaspin import yaspin
from time import sleep
import asyncio


@enforce_login
async def main(uid):
    user_handles: list[str] = []

    # Go to the followers page with the browser manager
    own_account = env.str('USERNAME')
    followers_url = f'https://x.com/{own_account}/followers'
    page = AsyncBrowserManager.get_page()

    # Then process the soup to get the user handle of each follower
    await page.goto(followers_url)

    # EXTRACT:
    # Extract follower handles
    user_handles = await get_user_handles()

    if user_handles:
        async def trigger_extraction():
            tasks = [get_user_data(handle) for handle in user_handles]
            return await asyncio.gather(*tasks, return_exceptions=True)

        # Trigger data extraction for each follower
        if not settings['logs']['debug']:
            with yaspin(text='Extracting follower data') as spinner:
                followers_data = await trigger_extraction()
                spinner.ok('[OK]')
        else:
            followers_data = await trigger_extraction()

        # TRANSFORM:
        # At this point we have follower handles and raw HTML code from each follower profile
        for user_extract in followers_data:
            if user_extract.html:
                # Transform this data into relevant data types, get each follower/user's first posts
                xuser = transform_user_data(user_extract, uid)

                # LOAD:
                # Load the discovered followers and their first posts into DB
                # Triggers user insertion AND the insertion of its associated posts
                if xuser:
                    xuser.upsert()
    else:
        logger.info('[OK] No new users found')

    await AsyncBrowserManager.close()


async def start():
    """
    Prepares the pipeline for data processing:
    - Argument parsing
    - X account insertion in DB

    The account credentials are stored in the .env file
    """
    args = parse_args()

    if args.dev:
        logger.info('Running in development mode')

    if args.head:
        AsyncBrowserManager.disable_headless()

    if args.setup:
        logger.info('Running with setup flag')
        if not setup_db(): # If the setup failed, stop the pipeline
            return


    uid = register_get_uid()

    if not uid:
        logger.error('Unable to get account id')
        return

    await main(uid)


if __name__ == '__main__':
    asyncio.run(start())
