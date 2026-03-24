import subprocess
import pytest
import grpc
from concurrent import futures
from sqlalchemy import text
from src.database import Base
from src.models import User
from src.containers import MainContainer
from src.generated import user_pb2_grpc
from src.servicer import UserServiceServicer


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
    user_pb2_grpc.add_UserServiceServicer_to_server(UserServiceServicer(), server)
    port = server.add_insecure_port("[::]:0")
    server.start()
    yield f"localhost:{port}"
    server.stop(grace=0)


@pytest.fixture()
def client(grpc_server):
    channel = grpc.insecure_channel(grpc_server)
    return user_pb2_grpc.UserServiceStub(channel)


@pytest.fixture()
def add_user(db):
    def _(**kwargs):
        user = User(**kwargs)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    return _
