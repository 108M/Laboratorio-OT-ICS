FROM python:3.12-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends iproute2 iputils-ping tcpdump \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /attack
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["sleep", "infinity"]
