# Step 1: Specify the base image with the required AMD64 architecture.
# We use a slim Python image to keep the final container size small.
FROM --platform=linux/amd64 python:3.9-slim

# Step 2: Set the working directory inside the container.
# All subsequent commands will run from this path.
WORKDIR /app

# Step 3: Copy the requirements file first.
# This is a Docker best practice. It caches this layer, so dependencies are not
# re-installed every time you change your code, making builds faster.
COPY requirements.txt .

# Step 4: Install the Python dependencies listed in requirements.txt.
# The --no-cache-dir flag helps to keep the image size smaller.
RUN pip install --no-cache-dir -r requirements.txt

# Step 5: Copy all your Python code and project files into the container.
COPY . .

# Step 6: Specify the command to run when the container starts.
# This will execute your main script. The container will automatically
# process PDFs from /app/input and exit.
CMD ["python", "main.py"]