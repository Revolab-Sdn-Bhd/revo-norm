//! Indonesian pack — mirrors revo_norm/langpack.py's "id" entry.


use crate::langpack::LanguagePack;

pub fn pack() -> &'static LanguagePack {
    static PACK: std::sync::LazyLock<LanguagePack> = std::sync::LazyLock::new(|| LanguagePack {
        code: "id",
        currency_names: [
            ("RP", ("rupiah", "sen")), ("IDR", ("rupiah", "sen")),
            ("RM", ("ringgit", "sen")), ("MYR", ("ringgit", "sen")),
            ("$", ("dolar", "sen")), ("USD", ("dolar", "sen")),
            ("£", ("pound", "pence")), ("GBP", ("pound", "pence")),
            ("€", ("euro", "sen")), ("EUR", ("euro", "sen")),
        ]
        .into_iter()
        .collect(),
        symbol_words: [
            ('&', "and".to_string()),
            ('+', "plus".to_string()),
            ('=', "equals".to_string()),
            ('@', "at".to_string()),
            ('#', "hash".to_string()),
            ('*', "star".to_string()), // id keeps speaking it
            ('%', "persen".to_string()),
            ('$', "dollar".to_string()),
            ('©', "copyright".to_string()),
            ('®', "registered".to_string()),
            ('™', "trademark".to_string()),
            ('<', "less than".to_string()),
            ('>', "greater than".to_string()),
            ('|', "bar".to_string()),
            ('~', "tilde".to_string()),
            ('^', "caret".to_string()),
        ]
        .into_iter()
        .collect(),
        symbol_words_multi: [
            ("EUR", "euro".to_string()),
            ("GBP", "pound".to_string()),
        ]
        .into_iter()
        .collect(),
        digit_words: [
            ('0', "nol"),
            ('1', "satu"),
            ('2', "dua"),
            ('3', "tiga"),
            ('4', "empat"),
            ('5', "lima"),
            ('6', "enam"),
            ('7', "tujuh"),
            ('8', "delapan"),
            ('9', "sembilan"),
        ]
        .into_iter()
        .collect(),
        negative_word: "negatif",
        month_names: [
            ("1", "Januari"),
            ("2", "Februari"),
            ("3", "Maret"),
            ("4", "April"),
            ("5", "Mei"),
            ("6", "Juni"),
            ("7", "Juli"),
            ("8", "Agustus"),
            ("9", "September"),
            ("10", "Oktober"),
            ("11", "November"),
            ("12", "Desember"),
        ]
        .into_iter()
        .collect(),
        drops_exclamation: false,
        distance_units: [
            ("km", "kilometer"), ("m", "meter"), ("cm", "sentimeter"),
            ("mm", "milimeter"), ("ft", "kaki"), ("in", "inci"),
            ("yd", "yard"), ("mi", "mil"), ("batu", "batu"),
            ("kaki", "kaki"), ("inci", "inci"),
        ]
        .into_iter()
        .map(|(k, v)| (k.to_string(), v.to_string()))
        .collect(),
        volume_units: [
            ("ml", "mililiter"), ("l", "liter"), ("gal", "galon"),
        ]
        .into_iter()
        .map(|(k, v)| (k.to_string(), v.to_string()))
        .collect(),
        weight_units: [
            ("kg", "kilogram"), ("g", "gram"), ("mg", "miligram"),
            ("lb", "pon"), ("oz", "ons"),
        ]
        .into_iter()
        .map(|(k, v)| (k.to_string(), v.to_string()))
        .collect(),
        duration_units: [
            ("jam", "jam"), ("minit", "menit"), ("saat", "detik"),
            ("hour", "jam"), ("hours", "jam"), ("minute", "menit"),
            ("minutes", "menit"), ("second", "detik"), ("seconds", "detik"),
        ]
        .into_iter()
        .map(|(k, v)| (k.to_string(), v.to_string()))
        .collect(),
        area_units: [
            ("sq ft", "kaki persegi"), ("sqft", "kaki persegi"),
        ]
        .into_iter()
        .map(|(k, v)| (k.to_string(), v.to_string()))
        .collect(),
        temperature_units: [
            ("c", "selsius"), ("f", "fahrenheit"), ("k", "kelvin"),
        ]
        .into_iter()
        .map(|(k, v)| (k.to_string(), v.to_string()))
        .collect(),
        fraction_word: "per",
        times_word: "kali",
        hijri_suffix: "Hijriah",
    });
    &PACK
}
