from datetime import datetime


class Post:
    def __init__(self,
                 post_id: str,
                 timestamp: datetime,
                 href: str,
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
        self.user_pseudonym = user_pseudonym
        self.user_handle = user_handle
        self.text = text
        self.replies = replies
        self.reposts = reposts
        self.likes = likes
        self.views = views
