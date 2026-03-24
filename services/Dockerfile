FROM python:3.13 AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONFAULTHANDLER=1
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=.

# Proto compilation stage
FROM base AS proto-builder
RUN pip install grpcio-tools
COPY proto/ /proto/
RUN mkdir -p /generated/user /generated/product /generated/order && \
    for service in user product order; do \
      python -m grpc_tools.protoc -I/proto/$service \
        --python_out=/generated/$service --grpc_python_out=/generated/$service \
        /proto/$service/$service.proto && \
      sed -i "s/^import \(.*\)_pb2 as/from . import \1_pb2 as/" /generated/$service/${service}_pb2_grpc.py && \
      touch /generated/$service/__init__.py; \
    done

FROM base AS user

WORKDIR /services/user

COPY services/user/pyproject.toml ./

RUN uv sync --no-install-project

COPY --from=proto-builder /generated/user/ ./src/generated/

CMD ["uv", "run", "python", "-m", "src.server"]

FROM base AS product

WORKDIR /services/product

COPY services/product/pyproject.toml ./

RUN uv sync --no-install-project

COPY --from=proto-builder /generated/product/ ./src/generated/

CMD ["uv", "run", "python", "-m", "src.server"]

FROM base AS order

WORKDIR /services/order

COPY services/order/pyproject.toml ./

RUN uv sync --no-install-project

COPY --from=proto-builder /generated/order/ ./src/generated/

CMD ["uv", "run", "python", "-m", "src.server"]
