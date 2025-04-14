FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy generated code first if not mounting volumes
# COPY generated ./generated
COPY . .

# Profile service gRPC port
EXPOSE 50052 

# Define environment variables (can be overridden by docker-compose)
ENV AUTH_SERVICE_URL=auth_service:50051

CMD ["python", "-u", "server.py"]