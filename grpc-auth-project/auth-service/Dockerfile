# Use Python 3.10
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# --no-cache-dir: Reduces image size by not storing the pip cache
# --trusted-host pypi.python.org --trusted-host pypi.org --trusted-host files.pythonhosted.org: 
# Needed sometimes in specific network environments/proxies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt # --trusted-host pypi.python.org --trusted-host pypi.org --trusted-host files.pythonhosted.org

# Copy the rest of the application code into the container at /app
# Copy generated code first if you don't mount volumes
# COPY generated ./generated
COPY . .

# Make port 50051 available to the world outside this container (gRPC port)
EXPOSE 50051

# Define environment variables (can be overridden by docker-compose)
ENV DATABASE_URL=postgresql://user:password@postgres_db:5432/authdb
ENV JWT_SECRET=your-super-secret-key

# Run server.py when the container launches
# Use -u for unbuffered output, helps with logging in Docker
CMD ["python", "-u", "server.py"]