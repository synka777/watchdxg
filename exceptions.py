
class NotLoggedInError(Exception):
    """Custom exception when we are not logged in on X"""
    def __init__(self, message='User is not logged in'):
        super().__init__(message)
