import grpc
from src.generated.user import user_pb2_grpc
from src.generated.product import product_pb2_grpc
from src.generated.order import order_pb2_grpc
from src.settings import Settings

settings = Settings()


def get_user_stub():
    channel = grpc.insecure_channel(settings.user_service_url)
    return user_pb2_grpc.UserServiceStub(channel)


def get_product_stub():
    channel = grpc.insecure_channel(settings.product_service_url)
    return product_pb2_grpc.ProductServiceStub(channel)


def get_order_stub():
    channel = grpc.insecure_channel(settings.order_service_url)
    return order_pb2_grpc.OrderServiceStub(channel)
