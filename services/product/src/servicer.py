import grpc
from src.generated import product_pb2, product_pb2_grpc
from src.models import Product
from src.containers import MainContainer

container = MainContainer()
Session = container.session()


class ProductServiceServicer(product_pb2_grpc.ProductServiceServicer):

    def GetProduct(self, request, context):
        with Session() as session:
            product = session.get(Product, request.id)
            if not product:
                context.abort(grpc.StatusCode.NOT_FOUND, f"Product {request.id} not found")
            return product_pb2.ProductResponse(
                id=product.id, name=product.name, created_by=product.created_by
            )

    def ListProducts(self, request, context):
        with Session() as session:
            products = session.query(Product).all()
            return product_pb2.ListProductsResponse(
                products=[
                    product_pb2.ProductResponse(
                        id=p.id, name=p.name, created_by=p.created_by
                    )
                    for p in products
                ]
            )

    def CreateProduct(self, request, context):
        with Session() as session:
            product = Product(
                name=request.name,
                created_by=request.created_by if request.HasField("created_by") else None,
            )
            session.add(product)
            session.commit()
            return product_pb2.ProductResponse(
                id=product.id, name=product.name, created_by=product.created_by
            )

    def GetProductsBatch(self, request, context):
        with Session() as session:
            products = session.query(Product).filter(Product.id.in_(request.ids)).all()
            return product_pb2.ListProductsResponse(
                products=[
                    product_pb2.ProductResponse(
                        id=p.id, name=p.name, created_by=p.created_by
                    )
                    for p in products
                ]
            )
