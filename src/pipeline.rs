//! 白底处理管道：光照归一化 → 背景增白 → 白边裁剪

use rayon::prelude::*;

use crate::ops;

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Mode {
    Natural,
    Balanced,
    Ultra,
}

impl Mode {
    pub fn parse(s: Option<&str>) -> Option<Self> {
        match s.unwrap_or("balanced") {
            "natural" => Some(Self::Natural),
            "balanced" => Some(Self::Balanced),
            "ultra" => Some(Self::Ultra),
            _ => None,
        }
    }

    pub fn as_str(self) -> &'static str {
        match self {
            Self::Natural => "natural",
            Self::Balanced => "balanced",
            Self::Ultra => "ultra",
        }
    }

    fn target(self) -> f32 {
        match self {
            Self::Natural => 244.0,
            Self::Balanced => 248.0,
            Self::Ultra => 250.0,
        }
    }
    fn max_gain(self) -> f32 {
        match self {
            Self::Natural => 1.8,
            Self::Balanced => 2.0,
            Self::Ultra => 2.4,
        }
    }
    fn white_push(self) -> f32 {
        match self {
            Self::Ultra => 0.35,
            _ => 0.0,
        }
    }
    // 灰点白平衡：把纸色拉到中性白（natural 保留原色温）
    fn gray_balance(self) -> bool {
        !matches!(self, Self::Natural)
    }
}

pub struct Processed {
    pub data: Vec<u8>,
    pub w: u32,
    pub h: u32,
}

pub fn whiten(rgb: Vec<u8>, w: u32, h: u32, mode: Mode, max_dim: u32) -> Processed {
    let (rgb, w, h) = resize_if_needed(rgb, w, h, max_dim);
    let n = (w as usize) * (h as usize);
    if n == 0 {
        return Processed { data: rgb, w, h };
    }

    // 1-3) 光照归一化 + 选择性白化：低频光照场估计 → 除法去除光照不均 →
    // 仅把接近纸张亮度的像素推向 target（插图中间调保留，不被冲淡）
    let target = mode.target();
    let mut out = rgb;
    illumination_pass(
        &mut out,
        w as usize,
        h as usize,
        target,
        mode.max_gain(),
        mode.gray_balance(),
    );
    if mode.gray_balance() {
        // 4) 灰点白平衡：逐通道 P75 估纸色，全局增益拉到中性白（不吃彩色内容饱和度）
        let g = gray_gains(&out, target);
        out.par_chunks_exact_mut(3).for_each(|px| {
            for i in 0..3 {
                let v = px[i] as f32 * g[i];
                px[i] = if v >= 255.0 { 255 } else { v as u8 };
            }
        });
    }

    // 5) ultra：高亮区软推向纯白，清除残余背景噪点
    let push = mode.white_push();
    if push > 0.0 {
        out.par_chunks_exact_mut(3).for_each(|px| {
            let luma = 0.299 * px[0] as f32 + 0.587 * px[1] as f32 + 0.114 * px[2] as f32;
            if luma > 190.0 {
                let k = push * smoothstep(190.0, 242.0, luma);
                for c in px {
                    *c = (*c as f32 + k * (255.0 - *c as f32)) as u8;
                }
            }
        });
    }

    // 6) 裁掉四周白边
    let wu = w as usize;
    let hu = h as usize;
    let (data, fw, fh) = match crop_bounds(&out, wu, hu) {
        Some((x0, y0, cw, ch)) => {
            let mut data = Vec::with_capacity(cw * ch * 3);
            for row in y0..y0 + ch {
                let s = (row * wu + x0) * 3;
                data.extend_from_slice(&out[s..s + cw * 3]);
            }
            (data, cw, ch)
        }
        None => (out, wu, hu),
    };
    Processed {
        data,
        w: fw as u32,
        h: fh as u32,
    }
}

