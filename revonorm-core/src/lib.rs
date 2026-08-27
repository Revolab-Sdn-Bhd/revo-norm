//! revonorm-core — Rust core for revo-norm, single-source multi-SDK.
//!
//! One normalization logic, consumed as:
//!   - wasm  (browser, revolab-web)
//!   - cdylib (C ABI — C# via DllImport, Python via ctypes)
//!   - PyO3  (future native wheel)
//!
//! Parity with the Python implementation is asserted against fixtures
//! generated from the Python code (`tests/gen_fixtures.py` output).
//!
//! Milestone 1: Malay path. en/id/zh/zh_my return a not-ported error until
//! their milestones land — never a silent Malay fallback.

pub mod entities;
pub mod options;
pub mod pron;
pub mod lang;
pub mod langpack;
pub mod normalize;
pub mod normalize_id;
pub mod num2word;
pub mod pipeline;
pub mod shared;

#[cfg(target_arch = "wasm32")]
pub mod wasm;

pub use num2word::to_cardinal;
pub use normalize::normalize_malay;
pub use pipeline::normalize;
