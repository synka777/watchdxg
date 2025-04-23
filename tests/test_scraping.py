from src.utils import str_to_int
from bs4 import BeautifulSoup
from datetime import datetime
from environs import Env
from pathlib import Path
from time import sleep
import random
import re

###################
# Helper functions

def login(page):
    try: # These waits are just here for mimicing human behavior
        env = Env()
        env.read_env()

        sleep(random.uniform(0.5, 1.2))
        # Wait for the username field
        username_input = page.locator('input[autocomplete="username"]')
        # print(page.locator('input[autocomplete="username"]').count())  # Check if the element exists
        username_input.wait_for()
        sleep(random.uniform(0.5, 1.2))        # Wait for the username field
        username_input.fill(env.str('USERNAME'))
        sleep(random.uniform(0.5, 1.2))        # Wait for the username field
        username_input.press('Enter')

        # Check if the contact input is present by querying its count
        contact_input = page.locator('input[data-testid="ocfEnterTextTextInput"]')
        sleep(random.uniform(4, 6)) # Let some spare time for the contact form to appear

        if contact_input.count() > 0:
            # If the contact input exists, fill it and press enter
            contact_input.fill(env.str('CONTACTINFO'))
            contact_input.press('Enter')
            print('[INFO] Contact info entered.')
        else:
            print('[INFO] Contact info step skipped (input not found).')

        send_password(page)

    except Exception as e:
        print(f'[ERROR] Login failed: {e}')
        return False

    # Save the entire session state (cookies + local storage + session storage)
    profile_dir = Path(__file__).parent / "playwright_profile"
    profile_dir.mkdir(exist_ok=True)

    # Path to save the storage state
    storage_file = profile_dir / "storage_state.json"

    # Allows time for localStorage & sessionStorage to be populated before the dump
    page.wait_for_timeout(6000)

    # Save session state to the storage file
    page.context.storage_state(path=str(storage_file))

    print(f"Storage state saved to {storage_file}")

    # After login, inspect localStorage and sessionStorage
    page.evaluate("console.log(localStorage); console.log(sessionStorage);")

    return True


def send_password(page):
    env = Env()
    env.read_env()

    sleep(random.uniform(0.5, 1.2))
    password_input = page.locator('input[name="password"]')
    password_input.wait_for()

    sleep(random.uniform(0.5, 1.2))
    password_input.fill(env.str('PASSWORD'))

    sleep(random.uniform(0.5, 1.2))
    password_input.press('Enter')


########################
# Unit tests: Home page

def test_login(page):
    """Ensure we're logged in before moving on to other tests"""
    # page = AsyncBrowserManager.get_page()
    page.goto('https://x.com/home', timeout=6000)
    current_url = page.url

    if 'login' in current_url or 'flow' in current_url:
        print('[INFO] Attempting autologin...')
        login(page)

    # user_agent = page.evaluate("() => navigator.userAgent")
    # print(user_agent)

    # Wait for the button to be visible
    page.wait_for_selector('article[data-testid="tweet"]')
    html = page.content()

    # Parse the HTML with BeautifulSoup and check if 'article' is present
    soup = BeautifulSoup(html, 'html.parser')
    assert soup.find('article') is not None


########################
# Unit tests: Followers

def test_get_usercell(page):
    """Followers page: Are individual follower main wrapper still reachable"""

    env = Env()
    env.read_env()
    username = env.str("USERNAME")
    page.goto(f'https://x.com/{username}/followers', timeout=6000)

    # Instead of waiting for networkidle, wait for the button itself
    page.locator('button[data-testid="UserCell"]').first.wait_for(timeout=6000)

    html = page.content()
    soup = BeautifulSoup(html, 'html.parser')

    # Looking for the button with the specific data-testid attribute
    user_cell = soup.find(attrs={"data-testid": "UserCell"})

    # Assert that the UserCell button exists in the page content
    assert user_cell is not None, "UserCell button not found"


def test_followers_section(page):
    """Followers page: Is the follower list's main wrapper still reachable"""
    env = Env()
    env.read_env()
    username = env.str("USERNAME")
    page.goto(f'https://x.com/{username}/followers', timeout=6000)

    # Wait for an element that's one of the last elements to be loaded
    page.locator('button[data-testid="UserCell"]').first.wait_for(timeout=6000)

    # Then get the actual element we're looking for
    html = page.content()
    soup = BeautifulSoup(html, 'html.parser')

    followers_section = soup.find('section', attrs={'role': 'region'})
    assert followers_section is not None


