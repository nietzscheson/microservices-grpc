from src.generated import product_pb2


def test_product_create(client):
    response = client.CreateProduct(
        product_pb2.CreateProductRequest(name="T-Shirt", created_by=1)
    )

    assert response.id == 1
    assert response.name == "T-Shirt"
    assert response.created_by == 1


def test_product(client, add_product):
    product = add_product(name="Pants", created_by=1)

    response = client.GetProduct(product_pb2.GetProductRequest(id=product.id))

    assert response.id == 1
    assert response.name == "Pants"
    assert response.created_by == 1


def test_products(client, add_product):
    add_product(name="T-Shirt", created_by=1)
    add_product(name="Pants", created_by=1)

    response = client.ListProducts(product_pb2.ListProductsRequest())

    assert len(response.products) == 2
    assert response.products[0].name == "T-Shirt"
    assert response.products[1].name == "Pants"


def test_products_batch(client, add_product):
    add_product(name="T-Shirt", created_by=1)
    add_product(name="Bag", created_by=1)
    add_product(name="Pants", created_by=1)

    response = client.GetProductsBatch(product_pb2.GetProductsBatchRequest(ids=[1, 3]))

    assert len(response.products) == 2
    assert response.products[0].name == "T-Shirt"
    assert response.products[1].name == "Pants"
