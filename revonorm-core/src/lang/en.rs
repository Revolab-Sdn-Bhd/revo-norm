//! English pack — mirrors revo_norm/langpack.py's "en" entry.


use crate::langpack::LanguagePack;

pub fn pack() -> &'static LanguagePack {
    static PACK: std::sync::LazyLock<LanguagePack> = std::sync::LazyLock::new(|| LanguagePack {
        code: "en",
        currency_names: Default::default(),
        symbol_words: [
            ('&', "and".to_string()),
            ('+', "plus".to_string()),
            ('=', "equals".to_string()),
            ('@', "at".to_string()),
            ('#', "hash".to_string()),
            ('*', String::new()), // dropped silently
            ('%', "percent".to_string()),
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
            ('0', "zero"),
            ('1', "one"),
            ('2', "two"),
            ('3', "three"),
            ('4', "four"),
            ('5', "five"),
            ('6', "six"),
            ('7', "seven"),
            ('8', "eight"),
            ('9', "nine"),
        ]
        .into_iter()
        .collect(),
        negative_word: "negative",
        month_names: [
            ("1", "January"),
            ("2", "February"),
            ("3", "March"),
            ("4", "April"),
            ("5", "May"),
            ("6", "June"),
            ("7", "July"),
            ("8", "August"),
            ("9", "September"),
            ("10", "October"),
            ("11", "November"),
            ("12", "December"),
        ]
        .into_iter()
        .collect(),
        drops_exclamation: true,
        distance_units: Default::default(),
        volume_units: Default::default(),
        weight_units: Default::default(),
        duration_units: Default::default(),
        area_units: Default::default(),
        temperature_units: Default::default(),
        fraction_word: "per",
        times_word: "kali",
        hijri_suffix: "Hijri",
    });
    &PACK
}
