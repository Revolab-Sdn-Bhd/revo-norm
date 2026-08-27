//! Snapshot tests — the engine is the source of truth; fixtures record its
//! output (tests/gen_fixtures.py). CI regenerates on every PR and asserts
//! byte-equality: any output change must be a deliberate snapshot update.

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

const LANGS: [&str; 5] = ["ms", "id", "en", "zh", "zh_my"];

#[test]
fn pipeline_standard_all_langs() {
    for lang in LANGS {
        for (input, expected) in fixtures(&format!("pipeline_{lang}.txt")) {
            let got = normalize(&input, lang, "").unwrap_or_else(|e| panic!("{lang} {input:?}: {e}"));
            assert_eq!(got, expected, "standard/{lang} {input:?}");
        }
    }
}

#[test]
fn pipeline_minimal_all_langs() {
    for lang in LANGS {
        for (input, expected) in fixtures(&format!("pipeline_{lang}_minimal.txt")) {
            let got = normalize(&input, lang, r#"{"profile":"minimal"}"#)
                .unwrap_or_else(|e| panic!("{lang} {input:?}: {e}"));
            assert_eq!(got, expected, "minimal/{lang} {input:?}");
        }
    }
}

#[test]
fn pipeline_basic_all_langs() {
    for lang in LANGS {
        for (input, expected) in fixtures(&format!("pipeline_{lang}_basic.txt")) {
            let got = normalize(&input, lang, r#"{"profile":"basic"}"#)
                .unwrap_or_else(|e| panic!("{lang} {input:?}: {e}"));
            assert_eq!(got, expected, "basic/{lang} {input:?}");
        }
    }
}

#[test]
fn unknown_language_errors() {
    let err = normalize("x", "tl", "").unwrap_err();
    assert!(err.contains("tl"), "error must name the bad code: {err}");
}

#[test]
fn empty_input_returns_empty() {
    assert_eq!(normalize("", "ms", "").unwrap(), "");
    assert_eq!(normalize("   ", "ms", "").unwrap(), "");
}

// --- options / pronunciation layers (inline — config semantics) ----------

#[test]
fn options_pronunciation_user_layer() {
    let got = normalize(
        "top up RevoPay RM30K",
        "ms",
        r#"{"pronunciations": {"*": {"RevoPay": "revo pay"}}}"#,
    )
    .unwrap();
    assert_eq!(got, "top up revo pay tiga puluh ribu ringgit");
}

#[test]
fn options_pronunciation_none_deletes() {
    let got = normalize(
        "sambung WiFi sekarang",
        "ms",
        r#"{"pronunciations": {"*": {"WiFi": null}}}"#,
    )
    .unwrap();
    assert_eq!(got, "sambung WiFi sekarang", "null deletes the builtin entry");
}

#[test]
fn options_pronunciation_profile_none() {
    let got = normalize("sambung WiFi sekarang", "ms", r#"{"pronunciation_profile": "none"}"#).unwrap();
    assert_eq!(got, "sambung WiFi sekarang");
}

#[test]
fn options_unknown_field_rejected() {
    let err = revonorm_core::options::Options::parse(r#"{"typo_field": 1}"#).unwrap_err();
    assert!(err.contains("invalid options JSON"), "got: {err}");
}

#[test]
fn builtin_honorifics_ms_only() {
    assert_eq!(normalize("Hj Ahmad datang", "ms", "").unwrap(), "Haji Ahmad datang");
}

#[test]
fn wasm_error_prefix() {
    // errors cross the wasm boundary as __ERROR__ strings; native callers
    // see Err — both surface the same message
    let err = normalize("x", "tl", "").unwrap_err();
    assert!(err.starts_with("Unsupported language"), "got: {err}");
}
