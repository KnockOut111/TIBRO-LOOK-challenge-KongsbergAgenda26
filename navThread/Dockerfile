FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    i2c-tools \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY navThread/requirements.txt /tmp/requirements.txt

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

COPY navThread/ /app/

CMD ["python", "roverPi_init.py"]