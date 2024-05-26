FROM python:3.12.3-slim-bookworm

RUN apt-get update && \
    apt-get install -y \
        pkg-config \
        libcairo2-dev \
        build-essential \
        libpango1.0-0 \
        libpangocairo-1.0-0

WORKDIR /lab-sample-tracking

COPY requirements.txt .
RUN pip install -r requirements.txt
