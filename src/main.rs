//! DocuScan —— 白底文档扫描 API（Rust 实现）
//!
//! POST /scan-document  {img: base64, mode?: natural|balanced|ultra}  -> image/jpeg
//! GET  /health

mod api;
mod codec;
mod ops;
mod pipeline;

use axum::extract::DefaultBodyLimit;
use axum::routing::{get, post};
use axum::{Json, Router};
use serde_json::json;
use std::net::SocketAddr;
use tower_http::cors::CorsLayer;

#[derive(Clone)]
pub struct AppConfig {
    pub max_dim: u32,
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "docuscan=info".into()),
        )
        .init();

    let port: u16 = std::env::var("PORT")
        .ok()
        .and_then(|v| v.parse().ok())
        .unwrap_or(8000);
    let max_dim: u32 = std::env::var("MAX_DIM")
        .ok()
        .and_then(|v| v.parse().ok())
        .unwrap_or(2000);

    let app = Router::new()
        .route("/scan-document", post(api::scan_document))
        .route("/health", get(health))
        .layer(CorsLayer::permissive())
        .layer(DefaultBodyLimit::max(64 * 1024 * 1024))
        .with_state(AppConfig { max_dim });

    let addr = SocketAddr::from(([0, 0, 0, 0], port));
    let listener = tokio::net::TcpListener::bind(addr)
        .await
        .unwrap_or_else(|e| panic!("bind {addr} failed: {e}"));
    tracing::info!("docuscan-rs listening on http://{addr} (max_dim={max_dim})");
    axum::serve(listener, app)
        .await
        .expect("server error");
}

async fn health() -> Json<serde_json::Value> {
    Json(json!({ "status": "ok" }))
}
