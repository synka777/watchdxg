from playwright.async_api import async_playwright
from src.exceptions import NotLoggedInError
from functools import wraps
from environs import Env
from time import sleep
import asyncio
import random

env = Env()
env.read_env()

#################
# App state mgmt

class AsyncBrowserManager:
    # Class-level variables to store the singleton instance, browser context, and processing state
    _instance = None
    _browser = None
    _context = None
    _page = None
    _ready = False

    def __new__(cls):
        """
        We use __new__ to control how the class is created.
        If we didn't override __new__, an instance of the class would be
        created each time the class is called
        """

        # If an instance doesn't exist yet, create one and initialize the browser context
        # This is the part that actually enforces Singleton pattern behavior
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # @classmethod allows us to access the class itself (cls) instead of an instance (self).
    # It’s used for operations that should apply to the class level (like checking or setting the _instance variable).
    # @staticmethod could also be used here to initialize resources without needing to access any instance or class attributes directly.
    @classmethod
    async def init(cls):
        if cls._browser:
            return  # Singleton pattern - no need to initialize again

        try:
            playwright = await async_playwright().start()

            # Launch the browser (not persistent)
            cls._browser = await playwright.firefox.launch_persistent_context(
                user_data_dir=env.str('FFPROFILEPATH'),
                headless=True,
                viewport={'width': 1920, 'height': 6000},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0'
            )

            cls._page = cls._browser.pages[0] if cls._browser.pages else await cls._browser.new_page()

            # Go to the homepage
            await cls._page.goto('https://x.com/home', wait_until='domcontentloaded')

            # Wait for an element that confirms the page is loaded (e.g., header or navigation bar)
            await cls._page.wait_for_selector('header[role="banner"]', timeout=30000)

            cls._init = True
            print("BrowserManager ready")

        except Exception as e:
            print(f"[ERROR] Something went wrong: {e}")

    @classmethod
    def ready(cls):
        return cls._ready

    # No need to use async if we just return async class instances
    @classmethod
    def get_browser(cls):
        return cls._browser

    @classmethod
    def get_page(cls):
        return cls._page

    @classmethod
    async def get_new_page(cls):
        return await cls._browser.new_page()

    @classmethod
    async def logged_in(cls):
        try:
            # print('Are we logged in? Checking...')
            # Wait for the page to load properly and stabilize after login
            # Use a reliable element that shows up only after you're logged in (e.g., the navigation bar or profile menu)
            await cls._page.wait_for_selector('header[role="banner"]', timeout=15000)  # Increase timeout to 15 seconds
            # print('[INFO] Navigation bar is present — you are logged in!')

            # Check if the URL is correct after the login (it should no longer be on the login or flow page)
            current_url = cls._page.url
            # print(f'[DEBUG] Current URL: {current_url}')

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
    async def close(cls):
        if cls._browser:
            await cls._browser.close()
            cls._instance = None


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
def enforce_login(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        print('Decorator kicks in...')  # Debugging line
        if not AsyncBrowserManager.ready():
            await AsyncBrowserManager.init()
        try:
            if await AsyncBrowserManager.logged_in():
                # print('Already logged in!')  # Debugging line
                return await func(*args, **kwargs)
            else:
                print('Not logged in! Attempting automatic login...')
                await login(AsyncBrowserManager.get_page())
                if not await AsyncBrowserManager.logged_in():
                    raise NotLoggedInError('Login attempt failed')
                print('Login successful!')  # Debugging line
                return await func(*args, **kwargs)
        except NotLoggedInError as e:
            print('Error: Unable to login:', e)
            return  # Optionally return an error message or handle the failure
        except Exception as e:
            print(f'Unexpected error in decorator: {e}')
            raise # This is key to get the traceback when an exception is caught
    return wrapper


####################
# Regular functions

async def login(page):
    try: # These waits are just here for mimicing human behavior
        await asyncio.sleep(random.uniform(0.5, 1.2))        # Wait for the username field
        username_input = page.locator('input[autocomplete="username"]')
        await username_input.wait_for()

        await asyncio.sleep(random.uniform(0.5, 1.2))        # Wait for the username field
        await username_input.fill(env.str('USERNAME'))
        await asyncio.sleep(random.uniform(0.5, 1.2))        # Wait for the username field
        await username_input.press('Enter')

        # Check if the contact input is present by querying its count
        contact_input = page.locator('input[data-testid="ocfEnterTextTextInput"]')
        if await contact_input.count() > 0:
            # If the contact input exists, fill it and press enter
            await contact_input.fill(env.str('CONTACTINFO'))
            await contact_input.press('Enter')
            print('[INFO] Contact info entered.')
        else:
            print('[INFO] Contact info step skipped (input not found).')

        await send_password(page)

    except Exception as e:
        print(f'[ERROR] Login failed: {e}')
        return False

    return True


async def send_password(page):
    await asyncio.sleep(random.uniform(0.5, 1.2))
    password_input = page.locator('input[name="password"]')
    await password_input.wait_for()

    await asyncio.sleep(random.uniform(0.5, 1.2))
    await password_input.fill(env.str('PASSWORD'))
    await asyncio.sleep(random.uniform(0.5, 1.2))

    await password_input.press('Enter')