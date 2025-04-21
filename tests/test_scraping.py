from src.infra import AsyncBrowserManager, enforce_login
from bs4 import BeautifulSoup
from environs import Env
import asyncio
import pytest

@pytest.mark.asyncio
@enforce_login
async def test_login():
    """Ensure we're logged in before moving on to other tests"""
    page = AsyncBrowserManager.get_page()

    # Wait for the button to be visible
    await page.wait_for_selector('article[data-testid="tweet"]')
    html = await page.content()

    # Parse the HTML with BeautifulSoup and check if 'article' is present
    soup = BeautifulSoup(html, 'html.parser')
    assert soup.find('article') is not None


# @pytest.mark.asyncio
# @enforce_login
# async def test_get_usercell():
#     """Followers page: Are individual follower main wrapper still reachable"""
#     page = AsyncBrowserManager.get_page()
#     env = Env()
#     env.read_env()
#     username = env.str("USERNAME")

#     print(f"[DEBUG] Going to followers page of {username}...")
#     await page.goto(f'https://x.com/{username}/followers')
#     await asyncio.sleep(3)  # let dynamic content load

#     print("[DEBUG] Waiting for UserCell...")
#     user_cell_elem = await page.wait_for_selector('button[data-testid="UserCell"]', timeout=10000)

#     print("[DEBUG] Getting inner HTML...")
#     html = await user_cell_elem.inner_html()

#     print("[DEBUG] Got HTML:\n", html)
#     assert 'UserCell' in html

# @pytest.mark.asyncio
# async def test_get_usercell():
#     """Followers page: Are individual follower main wrapper still reachable"""
#     page = AsyncBrowserManager.get_page()
#     env = Env()
#     env.read_env()
#     username = env.str("USERNAME")
#     await page.goto(f'https://x.com/{username}/followers')
#     user_cell_elem = await page.NOOOO.wait_for_selector('button[data-testid="UserCell"]')
#     html = await user_cell_elem.content()
#     print(html)
#     assert 'UserCell' in html == True


# @pytest.mark.asyncio
# async def test_followers_section():
#     """Followers page: Is the follower list's main wrapper still reachable"""
#     page = AsyncBrowserManager.get_page()

#     # Wait for an element that's one of the last elements to be loaded
#     await page.locator('button[data-testid="UserCell"]').first.wait_for(timeout=10000)

#     html_element = await page.locator('section[role:"region"]')
#     html = await html_element.content()
#     assert 'region' in html # TODO: Refine this test


# @pytest.mark.asyncio
# async def test_get_user_handle():
#     """Followers page: Can we still get user handles"""
#     page = AsyncBrowserManager.get_page()
#     html_element = await page.locator('button[data-testid="UserCell"]').first.wait_for(timeout=10000)

#     html = await html_element.content()
#     soup = BeautifulSoup(html, 'html.parser')
#     soup.find('a', {'role':'link', 'aria-hidden': 'true'})

#     handle = None
#     if html.has_attr('href'):
#         handle = html['href']
#     assert handle and type(handle) == 'str'


#####################
# User page scraping

# @pytest.mark.asyncio
# async def test_get_username():
#     """"""

#     assert ''


# @pytest.mark.asyncio
# async def test_get_user_bio():
#     """"""

#     assert ''


# @pytest.mark.asyncio
# async def test_get_user_join_date():
#     """"""

#     assert ''


# @pytest.mark.asyncio
# async def test_get_following_count():
#     """"""

#     assert ''



# @pytest.mark.asyncio
# async def test_get_followers_count():
#     """"""

#     assert ''


# @pytest.mark.asyncio
# async def test_get_url():
#     """"""

#     assert ''


# @pytest.mark.asyncio
# async def test_get_url_display_text():
#     """"""

#     assert ''