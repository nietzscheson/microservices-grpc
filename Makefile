.PHONY:
init: down volume up
down:
	docker compose down
volume:
	docker volume prune -f
pull:
	docker compose pull
build:
	docker compose build
up: pull build
	docker compose up -d
	make ps
ps:
	docker compose ps
proto:
	@docker run --rm \
		-v "$$(pwd)/proto:/proto" \
		-v "$$(pwd)/services:/services" \
		-v "$$(pwd)/gateway:/gateway" \
		python:3.13 bash -c " \
		pip install -q grpcio-tools && \
		for service in user product order; do \
			rm -rf /services/\$$service/src/generated && \
			mkdir -p /services/\$$service/src/generated && \
			python -m grpc_tools.protoc -I/proto/\$$service \
				--python_out=/services/\$$service/src/generated \
				--grpc_python_out=/services/\$$service/src/generated \
				/proto/\$$service/\$$service.proto && \
			sed -i \"s/^import \(.*\)_pb2 as/from . import \1_pb2 as/\" /services/\$$service/src/generated/\$${service}_pb2_grpc.py && \
			touch /services/\$$service/src/generated/__init__.py; \
		done && \
		rm -rf /gateway/src/generated && \
		mkdir -p /gateway/src/generated/user /gateway/src/generated/product /gateway/src/generated/order && \
		for service in user product order; do \
			python -m grpc_tools.protoc -I/proto/\$$service --python_out=/gateway/src/generated/\$$service --grpc_python_out=/gateway/src/generated/\$$service /proto/\$$service/\$$service.proto && \
			sed -i \"s/^import \(.*\)_pb2 as/from . import \1_pb2 as/\" /gateway/src/generated/\$$service/\$${service}_pb2_grpc.py; \
		done && \
		touch /gateway/src/generated/__init__.py /gateway/src/generated/user/__init__.py /gateway/src/generated/product/__init__.py /gateway/src/generated/order/__init__.py && \
		echo 'Proto files compiled successfully'"
test: test.user test.product test.order
test.user:
	@docker compose run -T --rm user uv run pytest tests/ -v -s
test.product:
	@docker compose run -T --rm product uv run pytest tests/ -v -s
test.order:
	@docker compose run -T --rm order uv run pytest tests/ -v -s
debug:
	docker compose -f docker compose.yml -f docker compose.debug.yml up --build
prune:
	make down
	docker volume prune -f
	docker system prune -f
upgrade: upgrade.user upgrade.product upgrade.order
upgrade.user:
	@docker compose run -T --rm user uv run alembic upgrade head
upgrade.product:
	@docker compose run -T --rm product uv run alembic upgrade head
upgrade.order:
	@docker compose run -T --rm order uv run alembic upgrade head
fixtures: fixtures.user fixtures.product fixtures.order
fixtures.user:
	@docker compose run -T --rm user uv run python -m src.fixtures
fixtures.product:
	@docker compose run -T --rm product uv run python -m src.fixtures
fixtures.order:
	@docker compose run -T --rm order uv run python -m src.fixtures
migrate:
	docker compose run -T --rm user uv run alembic revision --autogenerate
	docker compose run -T --rm product uv run alembic revision --autogenerate
	docker compose run -T --rm order uv run alembic revision --autogenerate
