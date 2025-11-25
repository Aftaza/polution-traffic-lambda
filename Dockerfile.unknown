# Gunakan image Python resmi
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Nonaktifkan buffering output agar log muncul di Docker
ENV PYTHONUNBUFFERED 1

# Copy requirements.txt dan install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy semua file proyek ke container
COPY . .

# Ekspos port default Streamlit
EXPOSE 8501

# Command default (akan di-override di docker-compose)
CMD ["echo", "Running..."]