/// 光照归一化 + 选择性白化：
/// 1) 低频光照场 L：强下采样 + 大核中值 + 上采样。下采样后插图/文字在小图上只剩几个像素，
///    被中值滤除，光照场只含光照不均——插图灰块不会进入背景场被误白化。
/// 2) base_gain = white_ref / L：除法归一化，所有内容恢复“亮区时的亮度”（纸均匀、插图恢复灰度）
/// 3) alpha 白化：仅接近纸张亮度的像素被推向 target（插图中间调 alpha=0 完全保留）
/// adaptive_cap：场景存在正常白纸（white_ref≥170）时放开上限到 4.2，深阴影一步平坦化。
fn illumination_pass(
    out: &mut [u8],
    w: usize,
    h: usize,
    target: f32,
    max_gain: f32,
    adaptive_cap: bool,
) {
    let n = w * h;
    let mut illum = vec![0u8; n];
    for i in 0..n {
        let p = i * 3;
        illum[i] = out[p].max(out[p + 1]).max(out[p + 2]);
    }
    let l_field = lowfreq_illumination(&illum, w, h);

    // 全局纸张参考亮度（P90：纸张在文档图中占多数且在亮端）
    let hist = l_field
        .par_iter()
        .fold(
            || [0u32; 256],
            |mut hh, &v| {
                hh[v as usize] += 1;
                hh
            },
        )
        .reduce(
            || [0u32; 256],
            |mut a, b| {
                for i in 0..256 {
                    a[i] += b[i];
                }
                a
            },
        );
    let white_ref = hist_percentile(&hist, n as u32, 0.90).max(60) as f32;
    let cap = if adaptive_cap && white_ref >= 170.0 {
        4.2
    } else {
        max_gain
    };

    // 白化调制区间：[lo, hi] 之间从 0 过渡到全推；低于 lo（插图/文字）保持不动
    let lo = white_ref * 0.78;
    let hi = white_ref * 0.93;
    let push = target / white_ref;

    out.par_chunks_exact_mut(3)
        .zip(illum.par_iter())
        .zip(l_field.par_iter())
        .for_each(|((px, &il), &lf)| {
            let base = white_ref / (lf as f32).max(1.0);
            // 用归一化后的亮度调制白化：阴影区的纸恢复后同样是纸（要推白），
            // 插图恢复后仍是中间调（保留）
            let lum_after = il as f32 * base;
            let alpha = smoothstep(lo, hi, lum_after);
            let boost = 1.0 + alpha * (push - 1.0);
            let gain = (base * boost).clamp(1.0, cap);
            for c in px {
                let v = (*c as f32) * gain;
                *c = if v >= 255.0 { 255 } else { v as u8 };
            }
        });
}

/// 低频光照场：强下采样（1/8）→ 大核中值 → 上采样回全尺寸。
/// 下采样后插图/文字等局部内容尺度过小被滤除，只保留光照不均。
fn lowfreq_illumination(illum: &[u8], w: usize, h: usize) -> Vec<u8> {
    const DS: usize = 8;
    let sw = (w / DS).max(16);
    let sh = (h / DS).max(16);
    let img = match image::GrayImage::from_raw(w as u32, h as u32, illum.to_vec()) {
        Some(i) => i,
        None => return illum.to_vec(),
    };
    let small =
        image::imageops::resize(&img, sw as u32, sh as u32, image::imageops::FilterType::Triangle);
    // 小图中值核：覆盖小图约 1/4 宽度 ≈ 全图 2 倍下采样宽度，足以滤掉 <200px 的插图块
    let radius = (sw / 8).max(3);
    let filtered = ops::median_blur(small.as_raw(), sw, sh, radius);
    let small_img = match image::GrayImage::from_raw(sw as u32, sh as u32, filtered) {
        Some(i) => i,
        None => return illum.to_vec(),
    };
    image::imageops::resize(&small_img, w as u32, h as u32, image::imageops::FilterType::Triangle)
        .into_raw()
}

