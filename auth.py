import bcrypt
import re
from database import create_user, get_user_by_username, get_user_by_email

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def validate_email(email: str) -> bool:
    return bool(re.match(r"^[\w\.\-]+@[\w\.\-]+\.\w{2,}$", email))

def validate_password(password: str):
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one digit."
    return True, ""

def signup(username, email, password, confirm_password):
    username = username.strip()
    email    = email.strip()
    if not username or len(username) < 3:
        return False, "Username must be at least 3 characters."
    if not validate_email(email):
        return False, "Please enter a valid email address."
    ok, msg = validate_password(password)
    if not ok:
        return False, msg
    if password != confirm_password:
        return False, "Passwords do not match."
    if get_user_by_username(username):
        return False, "Username already taken."
    if get_user_by_email(email):
        return False, "Email already registered."
    if create_user(username, email, hash_password(password)):
        return True, "Account created successfully!"
    return False, "Failed to create account. Please try again."

def login(username, password):
    if not username or not password:
        return False, "Please enter both username and password.", None
    user = get_user_by_username(username.strip())
    if not user or not verify_password(password, user["password_hash"]):
        return False, "Invalid username or password.", None
    return True, "Login successful!", user
