//! Parity tests — Rust output must byte-match fixtures generated from the
//! Python library (tests/gen_fixtures.py). Regenerate after any Python rule
//! change, then fix Rust until green.

use revonorm_core::{normalize, to_cardinal};

fn fixtures(name: &str) -> Vec<(String, String)> {
    let path = format!("{}/tests/fixtures/{name}", env!("CARGO_MANIFEST_DIR"));
    std::fs::read_to_string(&path)
        .unwrap_or_else(|e| panic!("read {path}: {e} — run gen_fixtures.py"))
        .lines()
        .filter(|l| !l.trim().is_empty())
        .map(|l| match l.split_once('\t') {
            Some((input, expected)) => (input.to_string(), expected.to_string()),
            None => panic!("malformed fixture line: {l:?}"),
        })
        .collect()
}

#[test]
fn num2word_ms_parity() {
    for (input, expected) in fixtures("num2word_ms.txt") {
        let n: u128 = input.parse().unwrap();
        assert_eq!(to_cardinal(n), expected, "num2word({n})");
    }
}

#[test]
fn pipeline_ms_parity() {
    // Tier 1 (full python pipeline) minus entity-extractor cases, plus the
    // normalizer-tier cases: everything milestone-1 Rust must byte-match.
    let mut cases = fixtures("pipeline_ms.txt");
    for (input, expected) in cases {
        let got = normalize(&input, "ms")
            .unwrap_or_else(|e| panic!("normalize({input:?}, ms) errored: {e}"));
        assert_eq!(got, expected, "normalize({input:?}, ms)");
    }
}

#[test]
fn unknown_language_errors() {
    let err = normalize("x", "tl").unwrap_err();
    assert!(err.contains("tl"), "error must name the bad code: {err}");
}

#[test]
fn unported_language_errors_loudly() {
    // en is registered but not ported in milestone 1 — must error, never
    // silently fall back to Malay.
    let err = normalize("hello", "en").unwrap_err();
    assert!(err.contains("not ported"), "got: {err}");
}

#[test]
fn empty_input_returns_empty() {
    assert_eq!(normalize("", "ms").unwrap(), "");
    assert_eq!(normalize("   ", "ms").unwrap(), "");
}

#[test]
fn options_pronunciation_user_layer() {
    let opts = revonorm_core::options::Options::parse(
        r#"{"pronunciations": {"*": {"RevoPay": "revo pay"}}}"#,
    )
    .unwrap();
    let got = revonorm_core::pipeline::normalize_with("top up RevoPay RM30K", "ms", &opts).unwrap();
    assert_eq!(got, "top up revo pay tiga puluh ribu ringgit");
}

#[test]
fn options_pronunciation_none_deletes() {
    let opts = revonorm_core::options::Options::parse(
        r#"{"pronunciations": {"*": {"WiFi": null}}}"#,
    )
    .unwrap();
    let got = revonorm_core::pipeline::normalize_with("sambung WiFi sekarang", "ms", &opts).unwrap();
    assert_eq!(got, "sambung WiFi sekarang", "None must delete the builtin entry");
}

#[test]
fn options_pronunciation_profile_none() {
    let opts = revonorm_core::options::Options::parse(r#"{"pronunciation_profile": "none"}"#).unwrap();
    let got = revonorm_core::pipeline::normalize_with("sambung WiFi sekarang", "ms", &opts).unwrap();
    assert_eq!(got, "sambung WiFi sekarang");
}

#[test]
fn options_pronunciation_scoped() {
    let opts = revonorm_core::options::Options::parse(
        r#"{"pronunciations": {"ms": {"Dr": "Doktor Besar"}}}"#,
    )
    .unwrap();
    let got = revonorm_core::pipeline::normalize_with("jumpa Dr Ali", "ms", &opts).unwrap();
    assert!(got.contains("Doktor Besar"), "got: {got}");
}

#[test]
fn options_unknown_field_rejected() {
    let err = revonorm_core::options::Options::parse(r#"{"typo_field": 1}"#).unwrap_err();
    assert!(err.contains("invalid options JSON"), "got: {err}");
}

#[test]
fn options_builtin_honorifics_ms_only() {
    // builtin honorifics apply to ms
    let got = revonorm_core::pipeline::normalize("Hj Ahmad datang", "ms").unwrap();
    assert_eq!(got, "Haji Ahmad datang");
}
