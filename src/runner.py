"""watchdxg-core
Copyright (c) 2025 Mathieu BARBE-GAYET
All Rights Reserved.
"""

from main.scraper import get_user_handles, extract, transform
from main.infra import enforce_login, AsyncBrowserManager
from tools.utils import filter_known
from main.db import setup_db, register_get_uid
from config import env, parse_args
from tools.logger import logger
import asyncio


@enforce_login
async def main(uid, noupdate):
    # Initialize main variables
    user_handles: list[str] = []

    own_account = env.str('USERNAME')
    followers_url = f'https://x.com/{own_account}/followers'
    page = AsyncBrowserManager.get_page()

    # Then process the soup to get the user handle of each follower
    await page.goto(followers_url)

    # Extract
    user_handles = await get_user_handles()
    if noupdate:
        user_handles = filter_known(user_handles)

    if user_handles:
        tasks = [extract(handle) for handle in user_handles]
        followers_data = await asyncio.gather(*tasks, return_exceptions=True)

        for user_extract in followers_data:
            # Transform
            xuser = transform(user_extract, uid)

            # Load
            # Triggers user insertion AND the insertion of its associated posts
            xuser.upsert()

    else:
        logger.info('[OK] No new users found')

    await AsyncBrowserManager.close()


async def start():
    args = parse_args()

    if args.setup:
        logger.info('Running with setup flag')
        if not setup_db():
            return

    if args.head:
        AsyncBrowserManager.disable_headless()

    noupdate = True if args.noupdate else False


    uid = register_get_uid()
    if not uid:
        logger.error('Unable to get account id')
        return
    await main(uid, noupdate)


if __name__ == '__main__':
    asyncio.run(start())
