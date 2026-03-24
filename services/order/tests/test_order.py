from src.generated import order_pb2


def test_order_create(client):
    response = client.CreateOrder(order_pb2.CreateOrderRequest(name="###-0001"))

    assert response.id == 1
    assert response.name == "###-0001"


def test_order(client, add_order):
    order = add_order(name="###-0001", created_by=1, product=1)

    response = client.GetOrder(order_pb2.GetOrderRequest(id=order.id))

    assert response.id == 1
    assert response.name == "###-0001"
    assert response.created_by == 1
    assert response.product == 1


def test_order_create_with_relationships(client):
    response = client.CreateOrder(
        order_pb2.CreateOrderRequest(name="###-0002", created_by=1, product=1)
    )

    assert response.id == 1
    assert response.name == "###-0002"
    assert response.created_by == 1
    assert response.product == 1


def test_orders(client, add_order):
    add_order(name="###-0001", created_by=1, product=1)
    add_order(name="###-0002", created_by=2, product=2)

    response = client.ListOrders(order_pb2.ListOrdersRequest())

    assert len(response.orders) == 2
    assert response.orders[0].name == "###-0001"
    assert response.orders[1].name == "###-0002"
