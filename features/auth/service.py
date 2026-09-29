from database.database import Database

from .models import User
from .repository import UserAuthRepository


class UserAuthService:
    def __init__(self, database: Database):
        self.repository = UserAuthRepository(database)
        self.current_user: User | None = None

    def register_user(self, username: str, password: str, confirmation: str):
        user = User(username=username, password_hash=password)
        # self._validate_password(password, confirmation)
        return self.repository.add(user, password)

    def authenticate_user(self, username: str, password: str) -> User:
        user = User(username=username, password_hash=password)
        record = self.repository.find_by_username(user.username)
        if record is None:
            raise ValueError("Invalid username or password.")
        saved_user, saved_password = record
        if password != saved_password:
            raise ValueError("Invalid username or password.")
        self.current_user = saved_user
        return saved_user
