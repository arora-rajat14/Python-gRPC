import grpc
import os
import logging
from generated import auth_pb2
from generated import auth_pb2_grpc

AUTH_SERVICE_URL = os.getenv(
    "AUTH_SERVICE_URL", "localhost:50051"
)  # Default for local dev


def verify_token(token: str) -> auth_pb2.VerifyTokenResponse | None:
    """Calls the AuthService to verify a token."""
    logging.debug(f"Connecting to AuthService at {AUTH_SERVICE_URL} to verify token")
    try:
        # Use insecure channel for simplicity IN DEV ONLY!
        with grpc.insecure_channel(AUTH_SERVICE_URL) as channel:
            # Test connectivity - optional but good practice for debugging
            try:
                grpc.channel_ready_future(channel).result(timeout=5)  # Wait 5 seconds
                logging.debug("Channel connection to AuthService successful.")
            except grpc.FutureTimeoutError:
                logging.error(
                    f"Timeout connecting to AuthService at {AUTH_SERVICE_URL}"
                )
                return None

            stub = auth_pb2_grpc.AuthServiceStub(channel)
            request = auth_pb2.VerifyTokenRequest(token=token)
            logging.debug("Sending VerifyToken request to AuthService")
            response = stub.VerifyToken(request, timeout=10)  # Add a timeout
            logging.debug(
                f"Received VerifyToken response: isValid={response.is_valid}, userId={response.user_id}"
            )
            return response
    except grpc.RpcError as e:
        logging.error(f"gRPC error calling VerifyToken: {e.status()} - {e.details()}")
        return None  # Indicate failure
    except Exception as e:
        logging.error(f"Unexpected error calling VerifyToken: {e}")
        return None
