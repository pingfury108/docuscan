//! API 层：仅保留 图片 → 白底 → 返回图片

use axum::body::Body;
use axum::extract::{Json, State};
use axum::http::{header, StatusCode};
use axum::response::{IntoResponse, Response};
use serde::Deserialize;
use serde_json::json;

use crate::pipeline::Mode;
use crate::{codec, pipeline, AppConfig};

#[derive(Deserialize)]
pub struct ScanRequest {
    pub img: String,
    pub mode: Option<String>,
}

pub struct ApiError(StatusCode, String);

impl ApiError {
    fn bad(msg: impl Into<String>) -> Self {
        Self(StatusCode::BAD_REQUEST, msg.into())
    }
    fn internal(msg: impl Into<String>) -> Self {
        Self(StatusCode::INTERNAL_SERVER_ERROR, msg.into())
    }
}

impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        (self.0, Json(json!({ "detail": self.1 }))).into_response()
    }
}

struct ScanOutput {
    jpeg: Vec<u8>,
    original: (u32, u32),
    final_size: (u32, u32),
    mode: Mode,
}

pub async fn scan_document(
    State(cfg): State<AppConfig>,
    Json(req): Json<ScanRequest>,
) -> Result<Response, ApiError> {
    let started = std::time::Instant::now();
    let mode = Mode::parse(req.mode.as_deref())
        .ok_or_else(|| ApiError::bad("invalid mode, valid: natural | balanced | ultra"))?;
    let max_dim = cfg.max_dim;

    let out = tokio::task::spawn_blocking(move || -> Result<ScanOutput, ApiError> {
        let raw = codec::decode_base64(&req.img)
            .map_err(|e| ApiError::bad(format!("Invalid base64 encoding: {e}")))?;
        let (rgb, w, h) = codec::decode_image(&raw)
            .map_err(|e| ApiError::bad(format!("Invalid image: {e}")))?;
        let processed = pipeline::whiten(rgb, w, h, mode, max_dim);
        let jpeg = codec::encode_jpeg(&processed.data, processed.w, processed.h, 95)
            .map_err(|e| ApiError::internal(format!("JPEG encode failed: {e}")))?;
        Ok(ScanOutput {
            jpeg,
            original: (w, h),
            final_size: (processed.w, processed.h),
            mode,
        })
    })
    .await
    .map_err(|e| ApiError::internal(format!("task join failed: {e}")))??;

    tracing::info!(
        "scan mode={} {}x{} -> {}x{} {}KB {}ms",
        out.mode.as_str(),
        out.original.0,
        out.original.1,
        out.final_size.0,
        out.final_size.1,
        out.jpeg.len() / 1024,
        started.elapsed().as_millis()
    );

    let response = Response::builder()
        .header(header::CONTENT_TYPE, "image/jpeg")
        .header(
            header::CONTENT_DISPOSITION,
            format!("inline; filename=scanned_document_{}.jpg", out.mode.as_str()),
        )
        .header("X-Scan-Mode", out.mode.as_str())
        .header(
            "X-Original-Size",
            format!("{}x{}", out.original.0, out.original.1),
        )
        .header(
            "X-Final-Size",
            format!("{}x{}", out.final_size.0, out.final_size.1),
        )
        .body(Body::from(out.jpeg))
        .map_err(|e| ApiError::internal(e.to_string()))?;
    Ok(response)
}
