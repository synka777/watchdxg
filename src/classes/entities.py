from main.db import execute_query, get_connection
from psycopg2.errors import UniqueViolation
from dataclasses import dataclass, field
from typing import Optional, List
from tools.logger import logger
from datetime import datetime


# Used to pass information from Extract to Transform
@dataclass(frozen=True) # Freeze it to make it immutable
class UserExtract:
    handle: str
    html: str


@dataclass
class XPost:
    id: int
    timestamp: datetime
    username: str
    handle: str
    text: str
    reposts: int
    likes: int
    replies: int
    views: int
    repost: bool
    user_id: Optional[int] = None

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
                ),
                do_raise = True
            )

        except UniqueViolation:
            logger.info(f'Post {self.id} already in DB - Stopping post insertions for user ID {self.user_id}')
            raise # re-raises the same exception to the caller

        except Exception as e:
            logger.error('Post insertion into database failed', e)


@dataclass
class XUser:
    account_id: int
    handle: str
    username: str
    certified: bool
    bio: str
    created_at: datetime
    following_count: int
    followers_count: int
    following_str: str
    followers_str: str
    featured_url: str
    follower: bool
    articles: List[XPost] = field(default_factory=list)
    id: Optional[int] = None # Declared as optional to be passed around the class

    def add_article(self, article_html):
        self.articles.append(article_html)

    def upsert(self):
        upsert_query = """
            insert INTO users (
                account_id, handle, username, certified, bio, created_at,
                following_count, followers_count, following_str, followers_str,
                featured_url, follower
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (handle, created_at) DO UPDATE SET
                username = EXCLUDED.username,
                certified = EXCLUDED.certified,
                bio = EXCLUDED.bio,
                following_count = EXCLUDED.following_count,
                followers_count = EXCLUDED.followers_count,
                following_str = EXCLUDED.following_str,
                followers_str = EXCLUDED.followers_str,
                featured_url = EXCLUDED.featured_url,
                follower = EXCLUDED.follower
            RETURNING id;
            """
        try:
            res = execute_query(
                get_connection(),
                upsert_query,
                (
                    self.account_id, self.handle, self.username,
                    self.certified, self.bio, self.created_at,
                    self.following_count, self.followers_count,
                    self.following_str, self.followers_str,
                    self.featured_url, self.follower
                ),
                fetchone = True
            )
            self.id = res[0]

        except Exception as e:
            logger.error('User upsertion into database failed', e)
            return

        if self.articles:
            for post in self.articles:
                try:
                    post.user_id = self.id
                    post.insert()
                except UniqueViolation:
                    break
