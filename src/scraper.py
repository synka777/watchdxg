from infra import enforce_login, AsyncBrowserManager, apply_concurrency_limit
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from tools.utils import get_settings, settings, str_to_int
from bs4 import BeautifulSoup
from datetime import datetime
from classes import XUser
from classes import Post
from environs import Env
from time import sleep
import asyncio
import random
import locale
import re

env = Env()
env.read_env()
locale.setlocale(locale.LC_TIME, env.str('LOCALE'))
get_settings() # Makes the app settings available during runtime
MAX_PARALLEL = settings['runtime']['max_parallel']
semaphore = asyncio.Semaphore(MAX_PARALLEL) # Defined at module level to ensure all tasks use the same semaphore (limit count)


def block_user():
    pass


# @enforce_login
@apply_concurrency_limit(semaphore)
async def get_user_data(handle, uid, follower=True):
    max_retries = settings['runtime']['max_retries']
    for attempt in range(max_retries):
        try:
            # Using one context per get_usr_data() call is lighter
            # than instanciating one browser per call instead
            page = await AsyncBrowserManager.get_new_page()
            url = f'https://x.com/{handle}'
            await page.goto(url)

            # Wait for one of the last elements of the page to load and THEN get the DOM
            await page.wait_for_selector('section[role="region"]')
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')

            user_name_wrapper = soup.find('div', attrs={'data-testid': 'UserName'})
            user_name_elem = next(
                (div for div in user_name_wrapper.find_all('div')
                if div.get_text(strip=True) and not div.find('div')),  # Ensure no nested <div>
                None
            )

            bio_elem_wrapper = soup.find(attrs={'data-testid': 'UserDescription'})
            if bio_elem_wrapper:
                bio_elem = next(
                    (div for div in bio_elem_wrapper.find_all('span')
                    if div.get_text(strip=True)),
                    None
                )

            date_pattern = re.compile(r'\d{4}')
            joined_elem = soup.find(attrs={'data-testid': 'UserJoinDate'}).find('span', string=date_pattern)
            date_str_list = joined_elem.text.strip().split(' ')[-2:]
            date_str = ' '.join(date_str_list)
            date_joined = datetime.strptime(date_str, '%B %Y')

            number_pattern = re.compile(r'\d( (M|k))?')
            following_elem = soup.find('a', attrs={'href': f'/{handle}/following'}).find('span', string=number_pattern)
            following_int = str_to_int(following_elem.text)
            followers_elem = soup.find('a', attrs={'href': f'/{handle}/verified_followers'}).find('span', string=number_pattern)
            followers_int = str_to_int(followers_elem.text)

            # profile_header: only available on profiles that include a location and/or a website
            profile_header = soup.find(attrs={'data-testid': 'UserProfileHeader_Items'})
            if profile_header:
                user_url = profile_header.find(attrs={'data-testid': 'UserUrl'})
                if user_url:
                    url_pattern = re.compile(r'\w+\.\w+(\/\w+)?')
                    redirected_url = user_url.find(string=url_pattern)

            username = user_name_elem.text.strip()
            bio = bio_elem.text if bio_elem_wrapper and bio_elem else None
            # Display url could be cropped but should be enough to get the domain name and first url params
            # Switch to user_url['href'] and follow url with playwright to get the full actual link if needed
            redirected_url = redirected_url.text if user_url and redirected_url else None

            print('Username:', username)
            if bio_elem_wrapper:
                print('Bio:', bio)
            print('Joined:', date_joined)
            print('Followers:', followers_int)
            print('Following:', following_int)
            if profile_header and user_url:
                print('User URL:', user_url['href'], redirected_url)

            return XUser(
                uid,
                handle, username,
                bio, date_joined,
                following_int,
                followers_int,
                redirected_url,
                follower
            )

        except (PlaywrightTimeoutError, Exception) as e:
            print(f'[WARN] Attempt {attempt+1} failed for {handle}: {e}')
            if attempt == max_retries - 1:
                print(f'[ERROR] Giving up on {handle} after {max_retries} attempts.')
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
            print('Follower:', a_elem['href'][1:])
            user_handles.append(a_elem['href'][1:])

    return user_handles


# def is_rock_bottom(driver):
#     return driver.execute_script("""
#             var scrollable = document.documentElement || document.body;
#             return (scrollable.scrollHeight - scrollable.scrollTop) <= scrollable.clientHeight;
#         """)


# # function to handle dynamic page content loading - using Selenium
# def scroll(driver):
#     driver.execute_script('window.scrollBy(0, document.body.scrollHeight/10);')
#     new_height = driver.execute_script('return document.body.scrollHeight')
#     return new_height


# def clean_stat(stat):
#     return stat.replace('0', '') if stat.startswith('0') else stat


# def get_stats(stats_grp, stat_pos):
#     subset = stats_grp[stat_pos].select('span span')
#     return str(0) if not bool(subset[0].select('span')) else subset[0].select('span')[0].text


