import grpc
from src.generated import user_pb2, user_pb2_grpc
from src.models import User
from src.containers import MainContainer

container = MainContainer()
Session = container.session()


class UserServiceServicer(user_pb2_grpc.UserServiceServicer):

    def GetUser(self, request, context):
        with Session() as session:
            user = session.get(User, request.id)
            if not user:
                context.abort(grpc.StatusCode.NOT_FOUND, f"User {request.id} not found")
            return user_pb2.UserResponse(id=user.id, name=user.name)

    def ListUsers(self, request, context):
        with Session() as session:
            users = session.query(User).all()
            return user_pb2.ListUsersResponse(
                users=[user_pb2.UserResponse(id=u.id, name=u.name) for u in users]
            )

    def CreateUser(self, request, context):
        with Session() as session:
            user = User(name=request.name)
            session.add(user)
            session.commit()
            return user_pb2.UserResponse(id=user.id, name=user.name)

    def GetUsersBatch(self, request, context):
        with Session() as session:
            users = session.query(User).filter(User.id.in_(request.ids)).all()
            return user_pb2.ListUsersResponse(
                users=[user_pb2.UserResponse(id=u.id, name=u.name) for u in users]
            )
