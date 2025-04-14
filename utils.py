
from selenium.common import StaleElementReferenceException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver import Keys
from selenium import webdriver
from environs import Env
from time import sleep
import random
import os

env = Env()
env.read_env()


def get_driver():
    options = Options()
    options.add_argument(f"-profile")
    options.add_argument(env.str('FFPROFILEPATH'))
    options.headless = False
    options.set_preference('general.useragent.override',
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0')
    options.set_preference('dom.webdriver.enabled', False)  # Disable the webdriver flag
    options.set_preference('useAutomationExtension', False)  # Disable automation extension

    service = Service(f'{os.getcwd()}/Geckodriver')

    driver = webdriver.Firefox(service=service, options=options)
    driver.install_addon(f'{os.getcwd()}/ext.xpi', temporary=True)

    WebDriverWait(driver, 10).until(
        lambda d: d.execute_script('return document.readyState') == 'complete'
    )

    return driver


def login(driver):
    driver.get("https://x.com/i/flow/login")
    wait = WebDriverWait(driver, 10)
    try:
        # TODO: Fix an issue where the username field can't be selected or the username can't be sent
        # resulting to Sorry, we could not find your account
        # Get the username field
        sleep(random.uniform(1, 3))
        username = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]')))
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

        # Input the username
        sleep(random.uniform(1, 3))
        username.send_keys(env.str('USERNAME'))
        sleep(random.uniform(1, 3))
        username.send_keys(Keys.ENTER)

        send_password(wait)

    except (StaleElementReferenceException, TimeoutException) as e:
        # TODO: handle Error window on username data-testid="confirmationSheetDialog"
        print('Working around suspicious activity detection...')
        contact_field = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'r-30o5oe')))
        contact_field.send_keys(env.str('CONTACT'))
        sleep(random.uniform(1, 3))
        contact_field.send_keys(Keys.ENTER)

        send_password(wait)

    sleep(random.uniform(1, 3))
    return True


def send_password(wait):
    sleep(random.uniform(1, 3))
    password_field = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[name="password"]')))
    sleep(random.uniform(1, 3))
    password_field.send_keys(env.str('PASSWORD'))
    sleep(random.uniform(1, 3))
    password_field.send_keys(Keys.ENTER)


def logged_in(current_url):
    if 'redirect_after_login' in current_url \
    or 'home' not in current_url:
        print("Session expired or you're logged out. Attempting automatic login...")
        return False
    else:
        print(f'On the correct page: {current_url}')
        return True