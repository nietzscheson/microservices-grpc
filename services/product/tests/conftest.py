import subprocess
import pytest
import grpc
from concurrent import futures
from sqlalchemy import text
from src.database import Base
from src.models import Product
from src.containers import MainContainer
from src.generated import product_pb2_grpc
from src.servicer import ProductServiceServicer


@pytest.fixture
def main_container():

    container = MainContainer()

    return container


@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    subprocess.run(["uv", "run", "alembic", "upgrade", "head"])
    yield


@pytest.fixture(autouse=True)
def db(main_container, apply_migrations):
    session_factory = main_container.session()

    with session_factory() as session:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(text(f'TRUNCATE TABLE "{table.name}" RESTART IDENTITY CASCADE'))
        session.commit()

        yield session

        session.rollback()


@pytest.fixture()
def grpc_server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
    product_pb2_grpc.add_ProductServiceServicer_to_server(ProductServiceServicer(), server)
    port = server.add_insecure_port("[::]:0")
    server.start()
    yield f"localhost:{port}"
    server.stop(grace=0)


@pytest.fixture()
def client(grpc_server):
    channel = grpc.insecure_channel(grpc_server)
    return product_pb2_grpc.ProductServiceStub(channel)


@pytest.fixture()
def add_product(db):
    def _(**kwargs):
        product = Product(**kwargs)
        db.add(product)
        db.commit()
        db.refresh(product)
        return product
    return _
