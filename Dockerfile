FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

RUN chmod +x entrypoint.sh

EXPOSE 8443
EXPOSE 443
EXPOSE 80