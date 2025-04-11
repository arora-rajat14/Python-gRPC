import grpc
import logging

# Import generated classes
import greeter_pb2
import greeter_pb2_grpc


def run():
    # Define the server address the client will connect to
    server_address = "localhost:50051"
    # Create an insecure channel to the server (no encryption/authentication)
    # Use grpc.secure_channel for production with credentials
    logging.info(f"Attempting to connect to server at {server_address}")
    with grpc.insecure_channel(server_address) as channel:
        try:
            # Test connectivity - optional, but good practice
            grpc.channel_ready_future(channel).result(timeout=5)  # Wait 5 seconds
            logging.info("Channel connection successful.")

            # Create a stub (client) using the channel
            stub = greeter_pb2_grpc.GreeterStub(channel)

            # Create a request message object
            name_to_greet = "Rajat Arora"
            request = greeter_pb2.HelloRequest(name=name_to_greet)
            logging.info(f"Sending request with name: {name_to_greet}")

            # Make the RPC call (looks like a normal function call)
            response = stub.SayHello(request, timeout=10)  # Add a timeout

            # Process the response
            logging.info(f"Greeter client received: {response.message}")

        except grpc.RpcError as e:
            logging.error(f"RPC failed: {e.status()} - {e.details()}")
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
