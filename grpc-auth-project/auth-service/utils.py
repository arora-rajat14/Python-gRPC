import os
import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import logging

# Configure password hashing
# Use bycrypt, recommended strong
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Get JWT secret from environment variable
# Use a default only for local dev, raise error if not set in production
JWT_SECRET = os.getenv("JWT_SECRET", "default-secret-for-dev")
if JWT_SECRET == "default-secret-for-dev":
    logging.warning(
        "Using default JWT secret. Set JWT_SECRET environment variable in production!"
    )
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Token validity period


def hash_password(password: str):
    """Hashes a plain text password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a stored hash."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logging.error(f"Error verifying password hash: {e}")
        return False


def create_jwt(data: dict, expires_delta: timedelta | None = None) -> str:
    """Creates a JWT Token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.w(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    # Ensure 'sub' (subject) is present, often the username or user ID
    if "sub" not in to_encode:
        logging.warning("JWT created without 'sub' field.")

    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt


def verify_jwt(token: str) -> dict | None:
    """Verifies a JWT token and returns the payload if valid, otherwise None."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        # Check if 'sub' claim exists (optional but good practice)
        # You could add more checks here (e.g., check against a token blacklist)
        return payload
    except jwt.ExpiredSignatureError:
        logging.warning("JWT verification failed: Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logging.error(f"JWT verification failed: Invalid token - {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred during JWT verification: {e}")
        return None
