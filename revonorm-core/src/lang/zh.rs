//! Chinese packs — mirrors revo_norm/langpack.py's "zh" and "zh_my" entries
//! (identical vocabulary; only normalization behavior diverges, which lives
//! in the language normalizer, not the pack).

use std::collections::HashMap;

use crate::langpack::LanguagePack;

fn base_pack(code: &'static str) -> LanguagePack {
    LanguagePack {
        code,
        currency_names: Default::default(),
        symbol_words: [
            ('&', "和".to_string()),
            ('+', "加".to_string()),
            ('=', "等于".to_string()),
            ('@', "at".to_string()), // zh_my uses "at"; zh uses 艾特 — split below
            ('#', "hash".to_string()),
            ('*', "星号".to_string()),
            ('%', "巴仙".to_string()),
            ('$', "块".to_string()),
            ('©', "版权".to_string()),
            ('®', "注册".to_string()),
            ('™', "商标".to_string()),
            ('<', "小于".to_string()),
            ('>', "大于".to_string()),
            ('|', "竖线".to_string()),
            ('~', "波浪号".to_string()),
            ('^', "插入符".to_string()),
        ]
        .into_iter()
        .collect(),
        symbol_words_multi: [
            ("EUR", "欧元".to_string()),
            ("GBP", "英镑".to_string()),
        ]
        .into_iter()
        .collect(),
        digit_words: [
            ('0', "零"),
            ('1', "一"),
            ('2', "二"),
            ('3', "三"),
            ('4', "四"),
            ('5', "五"),
            ('6', "六"),
            ('7', "七"),
            ('8', "八"),
            ('9', "九"),
        ]
        .into_iter()
        .collect(),
        negative_word: "负",
        month_names: HashMap::new(), // zh dates handled in the zh normalizer
        drops_exclamation: false,
        distance_units: Default::default(),
        volume_units: Default::default(),
        weight_units: Default::default(),
        duration_units: Default::default(),
        area_units: Default::default(),
        temperature_units: Default::default(),
        fraction_word: "per",
        times_word: "kali",
        hijri_suffix: "Hijri",
    }
}

pub fn pack() -> &'static LanguagePack {
    static PACK: std::sync::LazyLock<LanguagePack> = std::sync::LazyLock::new(|| {
        let mut p = base_pack("zh");
        p.symbol_words.insert('@', "艾特".to_string());
        p.symbol_words.insert('#', "井".to_string());
        p.symbol_words.insert('$', "美元".to_string());
        p
    });
    &PACK
}

pub fn pack_zh_my() -> &'static LanguagePack {
    static PACK: std::sync::LazyLock<LanguagePack> = std::sync::LazyLock::new(|| base_pack("zh_my"));
    &PACK
}
