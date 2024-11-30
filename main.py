"""Watchdxg
Copyright (c) 2024 Mathieu BARBE-GAYET
All Rights Reserved.
Released under the MIT license
"""
from environs import Env
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import StaleElementReferenceException, TimeoutException
from selenium.webdriver import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.firefox.options import Options
from time import sleep
import os
import random

import csv
import re

env = Env()
env.read_env()


class Post:
    def __init__(self, post_id: str, user_pseudonym: str, user_handle: str, text: str):
        self.post_id = post_id
        self.user_pseudonym = user_pseudonym
        self.user_handle = user_handle
        self.text = text


# def get_product_links(a_tags):
#     links = []
#     for a_tag in a_tags:
#         link = a_tag['href']
#         prefix = "https://www.sephora.com"
#         if prefix not in link:
#             link = f"{prefix}{link}"
#         links.append(link)
#     return links


# def in_history(url, check_mode=False):
#     # Checks if the link has already been processed, if so return True
#     with open('./history.log', 'a+', newline='') as file:
#         # If the URL is in the history file, quit the function
#         if url in file:
#             file.close()
#             return True
#         # If it's not in the history file and if this function has been called without check mode, add it in the history
#         if not check_mode:
#             file.write(f"{url}\n")
#             file.close()
#             return True
#     # Else if the function is called with check_mode True it will return false.
#     # The goal is to use this function to check if an URL has been already processed without adding it in the meantime
#     return False


# def write_to_csv(url, name, category, price, pros, desc, ingredients, how_to_use, pictures):
#     with open('./products.csv', 'a+', newline='') as csv_file:
#         if name in csv_file:
#             csv_file.close()
#             return
#         products_csv = csv.writer(csv_file, delimiter=';', quotechar='|', quoting=csv.QUOTE_MINIMAL)
#         products_csv.writerow([name, category, price, pros, desc, ingredients, how_to_use, pictures])
#         csv_file.close()
#         # Adds the URL corresponding to the processed product in the history
#         in_history(url)


# function to handle dynamic page content loading - using Selenium
def scroll(driver, last_height):
    driver.execute_script("window.scrollBy(0, document.body.scrollHeight/6);")
    new_height = driver.execute_script("return document.body.scrollHeight")
    return new_height


def get_posts(driver, url):
    # This function will parse the dom and store each info in a map
    # It then will return this map to the main function
    driver.get(url)
    sleep(3)

    # Get feed
    # feed = soup.find('div', class_='css-175oi2r', attrs={"aria-label": True})
    sleep(random.uniform(1, 3))
    batch = []
    pos_history = [0]
    height_pos = 0
    while True:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        for a in soup.findAll('article', {'data-testid': 'tweet'}):
            print('')
            # posted_by_at_grp is a bunch of nested elements that stores the username, handle and datetime
            posted_by_at_grp = a.select('div', {'data-testid': 'User-Name'})[0]
            display_name = posted_by_at_grp.select('a > div > div > span > span')[0].text
            user_handle = posted_by_at_grp.select('div > div > div > a > div > span')[0].text
            timestamp = posted_by_at_grp.select('time')[0]['datetime']

            # stats_grp = a.select('span[data-testid="app-text-transition-container"]')
            # replies = stats_grp[0].select('span span span')[0].text
            # reposts = stats_grp[1].select('span span span')[0].text
            # likes = stats_grp[2].select('span span span')[0].text
            # views = stats_grp[3].select('span span span ')[0].text
            # print('Replies',replies,'Reposts', reposts, 'Likes',likes, 'Views',views)

            # For some reason, tweet_text includes an unwanted string like below therefore we remove it
            trim_head_str = f'{display_name}{user_handle}·{posted_by_at_grp.select('time')[0].text}'
            tweet_text = a.select('div', {'data-testid': 'tweetText'})[0].text.replace(trim_head_str, '')

            post = Post(timestamp, display_name, user_handle, tweet_text)

            if not any(saved_post.post_id == timestamp for saved_post in batch):
                batch.append(post)
                print(f'DisplayName: {display_name}')
                print(f'Handle: {user_handle}')
                print(f'TimeStamp: {timestamp}')
                print(f'tweet_text: {tweet_text}')
    
        # Get the height_pos position and add it to the list of height_pos.
        height_pos = scroll(driver, height_pos)
        # If the new and last height_pos values are the same, then we've reached the bottom of the page.
        print(pos_history[-1], height_pos)
        if height_pos == pos_history[-1]:
            break
        else:
            pos_history.append(height_pos)
        sleep(random.uniform(2, 4))
    print('Done. Got ', len(batch), ' posts')

    # Writes the info found for the product in a CSV file
    # write_to_csv()


def send_password(wait):
    sleep(random.uniform(1, 3))
    password_field = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[name="password"]')))
    sleep(random.uniform(1, 3))
    password_field.send_keys(env.str('PASSWORD'))
    sleep(random.uniform(1, 3))
    password_field.send_keys(Keys.ENTER)


def login(driver):
    driver.get("https://x.com/i/flow/login")
    wait = WebDriverWait(driver, 10)
    try:
        # TODO: Fix an issue where the username filed can't be selected or the username can't be sent
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


def main():
    adv_search_urls = [
        "https://x.com/search?q=\"list\" (from:upbitglobal)&f=live"
        # 'https://x.com/search?q=%5C%22list%5C%22%20(from%3Abinance)&src=typed_query&f=live'
    ]

    options = Options()
    options.headless = False
    options.set_preference("general.useragent.override",
                           "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0")
    options.set_preference("dom.webdriver.enabled", False)  # Disable the webdriver flag
    options.set_preference("useAutomationExtension", False)  # Disable automation extension

    service = Service(f'{os.getcwd()}/Geckodriver')

    driver = webdriver.Firefox(service=service, options=options)
    driver.install_addon(f'{os.getcwd()}/ext.xpi', temporary=True)

    WebDriverWait(driver, 10).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

    for url in adv_search_urls:
        if login(driver):
            print('Successfully logged in!')
            get_posts(driver, url)
    # posts = get_posts(driver, url)
    # print(product.encode('utf-8'))
    # if not in_history(href, True):
    #     get_product_details(driver, href)
    # else:
    #     print("Skip: ", href)
    # driver.close()


if __name__ == '__main__':
    main()
