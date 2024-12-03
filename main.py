"""Watchdxg
Copyright (c) 2024 Mathieu BARBE-GAYET
All Rights Reserved.
Released under the MIT license
"""
from classes import Post
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
def scroll(driver):
    driver.execute_script("window.scrollBy(0, document.body.scrollHeight/6);")
    new_height = driver.execute_script("return document.body.scrollHeight")
    return new_height


def get_stats(stats_grp, stat_pos):
    subset = stats_grp[stat_pos].select('span span')
    return str(0) if not bool(subset[0].select('span')) else subset[0].select('span')[0].text


def get_posts(driver, url):
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
                for z in reply_container:
                    print(z.text)
                repl = True if bool(reply_container[4].text.startswith('@')) else False

                if repl:
                    in_reply_to.append(reply_container[4].text)
                    if len(reply_container) > 5:
                        if reply_container[5].text.startswith('@') and len(in_reply_to) > 0:
                            in_reply_to.append(reply_container[5].text)

            # TODO: Case 2: handle posts that are directly displayed under the original post

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
            trim_tail_str = (replies + reposts + likes + views).replace('O', '')

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
        # Get the height_pos position and add it to the list of height_pos.
        height_pos = scroll(driver)
        # If the new and last height_pos values are the same, then we've reached the bottom of the page.
        if height_pos == pos_history[-1]:
            break
        else:
            pos_history.append(height_pos)
        sleep(random.uniform(4, 5))
    print('Done. Got ', len(batch), ' posts')


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


def main():
    adv_search_urls = [
        # "https://x.com/search?q=\"list\" (from:upbitglobal)&f=live"
        'https://x.com/search?q=%5C%22list%5C%22%20(from%3Abinance)&src=typed_query&f=live'
        # 'https://x.com/search?f=live&q=(from%3Abinance)%20filter%3Areplies'
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
