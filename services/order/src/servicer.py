import grpc
from src.generated import order_pb2, order_pb2_grpc
from src.models import Order
from src.containers import MainContainer

container = MainContainer()
Session = container.session()


class OrderServiceServicer(order_pb2_grpc.OrderServiceServicer):

    def GetOrder(self, request, context):
        with Session() as session:
            order = session.get(Order, request.id)
            if not order:
                context.abort(grpc.StatusCode.NOT_FOUND, f"Order {request.id} not found")
            return order_pb2.OrderResponse(
                id=order.id, name=order.name,
                created_by=order.created_by, product=order.product,
            )

    def ListOrders(self, request, context):
        with Session() as session:
            orders = session.query(Order).all()
            return order_pb2.ListOrdersResponse(
                orders=[
                    order_pb2.OrderResponse(
                        id=o.id, name=o.name,
                        created_by=o.created_by, product=o.product,
                    )
                    for o in orders
                ]
            )

    def CreateOrder(self, request, context):
        with Session() as session:
            order = Order(
                name=request.name,
                created_by=request.created_by if request.HasField("created_by") else None,
                product=request.product if request.HasField("product") else None,
            )
            session.add(order)
            session.commit()
            return order_pb2.OrderResponse(
                id=order.id, name=order.name,
                created_by=order.created_by, product=order.product,
            )
