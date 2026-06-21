# syntax=docker/dockerfile:1

# TARGETARCH によるベースイメージの分岐:
#   arm (32-bit, arm/v7) → python:3-slim  (dhi.io/python は arm/v7 非対応)
#   amd64, arm64         → dhi.io/python:3-debian-sfw-ent-dev (DHI ハードニングイメージ)
ARG TARGETARCH

FROM python:3-slim AS base-arm
FROM dhi.io/python:3-debian-sfw-ent-dev AS base-amd64
FROM dhi.io/python:3-debian-sfw-ent-dev AS base-arm64

FROM base-${TARGETARCH}
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py sensor.py /app/
ENTRYPOINT ["python3", "-u"]
CMD ["/app/main.py"]