def test_get_user_handle(page):
    """Followers page: Can we still get user handles"""
    env = Env()
    env.read_env()
    username = env.str("USERNAME")
    page.goto(f'https://x.com/{username}/followers', timeout=6000)

    page.locator('button[data-testid="UserCell"]').first.wait_for(timeout=6000)

    html = page.content()
    soup = BeautifulSoup(html, 'html.parser')

    a = soup.find('a', {'role':'link', 'aria-hidden': 'true'})
    handle = None
    if a.has_attr('href'):
        handle = a['href']
    assert handle is not None and isinstance(handle, str)


###########################
# Unit tests: User profile

def test_get_username(page):
    """User page: Can we get the username"""
    env = Env()
    env.read_env()
    username = env.str("USERNAME")
    page.goto(f'https://x.com/{username}', timeout=6000)

    page.locator('article[data-testid="tweet"]').first.wait_for(timeout=6000)

    html = page.content()
    soup = BeautifulSoup(html, 'html.parser')

    user_name_wrapper = soup.find('div', attrs={'data-testid': 'UserName'})
    user_name_elem = next(
        (div for div in user_name_wrapper.find_all('div')
        if div.get_text(strip=True) and not div.find('div')),  # Ensure no nested <div>
        None
    )
    username = user_name_elem.text.strip()

    assert username is not None and isinstance(username, str)


def test_get_user_bio(page):
    """User page: Can we get the user bio"""
    env = Env()
    env.read_env()
    username = env.str("USERNAME")
    page.goto(f'https://x.com/{username}', timeout=6000)

    page.locator('article[data-testid="tweet"]').first.wait_for(timeout=6000)

    html = page.content()
    soup = BeautifulSoup(html, 'html.parser')

    bio_elem_wrapper = soup.find(attrs={'data-testid': 'UserDescription'})
    bio_elem = next(
        (div for div in bio_elem_wrapper.find_all('span')
        if div.get_text(strip=True)),
        None
    )
    bio = bio_elem.text.strip()

    assert bio is not None and isinstance(bio, str)


def test_get_user_join_date(page):
    """User page: Can we get the join date"""
    env = Env()
    env.read_env()
    username = env.str("USERNAME")
    page.goto(f'https://x.com/{username}', timeout=6000)

    page.locator('article[data-testid="tweet"]').first.wait_for(timeout=6000)

    html = page.content()
    soup = BeautifulSoup(html, 'html.parser')

    date_pattern = re.compile(r'\d{4}')
    joined_elem = soup.find(attrs={'data-testid': 'UserJoinDate'}).find('span', string=date_pattern)
    date_str_list = joined_elem.text.strip().split(' ')[-2:]
    date_str = ' '.join(date_str_list)
    date_joined = datetime.strptime(date_str, '%B %Y')

    assert isinstance(date_joined, datetime)


def test_get_followers_count(page):
    """User page: Can we get the followers count"""
    env = Env()
    env.read_env()
    username = env.str("USERNAME")
    page.goto(f'https://x.com/{username}', timeout=6000)

    page.locator('article[data-testid="tweet"]').first.wait_for(timeout=6000)

    html = page.content()
    soup = BeautifulSoup(html, 'html.parser')

    number_pattern = re.compile(r'\d( (M|k))?')
    following_elem = soup.find('a', attrs={'href': f'/{username}/following'}).find('span', string=number_pattern)
    following_int = str_to_int(following_elem.text)

    assert isinstance(following_int, int)


def test_get_following_count(page):
    """User page: Can we get the following count"""
    env = Env()
    env.read_env()
    username = env.str("USERNAME")
    page.goto(f'https://x.com/{username}', timeout=6000)

    page.locator('article[data-testid="tweet"]').first.wait_for(timeout=6000)

    html = page.content()
    soup = BeautifulSoup(html, 'html.parser')

    number_pattern = re.compile(r'\d( (M|k))?')
    followers_elem = soup.find('a', attrs={'href': f'/{username}/verified_followers'}).find('span', string=number_pattern)
    followers_int = str_to_int(followers_elem.text)

    assert isinstance(followers_int, int)


def test_get_website(page):
    """User page: Can we get the user's featured website"""
    env = Env()
    env.read_env()
    username = env.str("USERNAME")
    page.goto(f'https://x.com/{username}', timeout=6000)

    page.locator('article[data-testid="tweet"]').first.wait_for(timeout=6000)

    html = page.content()
    soup = BeautifulSoup(html, 'html.parser')

    # profile_header: only available on profiles that include a location and/or a website
    profile_header = soup.find(attrs={'data-testid': 'UserProfileHeader_Items'})
    user_url = profile_header.find(attrs={'data-testid': 'UserUrl'})
    url = user_url['href'] if user_url.has_attr('href') else None

    assert url is not None