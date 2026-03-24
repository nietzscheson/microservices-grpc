# Microservices gRPC

A hands-on example of how to orchestrate multiple microservices using [gRPC](https://grpc.io/) with a REST API Gateway.

Each microservice owns its own data and exposes a gRPC server. A Python/FastAPI gateway composes them into a single REST API, handling cross-service data enrichment — the same role Apollo Gateway played in the [GraphQL Federation version](https://github.com/nietzscheson/microservices-federation) of this project.

## Why an API Gateway?

In a microservices architecture with gRPC, each service communicates via Protocol Buffers over HTTP/2. But gRPC is not browser-friendly, and clients shouldn't need to know which service owns which data. The API Gateway solves this by:

1. **Each service defines its own `.proto` contract** — the User service knows about users, the Product service knows about products, the Order service knows about orders.
2. **Services stay decoupled** — they never call each other directly. Cross-service references are stored as integer IDs (e.g., `created_by = 1`).
3. **The Gateway orchestrates and composes** — it translates REST requests into gRPC calls, fetches data from multiple services, and returns a single enriched JSON response.

For example, when a client requests `GET /orders/1`:

1. The Gateway calls **Order service** via gRPC → gets `{ id: 1, name: "###-001", created_by: 1, product: 1 }`
2. The Gateway calls **User service** via gRPC → resolves `{ id: 1, name: "Admin" }`
3. The Gateway calls **Product service** via gRPC → resolves `{ id: 1, name: "T-Shirt", created_by: 1 }`
4. The Gateway calls **User service** again → resolves the product's creator
5. The Gateway composes and returns the full response:

```json
{
  "id": 1,
  "name": "###-001",
  "created_by": { "id": 1, "name": "Admin" },
  "product": {
    "id": 1,
    "name": "T-Shirt",
    "created_by": { "id": 1, "name": "Admin" }
  }
}
```

For list endpoints, the Gateway uses **batch RPCs** (`GetUsersBatch`, `GetProductsBatch`) to minimize round-trips.

### Services

| Service   | Port  | Protocol | Description                                      |
|-----------|-------|----------|--------------------------------------------------|
| Gateway   | 4000  | REST     | FastAPI — orchestrates gRPC calls, composes data  |
| User      | 50051 | gRPC     | Manages users                                    |
| Product   | 50052 | gRPC     | Manages products, references users via `created_by` |
| Order     | 50053 | gRPC     | Manages orders, references users and products    |

### Proto definitions

Each service has a `.proto` file in the `proto/` directory:

```protobuf
// proto/user/user.proto
service UserService {
  rpc GetUser (GetUserRequest) returns (UserResponse);
  rpc ListUsers (ListUsersRequest) returns (ListUsersResponse);
  rpc CreateUser (CreateUserRequest) returns (UserResponse);
  rpc GetUsersBatch (GetUsersBatchRequest) returns (ListUsersResponse);
}
```

```protobuf
// proto/product/product.proto
service ProductService {
  rpc GetProduct (GetProductRequest) returns (ProductResponse);
  rpc ListProducts (ListProductsRequest) returns (ListProductsResponse);
  rpc CreateProduct (CreateProductRequest) returns (ProductResponse);
  rpc GetProductsBatch (GetProductsBatchRequest) returns (ListProductsResponse);
}
```

```protobuf
// proto/order/order.proto
service OrderService {
  rpc GetOrder (GetOrderRequest) returns (OrderResponse);
  rpc ListOrders (ListOrdersRequest) returns (ListOrdersResponse);
  rpc CreateOrder (CreateOrderRequest) returns (OrderResponse);
}
```

## Tech Stack

- **Gateway**: Python 3.13, FastAPI, Uvicorn
- **Microservices**: Python 3.13, gRPC, Protocol Buffers
- **Database**: PostgreSQL 17.4, SQLAlchemy + Alembic
- **DI Container**: dependency-injector + pydantic-settings
- **Package Manager**: uv
- **Infrastructure**: Docker Compose

## Getting Started

### Prerequisites

- Docker and Docker Compose

### Installation

1. Clone the repository:

```bash
git clone https://github.com/nietzscheson/microservices-grpc
cd microservices-grpc
```

2. Build and start all services:

```bash
make up
```

3. Verify containers are running:

```bash
make ps
```

```
Container postgres   Running (healthy)   0.0.0.0:6543->5432/tcp
Container user       Running (healthy)   0.0.0.0:50051->50051/tcp
Container product    Running (healthy)   0.0.0.0:50052->50051/tcp
Container order      Running (healthy)   0.0.0.0:50053->50051/tcp
Container gateway    Running             0.0.0.0:4000->4000/tcp
```

4. Apply database migrations:

```bash
make upgrade
```

5. (Optional) Load sample data:

```bash
make fixtures
```

### REST API Endpoints

| Method | Endpoint            | Description                              |
|--------|---------------------|------------------------------------------|
| GET    | `/users`            | List all users                           |
| GET    | `/users/{id}`       | Get user by ID                           |
| POST   | `/users`            | Create user (`{ "name": "..." }`)        |
| GET    | `/products`         | List products (enriched with creator)    |
| GET    | `/products/{id}`    | Get product by ID (enriched with creator)|
| POST   | `/products`         | Create product                           |
| GET    | `/orders`           | List orders (enriched with user + product)|
| GET    | `/orders/{id}`      | Get order by ID (enriched with user + product)|
| POST   | `/orders`           | Create order                             |

### Try it

```bash
# List users
curl localhost:4000/users

# Get a product with its creator
curl localhost:4000/products/1

# Get an order with full composition (user + product + product's creator)
curl localhost:4000/orders/1

# Create a new user
curl -X POST localhost:4000/users -H "Content-Type: application/json" -d '{"name": "New User"}'

# Create an order with relationships
curl -X POST localhost:4000/orders -H "Content-Type: application/json" -d '{"name": "###-004", "created_by": 1, "product": 1}'
```

## Development

### Compile proto files

After modifying `.proto` files, regenerate the Python stubs:

```bash
make proto
```

### Run tests

```bash
make test
```

Run tests for a single service:

```bash
make test.user
make test.product
make test.order
```

### Database migrations

Apply migrations:

```bash
make upgrade
```

Generate a new migration after modifying models:

```bash
make migrate
```

### Project structure

```
.
├── proto/                         # Protocol Buffer definitions
│   ├── user/user.proto
│   ├── product/product.proto
│   └── order/order.proto
├── gateway/                       # REST API Gateway (Python/FastAPI)
│   ├── pyproject.toml
│   ├── src/
│   │   ├── app.py                 # REST endpoints with data composition
│   │   ├── settings.py            # gRPC service URLs
│   │   ├── clients.py             # gRPC stub factories
│   │   └── generated/             # Compiled proto stubs (all 3 services)
│   └── Dockerfile
├── services/
│   ├── Dockerfile                 # Multi-stage build for all Python services
│   ├── user/
│   │   ├── pyproject.toml
│   │   ├── alembic.ini
│   │   ├── src/
│   │   │   ├── models.py          # SQLAlchemy models
│   │   │   ├── servicer.py        # gRPC service implementation
│   │   │   ├── server.py          # gRPC server bootstrap
│   │   │   ├── settings.py        # pydantic-settings configuration
│   │   │   ├── containers.py      # dependency-injector container
│   │   │   ├── database.py        # SQLAlchemy Base
│   │   │   └── generated/         # Compiled proto stubs
│   │   ├── migrations/
│   │   └── tests/
│   ├── product/                   # Same structure as user
│   └── order/                     # Same structure as user
├── docker-compose.yaml
└── Makefile
```
