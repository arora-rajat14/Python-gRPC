import grpc
import logging
import sys  # To get command line arguments

# Needs access to generated code.
# Easiest way for a simple test script is to add service dirs to path
# In a real client app, you'd install generated code as a package.
sys.path.append("./auth_service")  # Adjust if your structure differs
sys.path.append("./profile_service")  # Adjust if your structure differs

from generated import auth_pb2
from generated import auth_pb2_grpc

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

AUTH_SERVICE_ADDR = "localhost:50051"
PROFILE_SERVICE_ADDR = "localhost:50052"

# --- Credentials to test with ---
TEST_USERNAME = "testuser"
TEST_PASSWORD = "password123"


def run_register(stub):
    """Calls the Register RPC."""
    logging.info(f"--- Calling Register for user: {TEST_USERNAME} ---")
    try:
        request = auth_pb2.RegisterRequest(
            username=TEST_USERNAME, password=TEST_PASSWORD
        )
        response = stub.Register(request, timeout=10)
        if response.success:
            logging.info(f"Register successful: {response.message}")
        else:
            logging.warning(f"Register failed: {response.message}")
        return response.success
    except grpc.RpcError as e:
        logging.error(f"Register RPC failed: {e.code()} - {e.details()}")
        return False


def run_login(stub):
    """Calls the Login RPC and returns the token."""
    logging.info(f"--- Calling Login for user: {TEST_USERNAME} ---")
    try:
        request = auth_pb2.LoginRequest(username=TEST_USERNAME, password=TEST_PASSWORD)
        response = stub.Login(request, timeout=10)
        if response.success and response.token:
            logging.info(
                f"Login successful. Token received: {response.token[:15]}..."
            )  # Log truncated token
            return response.token
        else:
            logging.warning(f"Login failed: {response.message}")
            return None
    except grpc.RpcError as e:
        logging.error(f"Login RPC failed: {e.code()} - {e.details()}")
        return None


def run_get_profile(stub, token):
    """Calls the GetProfile RPC with authentication token."""
    logging.info("--- Calling GetProfile ---")
    if not token:
        logging.error("Cannot call GetProfile without a token.")
        return

    try:
        # --- Create Metadata ---
        # Pass the token in the 'authorization' metadata key
        metadata = [("authorization", f"Bearer {token}")]

        request = (
            auth_pb2.GetProfileRequest()
        )  # Request is empty as user identified by token
        response = stub.GetProfile(request, metadata=metadata, timeout=10)

        if response.success:
            logging.info("GetProfile successful!")
            logging.info(f"  User ID: {response.user_id}")
            logging.info(f"  Email: {response.email}")
            logging.info(f"  Full Name: {response.full_name}")
        else:
            logging.warning(f"GetProfile failed: {response.message}")

    except grpc.RpcError as e:
        logging.error(f"GetProfile RPC failed: {e.code()} - {e.details()}")
        if e.code() == grpc.StatusCode.UNAUTHENTICATED:
            logging.error(
                "  Reason: Likely invalid or expired token, or token not provided correctly."
            )


def main():
    jwt_token = None

    # --- Connect to AuthService ---
    try:
        with grpc.insecure_channel(AUTH_SERVICE_ADDR) as channel:
            logging.info(f"Connecting to AuthService at {AUTH_SERVICE_ADDR}")
            auth_stub = auth_pb2_grpc.AuthServiceStub(channel)

            # 1. Register User (Optional - might fail if already exists, that's okay for test)
            run_register(auth_stub)

            # 2. Login User
            jwt_token = run_login(auth_stub)

    except Exception as e:
        logging.error(f"Failed to connect or interact with AuthService: {e}")
        return  # Cannot proceed without login

    # --- Connect to ProfileService ---
    if jwt_token:
        try:
            with grpc.insecure_channel(PROFILE_SERVICE_ADDR) as channel:
                logging.info(
                    f"\nConnecting to ProfileService at {PROFILE_SERVICE_ADDR}"
                )
                profile_stub = auth_pb2_grpc.ProfileServiceStub(channel)

                # 3. Call GetProfile with the token
                run_get_profile(profile_stub, jwt_token)

                # 4. Call GetProfile without token (expect failure)
                logging.info(
                    "\n--- Calling GetProfile WITHOUT token (expect UNAUTHENTICATED) ---"
                )
                run_get_profile(profile_stub, None)

                # 5. Call GetProfile with invalid token (expect failure)
                logging.info(
                    "\n--- Calling GetProfile WITH INVALID token (expect UNAUTHENTICATED) ---"
                )
                run_get_profile(profile_stub, "this.is.an.invalid.token")

        except Exception as e:
            logging.error(f"Failed to connect or interact with ProfileService: {e}")

    else:
        logging.error("Login failed, cannot test ProfileService.")


if __name__ == "__main__":
    main()
