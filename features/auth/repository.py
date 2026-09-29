import sqlite3

from database.database import Database
from .models import User


class UserAuthRepository:
    def __init__(self, database: Database):
        self.database = database

    def add(self, user: User, password_hash: str) -> User:
        try:
            with self.database.connect() as connection:
                cursor = connection.execute(
                    "INSERT INTO users (username, password) VALUES (?, ?)",
                    (user.username, password_hash),
                )
                user.id = cursor.lastrowid
        except sqlite3.IntegrityError as error:
            raise ValueError("Username is already taken.") from error
        return user

    def find_by_username(self, username: str) -> tuple[User, str] | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT id, username, password FROM users WHERE username = ?",
                (username,),
            ).fetchone()
        if row is None:
            return None
        user = User(id=row[0], username=row[1], password_hash=row[2])
        return user, row[2]
