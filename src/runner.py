"""watchdxg-core
Copyright (c) 2025 Mathieu BARBE-GAYET
All Rights Reserved.
"""

from main.scraper import get_user_handles, get_user_data, get_post_instance
from main.infra import enforce_login, AsyncBrowserManager
from tools.utils import parse_args, filter_known
from main.db import setup_db, register_get_uid
from config import get_settings, env
import asyncio


@enforce_login
async def main(uid):
    # Initialize main variables
    user_handles: list[str] = []

    own_account = env.str('USERNAME')
    followers_url = f'https://x.com/{own_account}/followers'
    page = AsyncBrowserManager.get_page()

    # Then process the soup to get the user handle of each follower
    await page.goto(followers_url)
    user_handles = await get_user_handles()

    user_handles = filter_known(user_handles)

    if user_handles:
        tasks = [get_user_data(handle, uid) for handle in user_handles]
        followers = await asyncio.gather(*tasks, return_exceptions=True)

        for follower in followers:
            user_id = follower.insert()
            # # Then, get Post data from each HTML Element
            for article in follower.get_articles():
                xpost = get_post_instance(article, user_id)
                xpost.insert()
            pass
    else:
        print('[OK] No new users found')

    await AsyncBrowserManager.close()


async def start():
    get_settings() # Makes the app settings available during runtime
    args = parse_args()

    if args.setup:
        print('[INFO] Running with setup flag')
        if not setup_db():
            return

    if args.head:
        AsyncBrowserManager.disable_headless()

    uid = register_get_uid()
    if not uid:
        print('[ERROR] Unable to get account id')
        return
    await main(uid)


if __name__ == '__main__':
    asyncio.run(start())
