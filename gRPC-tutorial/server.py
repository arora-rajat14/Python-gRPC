from concurrent import futures
import grpc
import logging
import time

# Import generated classes
import greeter_pb2
import greeter_pb2_grpc


# Create a class inheriting from the generated Servicer
# Implement the RPC method defined in the .proto file
class GreeterServicer(greeter_pb2_grpc.GreeterServicer):
    def SayHello(self, request, context):
        logging.info(f"Received SayHello request with name: {request.name}")
        # The actual logic for the RPC call
        response_message = f"Hello, {request.name}!"
        return greeter_pb2.HelloReply(message=response_message)


def serve():
    # Create a gRPC server instance
    # futures.ThreadPoolExecutor creates a pool of threads to handle requests
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Add the implemented Servicer to the server
    greeter_pb2_grpc.add_GreeterServicer_to_server(GreeterServicer(), server)

    # Define the address and port the server will listen on
    server_address = (
        "[::]:50051"  # '[::]' listens on all available IPv6 and IPv4 interfaces
    )
    server.add_insecure_port(server_address)  # Use insecure connection for simplicity

    # Start the server
    logging.info(f"Starting server on {server_address}")
    server.start()

    # Keep the server running indefinitely (or until interrupted)
    try:
        while True:
            time.sleep(86400)  # Sleep for a day
    except KeyboardInterrupt:
        logging.info("Server stopping...")
        server.stop(0)  # Graceful stop
        logging.info("Server stopped.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    serve()
