import grpc
from concurrent import futures
from src.generated import order_pb2_grpc
from src.servicer import OrderServiceServicer
from src.settings import Settings


def serve():
    settings = Settings()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    order_pb2_grpc.add_OrderServiceServicer_to_server(OrderServiceServicer(), server)
    server.add_insecure_port(f"0.0.0.0:{settings.grpc_port}")
    print(f"Order gRPC server starting on port {settings.grpc_port}")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
