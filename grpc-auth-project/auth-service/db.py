import psycopg2
import os
import logging
import time

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://user:password@localhost:5432/authdb"
)  # Default for local dev if not in Docker


def get_db_connection(retries=5, delay=5):
    """Establishes connection to the PostgreSQL database with retries."""
    last_exception = None
    for i in range(retries):
        try:
            conn = psycopg2.connect(DATABASE_URL)
            logging.info("Database connection successful.")
            return conn
        except psycopg2.OperationalError as e:
            last_exception = e
            logging.warning(
                f"Database connection attempt {i+1}/{retries} failed: {e}. Retrying in {delay} seconds..."
            )
            time.sleep(delay)
    logging.error(f"Database connection failed after {retries} retries.")
    raise last_exception  # Raise the last encountered exception


def init_db():
    """Initializes the database by creating the users table if it doesn't exist."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    hashed_password VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """
            )
            conn.commit()
            logging.info("Users table checked/created successfully.")
    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(f"Error initializing database: {error}")
        # Depending on the error, you might want to exit or handle differently
        raise error  # Re-raise to signal failure
    finally:
        if conn is not None:
            conn.close()
            logging.info("Database connection closed.")


def add_user(username: str, hashed_password: str) -> bool:
    """Adds a new user to the database."""
    conn = None
    sql = "INSERT INTO users(username, hashed_password) VALUES(%s, %s)"
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(sql, (username, hashed_password))
            conn.commit()
            logging.info(f"User '{username}' added successfully.")
            return True
    except psycopg2.IntegrityError:
        # This likely means the username already exists (due to UNIQUE constraint)
        logging.warning(f"Attempted to add duplicate username: {username}")
        return False
    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(f"Error adding user '{username}': {error}")
        if conn:
            conn.rollback()  # Roll back the transaction on error
        return False
    finally:
        if conn is not None:
            conn.close()


def get_user_by_username(username: str) -> dict | None:
    """Retrieves a user's data by username."""
    conn = None
    sql = "SELECT id, username, hashed_password FROM users WHERE username = %s;"
    user = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(sql, (username,))
            result = cur.fetchone()  # Fetch one record
            if result:
                user = {
                    "id": result[0],
                    "username": result[1],
                    "hashed_password": result[2],
                }
                logging.debug(f"User '{username}' found.")
            else:
                logging.debug(f"User '{username}' not found.")
        return user
    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(f"Error retrieving user '{username}': {error}")
        return None
    finally:
        if conn is not None:
            conn.close()
