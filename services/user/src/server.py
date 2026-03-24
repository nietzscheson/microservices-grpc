import grpc
from concurrent import futures
from src.generated import user_pb2_grpc
from src.servicer import UserServiceServicer
from src.settings import Settings


def serve():
    settings = Settings()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_pb2_grpc.add_UserServiceServicer_to_server(UserServiceServicer(), server)
    server.add_insecure_port(f"0.0.0.0:{settings.grpc_port}")
    print(f"User gRPC server starting on port {settings.grpc_port}")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
