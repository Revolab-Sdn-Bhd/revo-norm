//! Malay pack — mirrors revo_norm/langpack.py's "ms" entry (data dumped
//! from the Python pack; ms deliberately keeps English tech-symbol words).


use crate::langpack::LanguagePack;

pub fn pack() -> &'static LanguagePack {
    static PACK: std::sync::LazyLock<LanguagePack> = std::sync::LazyLock::new(|| LanguagePack {
        code: "ms",
        symbol_words: [
            ('&', "and".to_string()),
            ('+', "plus".to_string()),
            ('=', "equals".to_string()),
            ('@', "at".to_string()),
            ('#', "hash".to_string()),
            ('*', String::new()), // dropped silently (en/ms scope)
            ('%', "peratus".to_string()),
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
            ('0', "kosong"),
            ('1', "satu"),
            ('2', "dua"),
            ('3', "tiga"),
            ('4', "empat"),
            ('5', "lima"),
            ('6', "enam"),
            ('7', "tujuh"),
            ('8', "lapan"),
            ('9', "sembilan"),
        ]
        .into_iter()
        .collect(),
        negative_word: "negatif",
        month_names: [
            ("1", "Januari"),
            ("2", "Februari"),
            ("3", "Mac"),
            ("4", "April"),
            ("5", "Mei"),
            ("6", "Jun"),
            ("7", "Julai"),
            ("8", "Ogos"),
            ("9", "September"),
            ("10", "Oktober"),
            ("11", "November"),
            ("12", "Disember"),
        ]
        .into_iter()
        .collect(),
        drops_exclamation: true,
    });
    &PACK
}
