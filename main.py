import sys
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from database.database import Database
from features.auth.service import UserAuthService
from features.auth.view import UserAuthView


class MainWindow(QDialog):
    def __init__(self, auth_service: UserAuthService):
        super().__init__()
        self.auth_service = auth_service
        self.logged_out = False

        self.setObjectName("mainContent")
        self.setWindowTitle("Re:Mind - Task Manager")
        self.resize(820, 560)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)

        # Header section with greeting and logout button
        header = QWidget()
        header.setObjectName("appHeader")
        header.setMinimumHeight(78)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(22, 14, 18, 14)
        header_layout.setSpacing(16)

        title_group = QVBoxLayout()
        title_group.setSpacing(2)

        username = (
            self.auth_service.current_user.username
            if self.auth_service.current_user
            else "User"
        )
        title = QLabel("Re:Mind")
        title.setObjectName("appTitle")
        subtitle = QLabel(f"Logged in as: {username}")
        subtitle.setObjectName("appSubtitle")

        title_group.addWidget(title)
        title_group.addWidget(subtitle)
        header_layout.addLayout(title_group, 1)

        logout_button = QPushButton("Log Out")
        logout_button.setObjectName("logoutButton")
        logout_button.setFixedHeight(36)
        logout_button.clicked.connect(self.logout)
        header_layout.addWidget(logout_button)
        layout.addWidget(header)

        # Placeholder for the TaskView component (we will swap this in next)
        self.placeholder_content = QLabel(
            "Authentication successful! Task dashboard will be mounted here."
        )
        self.placeholder_content.setStyleSheet(
            "font-size: 16px; color: #555555; padding: 40px;"
        )
        layout.addWidget(self.placeholder_content)

    def logout(self):
        confirm = QMessageBox.question(
            self,
            "Log Out",
            "Are you sure you want to log out?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.auth_service.current_user = None
            self.logged_out = True
            self.close()


def main() -> int:
    database = Database()
    database.create_tables()

    app = QApplication(sys.argv)

    # Load stylesheet safely if it exists
    qss_path = Path(__file__).with_name("style.qss")
    if not qss_path.exists():
        qss_path = Path(__file__).parent / "assets" / "style.qss"

    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))

    auth_service = UserAuthService(database)

    # Authentication loop: Logs out back to the login dialog
    while True:
        login_dialog = UserAuthView(auth_service)
        if login_dialog.exec() != QDialog.DialogCode.Accepted:
            return 0  # User closed the login window without authenticating

        window = MainWindow(auth_service)
        window.exec()

        # If the user closed the window without clicking 'Log Out', quit the app
        if not window.logged_out:
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
