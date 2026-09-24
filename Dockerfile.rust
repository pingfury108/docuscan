# DocuScan 白底 API（Rust 版）
FROM rust:1-slim AS builder
WORKDIR /app
COPY Cargo.toml Cargo.lock ./
COPY src/ ./src/
RUN cargo build --release

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=builder /app/target/release/docuscan /usr/local/bin/docuscan
ENV PORT=8000 MAX_DIM=2000
EXPOSE 8000
CMD ["docuscan"]
