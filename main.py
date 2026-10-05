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
from features.tasks.repository import TaskRepository
from features.tasks.service import TaskService
from features.tasks.view import TaskView


class MainWindow(QDialog):
    def __init__(
        self,
        auth_service: UserAuthService,
        task_service: TaskService,
    ):
        super().__init__()

        self.auth_service = auth_service
        self.task_service = task_service
        self.logged_out = False

        self.setObjectName("mainContent")
        self.setWindowTitle("Re:Mind - Task Manager")
        self.resize(900, 650)

        self.build_ui()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)

        layout.addWidget(self._build_header())

        current_user = self.auth_service.current_user

        if current_user is None or current_user.id is None:
            raise RuntimeError(
                "MainWindow cannot be opened without an authenticated user."
            )

        self.task_view = TaskView(
            service=self.task_service,
            user_id=current_user.id,
        )

        layout.addWidget(self.task_view, 1)

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("appHeader")
        header.setMinimumHeight(78)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(22, 14, 18, 14)
        header_layout.setSpacing(16)

        title_group = QVBoxLayout()
        title_group.setSpacing(2)

        current_user = self.auth_service.current_user

        username = (
            current_user.username
            if current_user is not None
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

        return header

    def logout(self):
        confirm = QMessageBox.question(
            self,
            "Log Out",
            "Are you sure you want to log out?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        self.auth_service.logout()
        self.logged_out = True
        self.accept()


def load_stylesheet(app: QApplication) -> None:
    qss_path = Path(__file__).parent / "assets" / "style.qss"

    if not qss_path.exists():
        return

    try:
        stylesheet = qss_path.read_text(encoding="utf-8")
    except OSError as error:
        print(f"Unable to load stylesheet: {error}")
        return

    app.setStyleSheet(stylesheet)


def main() -> int:
    app = QApplication(sys.argv)

    database = Database()
    database.create_tables()

    load_stylesheet(app)

    auth_service = UserAuthService(database)

    task_repository = TaskRepository(database)
    task_service = TaskService(task_repository)

    while True:
        login_dialog = UserAuthView(auth_service)

        if login_dialog.exec() != QDialog.DialogCode.Accepted:
            database.close()
            return 0

        if auth_service.current_user is None:
            QMessageBox.critical(
                None,
                "Authentication Error",
                "No authenticated user was found.",
            )
            continue

        window = MainWindow(
            auth_service=auth_service,
            task_service=task_service,
        )
        window.exec()

        if not window.logged_out:
            database.close()
            return 0


if __name__ == "__main__":
    raise SystemExit(main())