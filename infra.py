from playwright.sync_api import sync_playwright
from exceptions import NotLoggedInError
from functools import wraps
from environs import Env
from time import sleep
import random
import json
import os

env = Env()
env.read_env()

#################
# App state mgmt

class BrowserSingleton:
    # Class-level variables to store the singleton instance, browser context, and processing state
    _instance = None
    _browser = None
    _context = None
    _page = None

    def __new__(cls):
        """
        We use __new__ to control how the class is created.
        If we didn't override __new__, an instance of the class would be
        created each time the class is called
        """

        # If an instance doesn't exist yet, create one and initialize the browser context
        # This is the part that actually enforce Singleton pattern behavior
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._initialize_browser()
        return cls._instance

    # @classmethod allows us to access the class itself (cls) instead of an instance (self).
    # It’s used for operations that should apply to the class level (like checking or setting the _instance variable).
    # @staticmethod could also be used here to initialize resources without needing to access any instance or class attributes directly.
    @classmethod
    def _initialize_browser(cls):
        playwright = sync_playwright().start()

        # Launch the browser (not persistent)
        cls._browser = playwright.firefox.launch(headless=False)
        if os.path.exists('auth_state.json'):
            cls._context = cls._browser.new_context(
                # viewport={'width': 1920, 'height': 6000},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0',
                storage_state='auth_state.json'
            )
            print('✅ Cookies loaded from auth_state.json')
        else:
            cls._context = cls._browser.new_context(
                # viewport={'width': 1920, 'height': 6000},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0',
            )
        cls._page = cls._context.new_page()
        # cls.load_cookies()
        cls._page.goto('https://x.com/home', wait_until='load')

    @classmethod
    def save_auth_state(cls):
        if cls._context:
            cls._context.storage_state(path='auth_state.json')

    @classmethod
    def get_main_context(cls):
        if cls._context:
            return cls._context

    @classmethod
    def get_new_context(cls):
        return cls._browser.new_context(
                viewport={'width': 1920, 'height': 6000},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0',
                storage_state='auth_state.json'
            )

    @classmethod
    def get_page(cls):
        return cls._page

    # @classmethod
    # def load_cookies(cls):
    #     try:
    #         with open('auth_state.json', 'r') as f:
    #             cookies = json.load(f).get('cookies', [])
    #             cls._page.context.add_cookies(cookies)
    #             # Print cookies for verification
    #             current_cookies = cls._page.context.cookies()
    #             print(f"✅ Current cookies: {current_cookies}")
    #     except Exception as e:
    #         print(f"Failed to load cookies: {e}")

    @classmethod
    def logged_in(cls):
        try:
            # Wait for the page to load properly and stabilize after login
            # Use a reliable element that shows up only after you're logged in (e.g., the navigation bar or profile menu)
            cls._page.wait_for_selector('header[role="banner"]', timeout=15000)  # Increase timeout to 15 seconds
            print('✅ Navigation bar is present — you are logged in!')

            # Check if the URL is correct after the login (it should no longer be on the login or flow page)
            current_url = cls._page.url
            print(f'[DEBUG] Current URL: {current_url}')

            if 'login' in current_url or 'flow' in current_url:
                print('[DEBUG] Still on login page — probably not logged in.')
                return False

            return True

        except TimeoutError:
            print('[DEBUG] Timeout or Navigation bar not found — probably still on login page.')
            return False

        except Exception as e:
            print(f'[DEBUG] Unexpected error during login check: {e}')
            return False

    @classmethod
    def close_main_context(cls):
        """Closes the browser context and resets the singleton instance."""
        if cls._context:
            cls._context.close()
            cls._instance = None  # Allow re-instantiating later if needed

##################
# Decorators zone

# Decorator factory: when you need to pass custom parameters, returns the decorator function
def delay(min_sec=4, max_sec=6):
    def decorator(func): # Receives the function we’ll be decorating (func) as an arg
        @wraps(func) # Preserves the original function’s name, docstring, etc
        def wrapper(*args, **kwargs): # Defines the function that'll wrap the decorated func
            sleep_time = random.uniform(min_sec, max_sec)
            sleep(sleep_time)
            print(f'Sleeping for {sleep_time:.2f}s...')

            result = func(*args, **kwargs) # Decorated func is executed here
            return result # Returns the result of the decorated func
        return wrapper
    return decorator

# Decorator function: when you don't need to pass custom parameters
def ensure_logged_in(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print('Checking login status...')  # Debugging line
        try:
            if BrowserSingleton.logged_in():
                print('Already logged in!')  # Debugging line
                return func(*args, **kwargs)
            else:
                print('Not logged in! Attempting automatic login...')
                login(BrowserSingleton.get_page())
                if not BrowserSingleton.logged_in():
                    raise NotLoggedInError('Login attempt failed')
                print('Login successful!')  # Debugging line
                return func(*args, **kwargs)
        except NotLoggedInError as e:
            print('Error: Unable to login:', e)
            return  # Optionally return an error message or handle the failure
        except Exception as e:
            print(f'Unexpected error in decorator: {e}')
            return
    return wrapper



####################
# Regular functions


def login(page):
    # page.goto('https://x.com/i/flow/login')

    try: # These waits are just here for mimicing human behavior
        sleep(random.uniform(0.5, 1.2))
        # Wait for the username field
        username_input = page.locator('input[autocomplete="username"]')
        username_input.wait_for()

        sleep(random.uniform(0.5, 1.2))
        username_input.fill(env.str('USERNAME'))
        sleep(random.uniform(0.5, 1.2))
        username_input.press('Enter')

        # Check if the contact input is present by querying its count
        contact_input = page.locator('input[data-testid="ocfEnterTextTextInput"]')
        if contact_input.count() > 0:
            # If the contact input exists, fill it and press enter
            contact_input.fill(env.str('CONTACTINFO'))
            contact_input.press('Enter')
            print('✅ Contact info entered.')
        else:
            print('✅ Contact info step skipped (input not found).')

        send_password(page)
        BrowserSingleton.save_auth_state()
        print('✅ Auth state saved to auth_state.json')

    except Exception as e:
        print(f'[ERROR] Login failed: {e}')
        return False

    return True


def send_password(page):
    sleep(random.uniform(0.5, 1.2))
    password_input = page.locator('input[name="password"]')
    password_input.wait_for()

    sleep(random.uniform(0.5, 1.2))
    password_input.fill(env.str('PASSWORD'))
    sleep(random.uniform(0.5, 1.2))

    password_input.press('Enter')