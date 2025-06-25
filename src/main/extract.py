from main.infra import enforce_login, AsyncBrowserManager, apply_concurrency_limit
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from classes.entities import UserExtract
from tools.logger import logger
from bs4 import BeautifulSoup
from config import settings
import asyncio
import random


MAX_PARALLEL = settings['runtime']['max_parallel']
semaphore = asyncio.Semaphore(MAX_PARALLEL) # Defined at module level to ensure all tasks use the same semaphore (limit count)


@apply_concurrency_limit(semaphore)
async def get_user_data(handle):
    logger.debug(f'Extracting data from {handle}')

    max_retries = settings['runtime']['max_retries']
    for attempt in range(max_retries):
        try:
            # Using one context per get_usr_data() call is lighter
            # than instanciating one browser per call instead
            page = await AsyncBrowserManager.get_new_page()
            url = f'https://x.com/{handle}/with_replies'
            await page.goto(url)

            # Wait for one of the last elements of the page to load and THEN get the DOM
            await page.wait_for_selector('section[role="region"]')
            await asyncio.sleep(random.uniform(5, 6))
            html = await page.content()

            logger.debug(f'Done: {handle}')
            return UserExtract(handle, html)

        except (PlaywrightTimeoutError, Exception) as e:
                logger.warning(f'Attempt {attempt+1} failed for {handle}: {e}')
                if attempt == max_retries - 1:
                    logger.error(f'Giving up on {handle} after {max_retries} attempts.')
                else:
                    await asyncio.sleep(2 + attempt * 2)  # Exponential backoff

        finally:
            try:
                await page.close()
            except Exception:
                pass


@enforce_login
async def get_user_handles():
        page = AsyncBrowserManager.get_page()
        # Here we use "first" because multiple elements can be returned w/ this selector
        await page.locator('button[data-testid="UserCell"]').first.wait_for(timeout=10000)
        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')
        followers_section = soup.find('section', attrs={'role': 'region'})
        followers = followers_section.find_all(attrs={'data-testid': 'UserCell'})

        user_handles: list[str] = []
        # Get each follower's handle here
        for follower in followers:
            a_elem = follower.find('a', {'role':'link', 'aria-hidden': 'true'})
            if a_elem.has_attr('href'):
                user_handles.append(a_elem['href'][1:])

        return user_handles