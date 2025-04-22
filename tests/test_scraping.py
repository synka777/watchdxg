from bs4 import BeautifulSoup
from environs import Env
from pathlib import Path
from time import sleep
import random


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
    page.goto('https://x.com/home', wait_until='networkidle')  # Wait until network activity is idle
    current_url = page.url

    if not ('login' in current_url or 'flow' in current_url):
        print('[INFO] Already logged in')
        return

    user_agent = page.evaluate("() => navigator.userAgent")
    print(user_agent)

    login(page)

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
    page.goto(f'https://x.com/{username}/followers', timeout=10000)

    # Instead of waiting for networkidle, wait for the button itself
    page.locator('button[data-testid="UserCell"]').first.wait_for(timeout=10000)

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
    page.goto(f'https://x.com/{username}/followers', timeout=10000)

    # Wait for an element that's one of the last elements to be loaded
    page.locator('button[data-testid="UserCell"]').first.wait_for(timeout=10000)

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
    page.goto(f'https://x.com/{username}/followers', timeout=10000)

    page.locator('button[data-testid="UserCell"]').first.wait_for(timeout=10000)

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
    page.goto(f'https://x.com/{username}/followers', timeout=10000)

    page.locator('button[data-testid="UserCell"]').first.wait_for(timeout=10000)

    html = page.content()
    soup = BeautifulSoup(html, 'html.parser')


    assert ''


def test_get_user_bio(page):
    """User page: Can we get the user bio"""
    env = Env()
    env.read_env()
    username = env.str("USERNAME")
    page.goto(f'https://x.com/{username}/followers', timeout=10000)

    page.locator('button[data-testid="UserCell"]').first.wait_for(timeout=10000)

    html = page.content()
    soup = BeautifulSoup(html, 'html.parser')


    assert ''


def test_get_user_join_date(page):
    """User page: Can we get the join date"""
    env = Env()
    env.read_env()
    username = env.str("USERNAME")
    page.goto(f'https://x.com/{username}/followers', timeout=10000)

    page.locator('button[data-testid="UserCell"]').first.wait_for(timeout=10000)

    html = page.content()
    soup = BeautifulSoup(html, 'html.parser')


    assert ''


def test_get_followers_count(page):
    """User page: Can we get the followers count"""
    env = Env()
    env.read_env()
    username = env.str("USERNAME")
    page.goto(f'https://x.com/{username}/followers', timeout=10000)

    page.locator('button[data-testid="UserCell"]').first.wait_for(timeout=10000)

    html = page.content()
    soup = BeautifulSoup(html, 'html.parser')


    assert ''


def test_get_following_count(page):
    """User page: Can we get the following count"""
    env = Env()
    env.read_env()
    username = env.str("USERNAME")
    page.goto(f'https://x.com/{username}/followers', timeout=10000)

    page.locator('button[data-testid="UserCell"]').first.wait_for(timeout=10000)

    html = page.content()
    soup = BeautifulSoup(html, 'html.parser')


    assert ''


def test_get_url(page):
    """User page: Can we get"""
    env = Env()
    env.read_env()
    username = env.str("USERNAME")
    page.goto(f'https://x.com/{username}/followers', timeout=10000)

    page.locator('button[data-testid="UserCell"]').first.wait_for(timeout=10000)

    html = page.content()
    soup = BeautifulSoup(html, 'html.parser')


    assert ''


def test_get_url_display_text(page):
    """User page: Can we get Th user's """
    env = Env()
    env.read_env()
    username = env.str("USERNAME")
    page.goto(f'https://x.com/{username}/followers', timeout=10000)

    page.locator('button[data-testid="UserCell"]').first.wait_for(timeout=10000)

    html = page.content()
    soup = BeautifulSoup(html, 'html.parser')


    assert ''