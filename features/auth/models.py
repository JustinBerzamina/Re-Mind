from dataclasses import dataclass


@dataclass
class User:
    username: str
    password: str
    id: int | None = None

    def __post_init__(self) -> None:
        self.username = self.username.strip()
        self.password_hash = self.password_hash.strip()

        if len(self.username) < 4:
            raise ValueError("Username is too short (Minimum of 4 characters).")
        if len(self.username) > 16:
            raise ValueError("Username is too long (Maximum of 16 characters).")
        if not self.password:
            raise ValueError("Password cannot be empty.")
