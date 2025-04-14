"""Watchdxg
Copyright (c) 2025 Mathieu BARBE-GAYET
All Rights Reserved.
Released under the MIT license
"""
from selenium.common import StaleElementReferenceException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver import Keys
from bs4 import BeautifulSoup
from environs import Env
from classes import Post
from time import sleep
import random
import utils
from exceptions import NotLoggedInError

env = Env()
env.read_env()


def is_rock_bottom(driver):
    return driver.execute_script("""
            var scrollable = document.documentElement || document.body;
            return (scrollable.scrollHeight - scrollable.scrollTop) <= scrollable.clientHeight;
        """)


# function to handle dynamic page content loading - using Selenium
def scroll(driver):
    driver.execute_script('window.scrollBy(0, document.body.scrollHeight/10);')
    new_height = driver.execute_script('return document.body.scrollHeight')
    return new_height


def clean_stat(stat):
    return stat.replace('0', '') if stat.startswith('0') else stat


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
            trim_tail_str = clean_stat(replies) + clean_stat(reposts) + clean_stat(likes) + clean_stat(views)

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

        rock_bottom = False
        retries = 0
        max_retries = 3
        error = False
        while not rock_bottom:
            # Get the height_pos position
            height_pos = scroll(driver)
            if retries > 0:
                print(f'Trying again... {retries}/{max_retries}')
                body = driver.find_element(By.TAG_NAME, "body")
                body.send_keys(Keys.PAGE_DOWN)

            # If the new and last height_pos values are the same we might've reached the bottom of the page.
            if height_pos == pos_history[-1]:
                if not is_rock_bottom(driver):
                    retries += 1
                    print('Same height position')
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    print('Trying a blast to half the page...')
                    print(driver.execute_script('return document.body.scrollHeight'))
                    # driver.execute_script("""
                    #     var lazyImages = document.querySelectorAll('img[data-src], video[data-src]');
                    #     lazyImages.forEach(function(img) {
                    #         img.src = img.getAttribute('data-src');
                    #     });
                    # """)
                    # driver.execute_script("""
                    #     // Hide potential blocking elements (e.g., ads, modals, etc.)
                    #     var overlays = document.querySelectorAll('.ad, .modal, .sticky');
                    #     overlays.forEach(function(element) {
                    #         element.style.display = 'none';
                    #     });
                    # """)
                    # driver.execute_script("""
                    #     // Disable auto-refresh or prevent JavaScript-driven reloads
                    #     window.onbeforeunload = null;
                    #     window.location.reload = function(){};
                    #     window.history.pushState({}, "", window.location.href);
                    # """)
                    if retries > max_retries:
                        print('ERROR! Was unable to scroll any further')
                        error = True
                        break
                else:
                    rock_bottom = True
            else:
                # If we have moved, then add the current position into the height position history
                pos_history.append(height_pos)
                break
            sleep(random.uniform(4, 5))

        sleep(random.uniform(4, 5))
        # Exit posts retrieval
        if rock_bottom:
            print('Done. Got ', len(batch), ' posts')
            break
        if error:
            break


def main():

    driver = utils.get_driver()

    # Navigate to the X page or any URL
    driver.get('https://x.com/')
    sleep(random.uniform(3, 5))

    # Get the current URL after the page loads
    current_url = driver.current_url

    # Check if we need to log in
    try:
        if utils.logged_in(current_url):
            print('Ready to rock')
            # Wrap the main logic here
        else:
            utils.login()
            if not utils.logged_in(current_url):
                raise NotLoggedInError('Login attempt failed')
    except NotLoggedInError as e:
        print('Error: Unable to login:', e)


if __name__ == '__main__':
    main()