@enforce_login
def get_posts(driver, url): # TODO: Revamp this function w/ new logic AND playwright
    # This function will parse the dom and store each info in a map
    # It then will return this map to the main function
    driver.get(url)
    sleep(random.uniform(1, 3))
    batch = []
    pos_history = [0]
    i = 0
    while True:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        for post_element in soup.findAll('article', {'data-testid': 'tweet'}):
            print('')
            # Get the social context for the current post

            # Is it a repost?
            is_reposted = True if bool(
                post_element.select('span', {'data-testid': 'socialContext'})[0].select('span span span')) else False
            # Is it a reply?
            in_reply_to = []
            # Case 1: handle posts that include "Replying to <someone>", happens when making an advanced search
            reply_container = post_element.select('div div div div div div')[0].select('div a span')

            if len(reply_container) > 4:
                repl = True if bool(reply_container[4].text.startswith('@')) else False

                if repl:
                    in_reply_to.append(reply_container[4].text)
                    if len(reply_container) > 5:
                        if reply_container[5].text.startswith('@') and len(in_reply_to) > 0:
                            in_reply_to.append(reply_container[5].text)

            # TODOold: Case 2: handle posts that are directly displayed under the original post

            # posted_by_at_grp is a bunch of nested elements that stores the username, handle, datetime, etc
            posted_by_at_grp = post_element.select('div', {'data-testid': 'User-Name'})[0]
            display_name = posted_by_at_grp.select('a > div > div > span > span')[0].text
            user_handle = posted_by_at_grp.select('div > div > div > a > div > span')[0].text
            timestamp = posted_by_at_grp.select('time')[0]['datetime']
            href = posted_by_at_grp.select('div div div a')[-1]['href'].replace('/analytics', '')
            post_id = href.split('/')[-1]

            # stats_grp is a web element group composing the social interaction statistics
            stats_grp = post_element.select('span[data-testid="app-text-transition-container"]')
            replies = get_stats(stats_grp, 0)
            reposts = get_stats(stats_grp, 1)
            likes = get_stats(stats_grp, 2)
            views = get_stats(stats_grp, 3) if len(stats_grp) > 3 else str(0)

            # For some reason, tweet_text includes unwanted strings, remove it
            trim_head_str = f'{display_name}{user_handle}·{posted_by_at_grp.select("time")[0].text}'
            trim_tail_str = clean_stat(replies) + clean_stat(reposts) + clean_stat(likes) + clean_stat(views)

            tweet_text = post_element.select('div', {'data-testid': 'tweetText'})[0].text.replace(trim_head_str, '')

            if tweet_text.endswith(trim_tail_str):
                tweet_text = tweet_text[: -len(trim_tail_str)]

            post = Post(post_id, timestamp, href, is_reposted, in_reply_to,
                        display_name, user_handle, tweet_text, replies, reposts, likes, views)

            if not any(saved_post.post_id == timestamp for saved_post in batch):
                batch.append(post)
                print('NEW POST: ', i)
                print(f'post_id: {post_id}')
                print(f'TimeStamp: {timestamp}')
                print(f'href: {href}')
                print(f'is_reposted: {is_reposted}')
                print(f'in_reply_to: {" ".join(map(str, in_reply_to))}')
                print(f'DisplayName: {display_name}')
                print(f'Handle: {user_handle}')
                print(f'tweet_text: {tweet_text}')
                print('Replies: ', replies, 'Reposts: ', reposts, 'Likes: ', likes, 'Views: ', views)
            i += 1

        rock_bottom = False
        retries = 0
        max_retries = 3
        error = False
        while not rock_bottom:
            # Get the height_pos position
            height_pos = scroll(driver)
            if retries > 0:
                print(f'Trying again... {retries}/{max_retries}')
                # body = driver.find_element(By.TAG_NAME, "body")
                # body.send_keys(Keys.PAGE_DOWN)

            # If the new and last height_pos values are the same we might've reached the bottom of the page.
            if height_pos == pos_history[-1]:
                if not is_rock_bottom(driver):
                    retries += 1
                    print('Same height position')
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    print('Trying a blast to half the page...')
                    print(driver.execute_script('return document.body.scrollHeight'))
                    # driver.execute_script("""
                    #     var lazyImages = document.querySelectorAll('img[data-src], video[data-src]');
                    #     lazyImages.forEach(function(img) {
                    #         img.src = img.getAttribute('data-src');
                    #     });
                    # """)
                    # driver.execute_script("""
                    #     // Hide potential blocking elements (e.g., ads, modals, etc.)
                    #     var overlays = document.querySelectorAll('.ad, .modal, .sticky');
                    #     overlays.forEach(function(element) {
                    #         element.style.display = 'none';
                    #     });
                    # """)
                    # driver.execute_script("""
                    #     // Disable auto-refresh or prevent JavaScript-driven reloads
                    #     window.onbeforeunload = null;
                    #     window.location.reload = function(){};
                    #     window.history.pushState({}, "", window.location.href);
                    # """)
                    if retries > max_retries:
                        print('ERROR! Was unable to scroll any further')
                        error = True
                        break
                else:
                    rock_bottom = True
            else:
                # If we have moved, then add the current position into the height position history
                pos_history.append(height_pos)
                break
            sleep(random.uniform(4, 5))

        sleep(random.uniform(4, 5))
        # Exit posts retrieval
        if rock_bottom:
            print('Done. Got ', len(batch), ' posts')
            break
        if error:
            break