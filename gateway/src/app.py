from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import grpc

from src.clients import get_user_stub, get_product_stub, get_order_stub
from src.generated.user import user_pb2
from src.generated.product import product_pb2
from src.generated.order import order_pb2

app = FastAPI(title="API Gateway")


# --- Request models ---

class UserCreate(BaseModel):
    name: str


class ProductCreate(BaseModel):
    name: str
    created_by: Optional[int] = None


class OrderCreate(BaseModel):
    name: str
    created_by: Optional[int] = None
    product: Optional[int] = None


# --- Helpers ---

def user_to_dict(user):
    return {"id": user.id, "name": user.name}


def product_to_dict(product, user=None):
    result = {"id": product.id, "name": product.name}
    if product.HasField("created_by"):
        result["created_by"] = user_to_dict(user) if user else {"id": product.created_by}
    else:
        result["created_by"] = None
    return result


def order_to_dict(order, user=None, product_dict=None):
    result = {"id": order.id, "name": order.name}
    if order.HasField("created_by"):
        result["created_by"] = user_to_dict(user) if user else {"id": order.created_by}
    else:
        result["created_by"] = None
    if order.HasField("product"):
        result["product"] = product_dict if product_dict else {"id": order.product}
    else:
        result["product"] = None
    return result


# --- User endpoints ---

@app.get("/users")
def list_users():
    stub = get_user_stub()
    response = stub.ListUsers(user_pb2.ListUsersRequest())
    return [user_to_dict(u) for u in response.users]


@app.get("/users/{user_id}")
def get_user(user_id: int):
    stub = get_user_stub()
    try:
        response = stub.GetUser(user_pb2.GetUserRequest(id=user_id))
        return user_to_dict(response)
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail=str(e.details()))
        raise


@app.post("/users")
def create_user(body: UserCreate):
    stub = get_user_stub()
    response = stub.CreateUser(user_pb2.CreateUserRequest(name=body.name))
    return user_to_dict(response)


# --- Product endpoints ---

@app.get("/products")
def list_products():
    product_stub = get_product_stub()
    user_stub = get_user_stub()

    response = product_stub.ListProducts(product_pb2.ListProductsRequest())

    # Collect unique creator IDs and batch-fetch users
    creator_ids = list({p.created_by for p in response.products if p.HasField("created_by")})
    users_map = {}
    if creator_ids:
        users_response = user_stub.GetUsersBatch(user_pb2.GetUsersBatchRequest(ids=creator_ids))
        users_map = {u.id: u for u in users_response.users}

    return [
        product_to_dict(p, users_map.get(p.created_by) if p.HasField("created_by") else None)
        for p in response.products
    ]


@app.get("/products/{product_id}")
def get_product(product_id: int):
    product_stub = get_product_stub()
    user_stub = get_user_stub()

    try:
        product = product_stub.GetProduct(product_pb2.GetProductRequest(id=product_id))
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail=str(e.details()))
        raise

    user = None
    if product.HasField("created_by"):
        try:
            user = user_stub.GetUser(user_pb2.GetUserRequest(id=product.created_by))
        except grpc.RpcError:
            pass

    return product_to_dict(product, user)


@app.post("/products")
def create_product(body: ProductCreate):
    stub = get_product_stub()
    req = product_pb2.CreateProductRequest(name=body.name)
    if body.created_by is not None:
        req.created_by = body.created_by
    response = stub.CreateProduct(req)
    return product_to_dict(response)


# --- Order endpoints ---

@app.get("/orders")
def list_orders():
    order_stub = get_order_stub()
    user_stub = get_user_stub()
    product_stub = get_product_stub()

    response = order_stub.ListOrders(order_pb2.ListOrdersRequest())

    # Batch-fetch users
    creator_ids = list({o.created_by for o in response.orders if o.HasField("created_by")})
    users_map = {}
    if creator_ids:
        users_response = user_stub.GetUsersBatch(user_pb2.GetUsersBatchRequest(ids=creator_ids))
        users_map = {u.id: u for u in users_response.users}

    # Batch-fetch products
    product_ids = list({o.product for o in response.orders if o.HasField("product")})
    products_map = {}
    if product_ids:
        products_response = product_stub.GetProductsBatch(
            product_pb2.GetProductsBatchRequest(ids=product_ids)
        )
        products_map = {p.id: p for p in products_response.products}

    # Also enrich products with their creators
    product_creator_ids = list({
        p.created_by for p in products_map.values() if p.HasField("created_by")
    })
    if product_creator_ids:
        extra_users = user_stub.GetUsersBatch(
            user_pb2.GetUsersBatchRequest(ids=product_creator_ids)
        )
        for u in extra_users.users:
            users_map[u.id] = u

    results = []
    for o in response.orders:
        user = users_map.get(o.created_by) if o.HasField("created_by") else None
        product = products_map.get(o.product) if o.HasField("product") else None
        product_dict = None
        if product:
            product_user = users_map.get(product.created_by) if product.HasField("created_by") else None
            product_dict = product_to_dict(product, product_user)
        results.append(order_to_dict(o, user, product_dict))

    return results


@app.get("/orders/{order_id}")
def get_order(order_id: int):
    order_stub = get_order_stub()
    user_stub = get_user_stub()
    product_stub = get_product_stub()

    try:
        order = order_stub.GetOrder(order_pb2.GetOrderRequest(id=order_id))
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail=str(e.details()))
        raise

    # Resolve user
    user = None
    if order.HasField("created_by"):
        try:
            user = user_stub.GetUser(user_pb2.GetUserRequest(id=order.created_by))
        except grpc.RpcError:
            pass

    # Resolve product (and its creator)
    product_dict = None
    if order.HasField("product"):
        try:
            product = product_stub.GetProduct(product_pb2.GetProductRequest(id=order.product))
            product_user = None
            if product.HasField("created_by"):
                try:
                    product_user = user_stub.GetUser(
                        user_pb2.GetUserRequest(id=product.created_by)
                    )
                except grpc.RpcError:
                    pass
            product_dict = product_to_dict(product, product_user)
        except grpc.RpcError:
            pass

    return order_to_dict(order, user, product_dict)


@app.post("/orders")
def create_order(body: OrderCreate):
    stub = get_order_stub()
    req = order_pb2.CreateOrderRequest(name=body.name)
    if body.created_by is not None:
        req.created_by = body.created_by
    if body.product is not None:
        req.product = body.product
    response = stub.CreateOrder(req)
    return order_to_dict(response)
