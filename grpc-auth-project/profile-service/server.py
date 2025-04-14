import grpc
from concurrent import futures
import time
import logging
import os

# Import generated code (needs auth_pb2 and auth_pb2_grpc for ProfileService itself)
from generated import auth_pb2
from generated import auth_pb2_grpc

# Import the helper client for calling AuthService
import auth_client

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


# --- Helper function to extract token ---
def get_token_from_context(context):
    """Extracts JWT token from gRPC metadata."""
    metadata = dict(context.invocation_metadata())
    # Metadata keys are often lowercased by gRPC infrastructure
    auth_header = metadata.get(
        "authorization"
    )  # Common practice: 'authorization: Bearer <token>'
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]
    # Fallback: Check for a simpler 'token' key if needed
    # token = metadata.get('token')
    # if token:
    #    return token
    return None


class ProfileServiceServicer(auth_pb2_grpc.ProfileServiceServicer):
    """Implements the ProfileService gRPC methods."""

    def GetProfile(self, request, context):
        """Handles GetProfile requests, requiring authentication."""
        logging.info("GetProfile request received.")

        token = get_token_from_context(context)
        if not token:
            logging.warning(
                "GetProfile failed: No authorization token found in metadata."
            )
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details("Authentication token is required.")
            return auth_pb2.GetProfileResponse(
                success=False, message="Authentication required."
            )

        logging.debug("Token found, attempting verification via AuthService...")
        # Call AuthService to verify the token
        verification_response = auth_client.verify_token(token)

        # Check the verification result
        if verification_response and verification_response.is_valid:
            user_id = verification_response.user_id
            logging.info(
                f"Token verified successfully for user ID: {user_id}. Access granted."
            )

            # --- Fetch Profile Data (Dummy Implementation) ---
            # In a real application, you would fetch data from a database
            # using the validated user_id.
            profile_data = {
                "user_id": user_id,
                "email": f"user_{user_id}@example.com",
                "full_name": f"User {user_id} Name",
            }
            # --- End Dummy Data ---

            return auth_pb2.GetProfileResponse(
                success=True,
                user_id=profile_data["user_id"],
                email=profile_data["email"],
                full_name=profile_data["full_name"],
                message="Profile retrieved successfully.",
            )
        else:
            # Verification failed (token invalid, expired, or AuthService unavailable)
            logging.warning(
                f"GetProfile failed: Token verification failed. Reason: {verification_response.message if verification_response else 'AuthService unreachable or error'}"
            )
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details("Invalid or expired token.")
            return auth_pb2.GetProfileResponse(
                success=False, message="Authentication failed: Invalid token."
            )


def serve():
    """Starts the ProfileService gRPC server."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    auth_pb2_grpc.add_ProfileServiceServicer_to_server(ProfileServiceServicer(), server)

    port = "50052"
    server_address = f"[::]:{port}"
    server.add_insecure_port(server_address)  # DEV ONLY!

    logging.info(f"ProfileService starting on port {port}...")
    server.start()
    logging.info("ProfileService started successfully.")

    # Keep the server running
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        logging.info("Stopping ProfileService...")
        server.stop(0)
        logging.info("ProfileService stopped.")


if __name__ == "__main__":
    serve()
