//! 基础算子：直方图中值滤波（Huang 算法）

use rayon::prelude::*;

/// 灰度图大核中值滤波，窗口 (2r+1)^2，边界处窗口收缩。
/// 滑动直方图实现，单像素 O(1)，按行 rayon 并行。
pub fn median_blur(src: &[u8], w: usize, h: usize, radius: usize) -> Vec<u8> {
    debug_assert_eq!(src.len(), w * h);
    let mut dst = vec![0u8; w * h];
    if w == 0 || h == 0 {
        return dst;
    }

    dst.par_chunks_mut(w)
        .enumerate()
        .for_each(|(y, drow)| {
            let ys = y.saturating_sub(radius);
            let ye = (y + radius + 1).min(h);
            let rows = (ye - ys) as u32;

            // 初始窗口：列 [0, xe]
            let mut hist = [0u32; 256];
            let xe = radius.min(w - 1);
            for yy in ys..ye {
                for &v in &src[yy * w..yy * w + xe + 1] {
                    hist[v as usize] += 1;
                }
            }
            let mut area = rows * (xe as u32 + 1);
            let mut want = (area + 1) / 2;

            // med：满足 cum(v) >= want 的最小值；below：小于 med 的像素数
            let mut med = 0usize;
            let mut below = 0u32;
            for (v, &c) in hist.iter().enumerate() {
                if below + c >= want {
                    med = v;
                    break;
                }
                below += c;
            }
            drow[0] = med as u8;

            for x in 1..w {
                if x + radius < w {
                    let xc = x + radius;
                    for yy in ys..ye {
                        let v = src[yy * w + xc] as usize;
                        hist[v] += 1;
                        if v < med {
                            below += 1;
                        }
                    }
                    area += rows;
                    want = (area + 1) / 2;
                }
                if x > radius {
                    let xc = x - radius - 1;
                    for yy in ys..ye {
                        let v = src[yy * w + xc] as usize;
                        hist[v] -= 1;
                        if v < med {
                            below -= 1;
                        }
                    }
                    area -= rows;
                    want = (area + 1) / 2;
                }
                while med < 255 && below + hist[med] < want {
                    below += hist[med];
                    med += 1;
                }
                while med > 0 && below >= want {
                    med -= 1;
                    below -= hist[med];
                }
                drow[x] = med as u8;
            }
        });

    dst
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn median_matches_brute_force() {
        let (w, h, r) = (61usize, 47usize, 5usize);
        let src: Vec<u8> = (0..w * h).map(|i| (i * 37 % 251) as u8).collect();
        let got = median_blur(&src, w, h, r);
        for y in 0..h {
            for x in 0..w {
                let ys = y.saturating_sub(r)..(y + r + 1).min(h);
                let xs = x.saturating_sub(r)..(x + r + 1).min(w);
                let mut vals = Vec::new();
                for yy in ys {
                    for xx in xs.clone() {
                        vals.push(src[yy * w + xx]);
                    }
                }
                vals.sort_unstable();
                // 与实现一致的下中位数：cum >= (area+1)/2 的最小值
                let want = vals[(vals.len() + 1) / 2 - 1];
                assert_eq!(got[y * w + x], want, "at ({x},{y})");
            }
        }
    }
}
