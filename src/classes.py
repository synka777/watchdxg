from db import execute_query, get_connection
from datetime import datetime

class XUser:
    def __init__(self,
            account_id: int,
            handle: str, username: str,
            bio: str, created_at: datetime,
            following_count: int,
            followers_count: int,
            featured_url: str,
            follower: bool
        ):
            self.account_id = account_id,
            self.handle = handle,
            self.username = username,
            self.bio = bio,
            self.created_at = created_at ,
            self.following_count = following_count,
            self.followers_count = followers_count,
            self.featured_url = featured_url,
            self.follower = follower

    def dataset_fill_up():
        pass

    def insert(self):
        insert_query = """
            INSERT INTO users (
                account_id,
                handle, username,
                bio, created_at,
                following_count,
                followers_count,
                featured_url,
                follower
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
        try:
            execute_query(
                get_connection(),
                insert_query,
                (
                    self.account_id,
                    self.handle, self.username,
                    self.bio, self.created_at,
                    self.following_count,
                    self.followers_count,
                    self.featured_url,
                    self.follower
                )
            )
            return True
        except Exception as e:
            print('[ERROR] Insertion into database failed', e)
            # raise


class Post:
    def __init__(self,
            post_id: str,
            timestamp: datetime,
            href: str,
            is_reposted: bool,
            in_reply_to: list,
            user_pseudonym: str,
            user_handle: str,
            text: str,
            replies: int,
            reposts: int,
            likes: int,
            views: int
        ):
        self.post_id = post_id
        self.timestamp = timestamp
        self.href = href
        self.is_reposted = is_reposted,
        self.in_reply_to = in_reply_to,
        self.user_pseudonym = user_pseudonym
        self.user_handle = user_handle
        self.text = text
        self.replies = replies
        self.reposts = reposts
        self.likes = likes
        self.views = views

