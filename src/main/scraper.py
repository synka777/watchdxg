from main.infra import enforce_login, AsyncBrowserManager, apply_concurrency_limit
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from tools.utils import str_to_int, get_stats, clean_stat
from classes.entities import UserExtract, XUser, XPost
from config import settings
from bs4 import BeautifulSoup
from dateutil import parser
import asyncio
import re

MAX_PARALLEL = settings['runtime']['max_parallel']
semaphore = asyncio.Semaphore(MAX_PARALLEL) # Defined at module level to ensure all tasks use the same semaphore (limit count)

# @apply_concurrency_limit(semaphore)
def get_post_instance(post_elem, user_handle):
    """Get all data from a given a post
    Args:
        post_elem <article> tag and its content
        user_id: The user ID that post is attached to
        user_handle: The current user's handle
    Returns:
        A UserExtract instance to pass to transform() or None if the post is not a repost or from current user
    """

    #######################################
    # Step 1: Get handle and repost status

    reposted = True if bool(post_elem.select('span[data-testid="socialContext"]')) else False

    # posted_by_at_grp is a bunch of nested elements that stores the username, handle, datetime, in its two children
    posted_by_at_grp = post_elem.find('div', {'data-testid': 'User-Name'})
    pbag_children = posted_by_at_grp.find_all('div', recursive=False)

    userhandle_dt_wrapper = pbag_children[1]

    handle_elem = next( # Search for the next span with text
        (span for span in userhandle_dt_wrapper.find_all('span')
        if span.get_text(strip=True) and not span.find('span')),
        None
    )

    # If the username is only composed of emojis (=None), use handle as username instead
    handle = handle_elem.get_text()[1:]

    # Now that we know the handle of the current post,
    # if it's not from the currently evaluated user AND it's not reposed by it neither, return None
    if not reposted:
        if not handle == user_handle:
            print('[INFO]: Post discarded')
            return

    ###################################
    # Step 2: Get the rest of the data

    # If the current post is relevant, process the rest of the data
    username_wrapper = pbag_children[0]
    username_elem = next( # Search for the next span with text
        (span for span in username_wrapper.find_all('span')
        if span.get_text(strip=True) and not span.find('span')),
        None
    )

    username = handle[1:] if not username_elem else username_elem.get_text()
    timestamp = userhandle_dt_wrapper.find('time')['datetime']


    href_elem = None
    for a in userhandle_dt_wrapper.find_all('a'):
        if a['href'] and 'status/' in a['href']:
            if not a.find('a'):
                href_elem = a

    post_id = href_elem['href'].split('/')[-1]

    # stats_grp is a web element group composing the social interaction statistics
    stats_grp = post_elem.select('span[data-testid="app-text-transition-container"]')
    replies = get_stats(stats_grp, 0)
    reposts = get_stats(stats_grp, 1)
    likes = get_stats(stats_grp, 2)
    views = get_stats(stats_grp, 3) if len(stats_grp) > 3 else str(0)

    # For some reason, tweet_text includes unwanted strings, remove it
    trim_head_str = f'{username}{handle}·{posted_by_at_grp.select("time")[0].text}'
    trim_tail_str = clean_stat(replies) + clean_stat(reposts) + clean_stat(likes) + clean_stat(views)

    # Prepare stats for the upcoming DB storage
    replies = str_to_int(replies)
    reposts = str_to_int(likes)
    likes = str_to_int(likes)
    views = str_to_int(views)

    tweet_text = post_elem.select('div', {'data-testid': 'tweetText'})[0].text.replace(trim_head_str, '')

    if tweet_text.endswith(trim_tail_str):
        tweet_text = tweet_text[: -len(trim_tail_str)]

    print('-----')
    print(f'Post_id: {post_id}')
    print(f'Username: {username}')
    print(f'TimeStamp: {timestamp}')
    print(f'Handle: {handle}')
    print(f'Text: {tweet_text}')
    print('Replies: ', replies, 'Reposts: ', reposts, 'Likes: ', likes, 'Views: ', views)
    print(f'Reposted: {reposted}')


    ###############################
    # Step 3: Return post instance

    return XPost(
        post_id, timestamp, username, handle, tweet_text,
        replies, reposts, likes, views, reposted
    )


def transform(user_extract: UserExtract, uid, follower=True):
    """Get all data for a given user
    Args:
        user_extract: class to pass handle/html data to this function
        uid: The account ID that user is attached to
        follower: Boolean, depends on the caller's location/context
    Returns:
        A XUser instance to pass to the next layer
    """
    try:
        soup = BeautifulSoup(user_extract.html, 'html.parser')

        user_name_wrapper = soup.find('div', attrs={'data-testid': 'UserName'})
        user_name_elem = next(
            (div for div in user_name_wrapper.find_all('div')
            if div.get_text(strip=True) and not div.find('div')),  # Ensure no nested <div>
            None
        )

        certified = True if user_name_wrapper.find('svg', attrs={'data-testid': 'icon-verified'}) else False

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
        date_joined = parser.parse(date_str) # Use datutil parser instead of datetime.strptime, works for any locale

        number_pattern = re.compile(r'\d( (M|k))?')

        following_elem = soup.find('a', attrs={'href': f'/{user_extract.handle}/following'}).find('span', string=number_pattern)
        following_str = following_elem.text
        following_int = str_to_int(following_str)

        followers_elem = soup.find('a', attrs={'href': f'/{user_extract.handle}/verified_followers'}).find('span', string=number_pattern)
        followers_str = followers_elem.text
        followers_int = str_to_int(followers_str)

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

        # Get user posts
        feed_region = soup.find('section', {'role': 'region'})

        xuser = XUser(
            uid,
            user_extract.handle,
            username, certified,
            bio, date_joined,
            following_int,
            followers_int,
            following_str,
            followers_str,
            redirected_url,
            follower
        )

        print('XUser instance:', xuser)
        print('Type of xuser:', type(xuser))
        print('XUser dict:', xuser.__dict__)
        articles = feed_region.findAll('article', {'data-testid': 'tweet'})
        print('LEN', len(articles))
        for article in articles:
            try:
                xpost = get_post_instance(article, user_extract.handle)
                print('[DEBUG] xpost =', xpost)
                if xpost:
                    print('[DEBUG] About to call add_article()')
                    print('add_article method:', xuser.add_article)
                    xuser.add_article(xpost)
            except Exception as e:
                print('[ERROR] Article loop failed:', e)


        print('Username:', username)
        print('Certified:', certified)
        if bio_elem_wrapper:
            print('Bio:', bio)
        print('Joined:', date_joined)
        print('Followers:', followers_int)
        print('Following:', following_int)
        if profile_header and user_url:
            print('User URL:', user_url['href'], redirected_url)
        print('-----')

        return xuser

    except (Exception) as e:
        print(f'[ERROR] Unable to get data: {e}')


@apply_concurrency_limit(semaphore)
async def extract(handle):
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
            await asyncio.sleep(5)
            html = await page.content()

            return UserExtract(handle, html)

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
            user_handles.append(a_elem['href'][1:])

    return user_handles