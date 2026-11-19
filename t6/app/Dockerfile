FROM python:3.12-slim
RUN pip install --no-cache-dir fastapi uvicorn strawberry-graphql grpcio grpcio-tools locust
WORKDIR /app
COPY . .
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. music.proto
