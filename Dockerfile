FROM python:3.12.3-slim-bookworm

RUN apt-get update && \
    apt-get install -y \
        pkg-config \
        libcairo2-dev \
        build-essential

WORKDIR /culturesFlask

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV HOST 0.0.0.0
ENV PORT 5000
CMD flask --app cultures run --host $HOST --port $PORT