fn resize_if_needed(rgb: Vec<u8>, w: u32, h: u32, max_dim: u32) -> (Vec<u8>, u32, u32) {
    if w <= max_dim && h <= max_dim {
        return (rgb, w, h);
    }
    let img = match image::RgbImage::from_raw(w, h, rgb) {
        Some(img) => img,
        None => return (Vec::new(), w, h),
    };
    let resized = image::DynamicImage::ImageRgb8(img)
        .resize(max_dim, max_dim, image::imageops::FilterType::Triangle);
    let out = resized.into_rgb8();
    let (nw, nh) = (out.width(), out.height());
    (out.into_raw(), nw, nh)
}

const CROP_T: u32 = 240; // 白边判定亮度阈值（luma8 为 0-255 整数近似）

/// 返回 Some((x0, y0, 宽, 高))；无需裁剪时返回 None
fn crop_bounds(rgb: &[u8], w: usize, h: usize) -> Option<(usize, usize, usize, usize)> {
    let extents: Vec<Option<(usize, usize)>> = (0..h)
        .into_par_iter()
        .map(|y| {
            let row = &rgb[y * w * 3..(y + 1) * w * 3];
            let mut min_x = None;
            let mut max_x = 0usize;
            for x in 0..w {
                let p = x * 3;
                if luma8(row[p], row[p + 1], row[p + 2]) < CROP_T {
                    if min_x.is_none() {
                        min_x = Some(x);
                    }
                    max_x = x;
                }
            }
            min_x.map(|mn| (mn, max_x))
        })
        .collect();

    let mut y0: Option<usize> = None;
    let mut y1 = 0usize;
    let mut x0 = usize::MAX;
    let mut x1 = 0usize;
    for (y, ext) in extents.iter().enumerate() {
        if let Some((mn, mx)) = ext {
            if y0.is_none() {
                y0 = Some(y);
            }
            y1 = y;
            x0 = x0.min(*mn);
            x1 = x1.max(*mx);
        }
    }
    let y0 = y0?;
    if x0 == usize::MAX {
        return None;
    }
    let cw = x1 - x0 + 1;
    let ch = y1 - y0 + 1;
    if cw == w && ch == h {
        return None;
    }
    Some((x0, y0, cw, ch))
}

fn smoothstep(a: f32, b: f32, x: f32) -> f32 {
    let t = ((x - a) / (b - a)).clamp(0.0, 1.0);
    t * t * (3.0 - 2.0 * t)
}

#[inline]
fn luma8(r: u8, g: u8, b: u8) -> u32 {
    (r as u32 * 77 + g as u32 * 150 + b as u32 * 29) >> 8
}

/// 用 256-bin 直方图 + rayon fold 统计
fn hist_fold<F: Fn(&[u8], &mut [u32; 256]) + Copy + Send + Sync>(rgb: &[u8], f: F) -> [u32; 256] {
    rgb.par_chunks_exact(3)
        .fold(
            || [0u32; 256],
            |mut h, px| {
                f(px, &mut h);
                h
            },
        )
        .reduce(
            || [0u32; 256],
            |mut a, b| {
                for i in 0..256 {
                    a[i] += b[i];
                }
                a
            },
        )
}

fn hist_percentile(hist: &[u32; 256], total: u32, p: f32) -> u32 {
    let want = (total as f64 * p as f64) as u64;
    let mut cum = 0u64;
    for (v, &c) in hist.iter().enumerate() {
        cum += c as u64;
        if cum >= want {
            return v as u32;
        }
    }
    255
}

/// 纸色估计：逐通道 P75 分位数（文档图中纸面占多数且总在亮端）。
/// 返回把纸色拉到 target 的全局白平衡增益（全局增益不会吃掉彩色内容的饱和度）
fn gray_gains(rgb: &[u8], target: f32) -> [f32; 3] {
    let mut gains = [1.0f32; 3];
    for i in 0..3 {
        let hist = hist_fold(rgb, |px, h| h[px[i] as usize] += 1);
        let total: u32 = hist.iter().sum();
        if total == 0 {
            continue;
        }
        let paper = hist_percentile(&hist, total, 0.75).max(40) as f32;
        gains[i] = (target / paper).clamp(1.0, 1.4);
    }
    gains
}
