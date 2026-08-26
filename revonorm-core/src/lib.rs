//! revonorm-core — Malay text normalization, single-source multi-SDK core.
//!
//! A faithful Rust port of revo_norm's Malay path (normalizer_ms.py +
//! num2word_ms.py + currency_utils.py). One logic, consumed as:
//!   - wasm  (browser, revolab-web)
//!   - cdylib (C ABI — C# via DllImport, Python via ctypes)
//!   - PyO3  (native python wheel)
//!
//! Parity with the Python implementation is asserted by the test suite
//! against generated ground-truth fixtures.

pub mod normalize;
pub mod num2word;

#[cfg(target_arch = "wasm32")]
pub mod wasm;

pub use num2word::to_cardinal;

pub use normalize::normalize_malay;

#[cfg(test)]
mod tests {
    use super::*;

    // ground truth: python revo_norm.num2word_ms.to_cardinal on 2026-08-26
    #[test]
    fn num2word_parity() {
        for (n, want) in [
            (0u128, "kosong"),
            (1, "satu"),
            (10, "sepuluh"),
            (11, "sebelas"),
            (15, "lima belas"),
            (20, "dua puluh"),
            (21, "dua puluh satu"),
            (23, "dua puluh tiga"),
            (31, "tiga puluh satu"),
            (50, "lima puluh"),
            (67, "enam puluh tujuh"),
            (100, "seratus"),
            (111, "seratus sebelas"),
            (1000, "seribu"),
            (1001, "seribu satu"),
            (1990, "seribu sembilan ratus sembilan puluh"),
            (2000, "dua ribu"),
            (5670, "lima ribu enam ratus tujuh puluh"),
            (8888, "lapan ribu lapan ratus lapan puluh lapan"),
            (9999, "sembilan ribu sembilan ratus sembilan puluh sembilan"),
            (10000, "sepuluh ribu"),
            (25000, "dua puluh lima ribu"),
            (30000, "tiga puluh ribu"),
            (100000, "seratus ribu"),
            (1000000, "satu juta"),
            (1567023, "satu juta lima ratus enam puluh tujuh ribu dua puluh tiga"),
        ] {
            assert_eq!(to_cardinal(n), want, "to_cardinal({n})");
        }
    }
}
