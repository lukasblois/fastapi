from passlib.context import CryptContext
from zxcvbn import zxcvbn

pwd_context = CryptContext(
    schemes=['bcrypt'], deprecated='auto', truncate_error=False)


def hash(password: str):
    return pwd_context.hash(password)


def verify(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def sanitize_credentials(username, password):
    return username.strip().lower(), password.strip()


def validate_password_strength(password: str, email: str = None):
    result = zxcvbn(password, user_inputs=[email] if email else [])

    score = result['score']
    feedback = result['feedback']
    crack_time = result['crack_times_display']['offline_slow_hashing_1e4_per_second']

    if score < 3:
        suggestions = feedback.get('suggestions', [])
        warning = feedback.get('warning', '')

        error_msg = "Password is too weak. "
        if warning:
            error_msg += f"{warning} "
        if suggestions:
            error_msg += " ".join(suggestions)

        return False, error_msg, score, crack_time

    return True, "Password strength is acceptable", score, crack_time


def get_limit_count(limit_str: str) -> int:
    return int(limit_str.split('/')[0])
