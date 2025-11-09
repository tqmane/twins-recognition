FROM python:3.12-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake git libopenblas-dev libjpeg-dev libpng-dev && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml README.md requirements.txt ./
COPY src ./src
RUN pip install --no-cache-dir -e .

FROM python:3.12-slim
WORKDIR /app
COPY --from=build /usr/local /usr/local
COPY README.md ./
COPY src ./src
ENTRYPOINT ["twins-cli"]
CMD ["--help"]