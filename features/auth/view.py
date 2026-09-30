from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


class UserAuthView(QDialog):
    def __init__(self, service):
        super().__init__()
        self.setObjectName("userauthView")
        self.service = service
        self.setWindowTitle("Re:Mind Login Page")
        self.setMinimumWidth(380)
        self.build_ui()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        heading = QLabel("Re: Mind")
        heading.setObjectName("heading")
        heading.setWordWrap(True)
        layout.addWidget(heading)

        self.pages = QStackedWidget()
        self.pages.addWidget(self._build_login_page())
        self.pages.addWidget(self._build_registration_page())
        layout.addWidget(self.pages)

    def _build_login_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Sign in to start managing your Tasks."))

        form = QFormLayout()
        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("Enter your username")
        self.login_password = QLineEdit()
        self.login_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_password.setPlaceholderText("Enter your password")
        form.addRow("Username", self.login_username)
        form.addRow("Password", self.login_password)
        layout.addLayout(form)

        login_button = QPushButton("Log In")
        login_button.setObjectName("primaryButton")
        login_button.clicked.connect(self.login)
        layout.addWidget(login_button)

        register_button = QPushButton("Create an Account")
        register_button.setObjectName("secondaryButton")
        register_button.clicked.connect(lambda: self.pages.setCurrentIndex(1))
        layout.addWidget(register_button)
        return page

    def _build_registration_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Create an account to use the application."))

        form = QFormLayout()
        self.register_username = QLineEdit()
        self.register_username.setPlaceholderText("At least 4 characters")
        self.register_password = QLineEdit()
        self.register_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.register_password.setPlaceholderText("At least 8 characters")
        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password.setPlaceholderText("Enter the password again")
        form.addRow("Username", self.register_username)
        form.addRow("Password", self.register_password)
        form.addRow("Confirm Password", self.confirm_password)
        layout.addLayout(form)

        register_button = QPushButton("Register")
        register_button.setObjectName("primaryButton")
        register_button.clicked.connect(self.register)
        layout.addWidget(register_button)

        back_button = QPushButton("Back to Login")
        back_button.setObjectName("secondaryButton")
        back_button.clicked.connect(lambda: self.pages.setCurrentIndex(0))
        layout.addWidget(back_button)
        return page

    def register(self):
        try:
            self.service.register_user(
                self.register_username.text(),
                self.register_password.text(),
                self.confirm_password.text(),
            )
        except ValueError as error:
            QMessageBox.warning(self, "User Account Registration Failed", str(error))
            return
        QMessageBox.information(
            self,
            "Account Created",
            "Account registered successfully. Please Log in to continue.",
        )
        self.login_username.setText(self.register_username.text().strip())
        self.login_password.clear()
        self.register_password.clear()
        self.confirm_password.clear()
        self.pages.setCurrentIndex(0)

    def login(self):
        try:
            self.service.authenticate_user(
                self.login_username.text(), self.login_password.text()
            )
        except ValueError as error:
            QMessageBox.warning(self, "Login Failed", str(error))
            return
        self.accept()
