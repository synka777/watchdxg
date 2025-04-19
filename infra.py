from playwright.sync_api import sync_playwright
from exceptions import NotLoggedInError
from functools import wraps
from environs import Env
from time import sleep
import random
import time

env = Env()
env.read_env()

#################
# App state mgmt

class BrowserSingleton:
    # Class-level variables to store the singleton instance, browser context, and processing state
    _instance = None
    _context = None
    _processing = []

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
        """
        Starts Playwright and launches a persistent Firefox context using a custom profile.
        This allows the browser to maintain cookies, sessions, and settings across runs.
        """
        playwright = sync_playwright().start()

        # Launch Firefox with persistent context (needed for keeping session info between runs)
        cls._context = playwright.firefox.launch_persistent_context(
            env('FFPROFILEPATH'),  # Path to a pre-created Firefox profile
            headless=False,        # Set to True if you don't want to see the UI
            viewport={'width': 1920, 'height': 6000},  # Large viewport to avoid lazy-loaded content issues
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0'
        )
        cls._page = cls._context.new_page()

    def get_browser(cls):
        return cls._instance

    def get_context(self):
        return self._context  # Return the context, not the browser

    def get_page(cls):
        return cls._page

    def logged_in(cls):
        try:
            cls._page.locator('header[role="banner"]').wait_for(timeout=10000)
            print("Navigation bar is present — you're logged in!")
            return True
        except TimeoutError:
            print("Navigation bar not found — probably still on login page.")
            return False

    def close_context(self):
        """Closes the browser context and resets the singleton instance."""
        if self._context:
            self._context.close()
            self._instance = None  # Allow re-instantiating later if needed

##################
# Decorators zone

# Decorator factory: when you need to pass custom parameters, returns the decorator function
def delay(min_sec=4, max_sec=6):
    def decorator(func): # Receives the function we’ll be decorating (func) as an arg
        @wraps(func) # Preserves the original function’s name, docstring, etc
        def wrapper(*args, **kwargs): # Defines the function that'll wrap the decorated func
            sleep_time = random.uniform(min_sec, max_sec)
            time.sleep(sleep_time)
            print(f'Sleeping for {sleep_time:.2f}s...')

            result = func(*args, **kwargs) # Decorated func is executed here
            return result # Returns the result of the decorated func
        return wrapper
    return decorator

# Decorator function: when you don't need to pass custom parameters
def ensure_logged_in(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            if BrowserSingleton().logged_in():
                result = func(*args, **kwargs) # Decorated func is executed here
                return result # Returns the result of the decorated func
            else:
                print('Not logged in! Attempting automatic login...')
                login(BrowserSingleton().get_page())
                if not BrowserSingleton().logged_in():
                    raise NotLoggedInError('Login attempt failed')
        except NotLoggedInError as e:
            print('Error: Unable to login:', e)
    return wrapper


####################
# Regular functions


def login(page):
    page.goto('https://x.com/i/flow/login')

    try: # These waits are just here for mimicing human behavior
        sleep(random.uniform(0.5, 1.2))
        # Wait for the username field
        username_input = page.locator('input[autocomplete="username"]')
        username_input.wait_for()

        sleep(random.uniform(0.5, 1.2))
        username_input.fill(env.str('USERNAME'))
        sleep(random.uniform(0.5, 1.2))
        username_input.press('Enter')

        send_password(page)

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