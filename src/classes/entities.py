from main.db import execute_query, get_connection
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


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
                )
            )
        except Exception as e:
            print('[ERROR] Post insertion into database failed', e)
            # raise


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

    def add_article(self, article_html):
        print('Adding article to XUser')
        self.articles.append(article_html)

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
            xuser_id = res[0]

        except Exception as e:
            print('[ERROR] User insertion into database failed', e)
            # raise
        if self.articles:
            for post in self.articles:
                post.user_id = xuser_id
                post.insert()
        else:
            print('No articles!')