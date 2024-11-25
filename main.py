"""Watchdxg
Copyright (c) 2024 Mathieu BARBE-GAYET
All Rights Reserved.
Released under the MIT license
"""
from environs import Env
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import StaleElementReferenceException
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
import regex

env = Env()
env.read_env()


def get_content(driver, url):
    driver.get(url)
    # scroll_to_bottom(driver)
    sleep(5)
    return driver.page_source


# function to handle dynamic page content loading - using Selenium
# def scroll_to_bottom(driver):
#     # define initial page height for 'while' loop
#     last_height = driver.execute_script("return document.body.scrollHeight")
#     while True:
#         driver.execute_script("window.scrollBy(0, document.body.scrollHeight/3);")
#         """if "skuId" in url:
#             expand_info(driver, "css-1n34gja eanm77i0")
#             expand_info(driver, "css-1o99c9n eanm77i0")"""
#         new_height = driver.execute_script("return document.body.scrollHeight")
#         print("New height: ", new_height)
#         if new_height == last_height:
#             break
#         else:
#             last_height = new_height
#             sleep(5)


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


def get_posts(driver, url):
    # This function will parse the dom and store each info in a map
    # It then will return this map to the main function
    main_page_dom = get_content(driver, url)

    print(url)
    soup = BeautifulSoup(main_page_dom, 'html.parser')
    script = (soup.find('script', charset=True))
    charset = script['charset']

    # Get feed
    feed = soup.find('div', class_='css-175oi2r', attrs={"aria-label": True})
    print(feed['aria-label'])
    # feed = soup.find('div', class_='css-175oi2r', attrs={"aria-label": True})

    # # Sets a list of pictures
    # pictures_found = soup.find_all('img', class_='css-1rovmyu e65zztl0')
    # pictures = []
    # for picture_link in pictures_found:
    #     prefix = "https://www.sephora.com"
    #     if prefix not in picture_link:
    #         picture_link = f"{prefix}{picture_link['src']}"
    #     # print("Picture: ", picture['src'] + "\n")
    #     pictures.append(picture_link)

    # Writes the info found for the product in a CSV file
    # write_to_csv(url, name, "Maquillage", price, pros, description, ingredients, how_to_use, pictures)


# def drv_click_btn_by_label(btns, label):
#     click = False
#     for btn in btns:
#         if label in btn.text:
#             btn.click()
#             click = True
#             break
#     return click

# def get_btn(btns, label):
#     b = False
#     for btn in btns:
#         if label in btn.text:
#             btn.click()
#             b = btn
#             break
#     return b


def login(driver):
    get_content(driver, "https://x.com/i/flow/login")
    wait = WebDriverWait(driver, 10)
    try:
        # Get the username field
        sleep(random.uniform(1, 3))
        username = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]')))
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

        # Input the username
        sleep(random.uniform(1, 3))
        username.send_keys(env.str('USERNAME'))
        username.send_keys(Keys.ENTER)

        # Get the password field and
        sleep(random.uniform(1, 3))
        password_field = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[name="password"]')))
        sleep(random.uniform(1, 3))
        password_field.send_keys(env.str('PASSWORD'))
        sleep(random.uniform(1, 3))
        password_field.send_keys(Keys.ENTER)

        return True

    except StaleElementReferenceException as sere:
        print(sere)
        return False


def main():
    adv_search_urls = [
        "https://x.com/search?q=\"list\" (from:upbitglobal)"
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
    # posts = get_posts(driver, url)
    # print(product.encode('utf-8'))
    # if not in_history(href, True):
    #     get_product_details(driver, href)
    # else:
    #     print("Skip: ", href)
    # driver.close()


if __name__ == '__main__':
    main()
