from src.generated import user_pb2


def test_user_create(client):
    response = client.CreateUser(user_pb2.CreateUserRequest(name="Isabella"))

    assert response.id == 1
    assert response.name == "Isabella"


def test_user(client, add_user):
    user = add_user(name="Isabella")

    response = client.GetUser(user_pb2.GetUserRequest(id=user.id))

    assert response.id == 1
    assert response.name == "Isabella"


def test_users(client, add_user):
    add_user(name="Isabella")
    add_user(name="Fernando")

    response = client.ListUsers(user_pb2.ListUsersRequest())

    assert len(response.users) == 2
    assert response.users[0].name == "Isabella"
    assert response.users[1].name == "Fernando"


def test_users_batch(client, add_user):
    add_user(name="Isabella")
    add_user(name="Fernando")
    add_user(name="Carlos")

    response = client.GetUsersBatch(user_pb2.GetUsersBatchRequest(ids=[1, 3]))

    assert len(response.users) == 2
    assert response.users[0].name == "Isabella"
    assert response.users[1].name == "Carlos"
