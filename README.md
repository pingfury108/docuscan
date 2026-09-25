# DocuScan

高性能文档白底扫描 API（Rust 实现）：将文档照片转换为白底扫描风格。

## 功能

- 白底转换：光照归一化 + 灰点白平衡，消除阴影、色偏
- 彩色内容保护：红章/彩色内容保色不变
- 多格式输入：JPEG / PNG / GIF / BMP / WEBP（base64 或 data URL）
- 自动白边裁剪、图像尺寸归一（默认最长边 2000px）

## API

### POST /scan-document

请求（JSON）：

```json
{
  "img": "base64 编码的图片（支持 data:image/...;base64, 前缀）",
  "mode": "balanced"
}
```

`mode` 可选：`natural`（保留原色温）、`balanced`（默认，白底）、`ultra`（超白+噪点清理）。

响应：`image/jpeg` 二进制，附带 headers：

- `X-Scan-Mode`：使用的模式
- `X-Original-Size` / `X-Final-Size`：原图/输出尺寸

### GET /health

健康检查：`{"status": "ok"}`

## 运行

```bash
# 本地
cargo build --release
PORT=8000 ./target/release/docuscan

# Docker
docker build -t docuscan .
docker run -p 8000:8000 docuscan

# docker compose
docker compose up -d
```

环境变量：`PORT`（默认 8000）、`MAX_DIM`（默认 2000）、`RUST_LOG`。

## 示例

```bash
curl -X POST http://localhost:8000/scan-document \
  -H 'Content-Type: application/json' \
  -d '{"img":"...base64...","mode":"balanced"}' \
  --output scanned.jpg
```
