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

FROM base AS gateway

WORKDIR /gateway

COPY gateway/pyproject.toml ./

RUN uv sync --no-install-project

COPY --from=proto-builder /generated/user/ ./src/generated/user/
COPY --from=proto-builder /generated/product/ ./src/generated/product/
COPY --from=proto-builder /generated/order/ ./src/generated/order/
RUN touch ./src/generated/__init__.py

CMD ["uv", "run", "uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "4000"]
