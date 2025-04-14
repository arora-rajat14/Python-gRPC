import grpc
from concurrent import futures
import time
import logging
import os
from datetime import timedelta

# Import generated code
from generated import auth_pb2
from generated import auth_pb2_grpc

# Import local modules
import db
import utils

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class AuthServiceServicer(auth_pb2_grpc.AuthServiceServicer):
    """Implements the AuthService gRPC methods."""

    def Register(self, request, context):
        """Handles user registration requests."""
        logging.info(f"Register request received for username: {request.username}")

        # check if user already exists in the db
        existing_user = db.get_user_by_username(request.username)
        if existing_user:
            logging.warning(
                f"Registration failed: Username '{request.username}' already exists."
            )
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details(f"Username '{request.username}' already exists")
            return auth_pb2.RegisterResponse(
                success=False, message="Username already exists"
            )
        # Hash the password
        try:
            hashed_password: str = utils.hash_password(request.password)
        except Exception as e:
            logging.error(f"Password hashing failed for user '{request.username}': {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error during password hashing.")
            return auth_pb2.RegisterResponse(
                success=False, message="Server error during registration"
            )

        # Add user to database
        if db.add_user(request.username, hashed_password):
            logging.info(f"User '{request.username}' registered successfully.")
            return auth_pb2.RegisterResponse(
                success=True, message="User registered successfully"
            )
        else:
            # This could be due to a race condition or other DB error handled in db.py
            logging.error(
                f"Registration failed for user '{request.username}' due to database error."
            )
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Failed to save user to database.")
            return auth_pb2.RegisterResponse(
                success=False, message="Database error during registration"
            )

    def Login(self, request, context):
        """Handles users login requests."""
        logging.info(f"Login request received for username: {request.username}")
        user = db.get_user_by_username(request.username)

        if not user:
            logging.warning(
                f"Login failed for username '{request.username}': User not found."
            )
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("User not found.")
            return auth_pb2.LoginResponse(success=False, message="User not found")

        # verify password
        if not utils.verify_password(request.password, user["hashed_password"]):
            logging.warning(
                f"Login failed: Invalid password for user '{request.username}'."
            )
            context.set_code(
                grpc.StatusCode.UNAUTHENTICATED
            )  # More specific than NOT_FOUND here
            context.set_details("Invalid credentials.")
            return auth_pb2.LoginResponse(
                success=False, message="Invalid username or password"
            )  # Generic message

        # Generate JWT
        try:
            # We store the user ID (or username) in the 'sub' (subject) claim
            access_token_expires = timedelta(minutes=utils.ACCESS_TOKEN_EXPIRE_MINUTES)
            token = utils.create_jwt(
                data={
                    "sub": str(user["id"]),
                    "username": user["username"],
                },  # Include username for potential use
                expires_delta=access_token_expires,
            )
            logging.info(
                f"Login successful for user '{request.username}'. Token issued."
            )
            return auth_pb2.LoginResponse(
                success=True, token=token, message="Login successful"
            )
        except Exception as e:
            logging.error(f"JWT generation failed for user '{request.username}': {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error during token generation.")
            return auth_pb2.LoginResponse(
                success=False, message="Server error during login"
            )

    def VerifyToken(self, request, context):
        """Verifies a JWT token provided by another service or client."""
        logging.info("VerifyToken request received.")
        token_data = utils.verify_jwt(request.token)

        if token_data and "sub" in token_data:
            logging.info(
                f"Token verified successfully for user ID: {token_data['sub']}"
            )
            return auth_pb2.VerifyTokenResponse(
                is_valid=True, user_id=str(token_data["sub"])
            )
        elif token_data:
            logging.warning("Token verification failed: 'sub' claim missing in token.")
            # Decide if this is valid - depends on your requirements
            # Let's treat it as invalid for this example
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details("Token is missing required 'sub' claim.")
            return auth_pb2.VerifyTokenResponse(
                is_valid=False, message="Token invalid (missing sub claim)"
            )
        else:
            # verify_jwt already logged the reason (expired or invalid)
            logging.warning("Token verification failed.")
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details("Invalid or expired token.")
            return auth_pb2.VerifyTokenResponse(
                is_valid=False, message="Token invalid or expired"
            )


def serve():
    """Starts the gRPC server."""
    # Initialize database
    try:
        db.init_db()
    except Exception as e:
        logging.critical(f"Failed to initialize database: {e}. Exiting.")
        return  # Exit if DB init fails

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    auth_pb2_grpc.add_AuthServiceServicer_to_server(AuthServiceServicer(), server)

    port = "50051"
    server_address = f"[::]:{port}"
    server.add_insecure_port(server_address)  # Use insecure for simplicity IN DEV ONLY!

    logging.info(f"AuthService starting on port {port}...")
    server.start()
    logging.info("AuthService started successfully.")

    # Keep the server running
    try:
        while True:
            time.sleep(86400)  # One day
    except KeyboardInterrupt:
        logging.info("Stopping AuthService...")
        server.stop(0)  # Graceful shutdown
        logging.info("AuthService stopped.")


if __name__ == "__main__":
    serve()
