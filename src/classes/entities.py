from main.db import execute_query, get_connection
from datetime import datetime


class XUser:
    def __init__(self,
            account_id: int,
            handle: str, username: str,
            certified: bool,
            bio: str, created_at: datetime,
            following_count: int,
            followers_count: int,
            following_str: str,
            followers_str: str,
            featured_url: str,
            follower: bool
        ):
            self.account_id = account_id
            self.handle = handle
            self.username = username
            self.certified = certified
            self.bio = bio
            self.created_at = created_at
            self.following_count = following_count
            self.followers_count = followers_count
            self.following_str = following_str
            self.followers_str = followers_str
            self.featured_url = featured_url
            self.follower = follower
            self.articles = []

    def add_article(self, article_html):
        self.articles.append(article_html)

    def get_articles(self):
        return self.articles

    def dataset_fill_up():
        pass

    def insert(self):
        insert_query = """
            INSERT INTO users (
                account_id, handle, username, certified, bio, created_at,
                following_count, followers_count, following_str, followers_str,
                featured_url, follower
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            """
        try:
            res = execute_query(
                get_connection(),
                insert_query,
                (
                    self.account_id, self.handle, self.username,
                    self.certified, self.bio, self.created_at,
                    self.following_count, self.followers_count,
                    self.following_str, self.followers_str,
                    self.featured_url, self.follower
                ),
                fetchone = True
            )
            return res[0]
        except Exception as e:
            print('[ERROR] User insertion into database failed', e)
            # raise


class XPost:
    def __init__(self,
            id: int,
            user_id: int,
            timestamp: datetime,
            username: str,
            handle: str,
            text: str,
            reposts: int,
            likes: int,
            replies: int,
            views: int,
            repost: bool,
        ):
        self.id = id,
        self.user_id = user_id
        self.timestamp = timestamp
        self.username = username
        self.handle = handle
        self.text = text
        self.replies = replies
        self.reposts = reposts
        self.likes = likes
        self.views = views
        self.repost = repost

    def insert(self):
        insert_query = """
            INSERT INTO posts (
                id, user_id, timestamp, username, handle, text, reposts, likes, replies, views, repost
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            execute_query(
                get_connection(),
                insert_query,
                (
                    self.id, self.user_id, self.timestamp, self.username,
                    self.handle, self.text, self.replies, self.reposts,
                    self.likes, self.views, self.repost
                )
            )
        except Exception as e:
            print('[ERROR] Post insertion into database failed', e)
            # raise
