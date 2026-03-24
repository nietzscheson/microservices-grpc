from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    user_service_url: str = "user:50051"
    product_service_url: str = "product:50051"
    order_service_url: str = "order:50051"
