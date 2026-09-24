//! base64 / 图像解码 / JPEG 编码

use base64::Engine;

/// 解码 base64，兼容 data URL 前缀与空白字符
pub fn decode_base64(input: &str) -> Result<Vec<u8>, String> {
    let s = input.trim();
    let b64 = if s.starts_with("data:") {
        match s.find(',') {
            Some(i) => &s[i + 1..],
            None => return Err("missing comma after data URL prefix".into()),
        }
    } else {
        s
    };
    let cleaned: String = b64.chars().filter(|c| !c.is_ascii_whitespace()).collect();
    base64::engine::general_purpose::STANDARD
        .decode(cleaned.as_bytes())
        .or_else(|_| {
            base64::engine::general_purpose::STANDARD_NO_PAD
                .decode(cleaned.trim_end_matches('='))
        })
        .map_err(|e| e.to_string())
}

/// 解码任意支持格式（JPEG/PNG/GIF/BMP/WEBP）为 RGB8
pub fn decode_image(bytes: &[u8]) -> Result<(Vec<u8>, u32, u32), String> {
    let img = image::load_from_memory(bytes).map_err(|e| e.to_string())?;
    let rgb = img.to_rgb8();
    let (w, h) = (rgb.width(), rgb.height());
    Ok((rgb.into_raw(), w, h))
}

/// 编码 JPEG
pub fn encode_jpeg(rgb: &[u8], w: u32, h: u32, quality: u8) -> Result<Vec<u8>, String> {
    let mut out = Vec::with_capacity(rgb.len() / 4 + 1024);
    let enc = jpeg_encoder::Encoder::new(&mut out, quality);
    enc.encode(rgb, w as u16, h as u16, jpeg_encoder::ColorType::Rgb)
        .map_err(|e| e.to_string())?;
    Ok(out)
}
