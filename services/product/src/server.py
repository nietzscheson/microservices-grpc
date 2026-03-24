import grpc
from concurrent import futures
from src.generated import product_pb2_grpc
from src.servicer import ProductServiceServicer
from src.settings import Settings


def serve():
    settings = Settings()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    product_pb2_grpc.add_ProductServiceServicer_to_server(ProductServiceServicer(), server)
    server.add_insecure_port(f"0.0.0.0:{settings.grpc_port}")
    print(f"Product gRPC server starting on port {settings.grpc_port}")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
