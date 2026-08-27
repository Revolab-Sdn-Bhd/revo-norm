//! normalize_zh — Chinese paths, ports of revo_norm/num2word_zh.py and
//! normalizer_zh.py. zh_my shares every pass (python imports zh's
//! converters); only pack vocabulary differs.

use fancy_regex::Regex;
use std::sync::LazyLock;

const DIGITS: [char; 10] = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九'];
const LARGE_UNITS: [&str; 4] = ["", "万", "亿", "兆"];

/// Chinese cardinal for integers 0..10^16 (mirrors python _convert_integer).
pub fn to_cardinal_zh(n: u128) -> String {
    if n == 0 {
        return "零".to_string();
    }
    if n >= 10_u128.pow(16) {
        return "太大".to_string(); // python raises; degrade gracefully
    }
    convert_integer(n)
}

fn digit(n: u128) -> char {
    DIGITS[(n % 10) as usize]
}

fn convert_integer(n: u128) -> String {
    if n < 10 {
        return digit(n).to_string();
    }
    if n < 100 {
        return convert_tens(n, false);
    }
    if n < 1000 {
        return convert_hundreds(n);
    }
    if n < 10000 {
        return convert_thousands(n);
    }
    convert_large(n)
}

fn convert_tens(n: u128, embedded: bool) -> String {
    let tens = n / 10;
    let ones = n % 10;
    if tens == 1 && !embedded {
        if ones == 0 {
            return "十".to_string();
        }
        return format!("十{}", digit(ones));
    }
    if ones == 0 {
        return format!("{}十", digit(tens));
    }
    format!("{}十{}", digit(tens), digit(ones))
}

fn convert_hundreds(n: u128) -> String {
    let hundreds = n / 100;
    let remainder = n % 100;
    let result = format!("{}百", digit(hundreds));
    if remainder == 0 {
        return result;
    }
    if remainder < 10 {
        return format!("{result}零{}", digit(remainder));
    }
    format!("{result}{}", convert_tens(remainder, true))
}

fn convert_thousands(n: u128) -> String {
    let thousands = n / 1000;
    let remainder = n % 1000;
    let result = format!("{}千", digit(thousands));
    if remainder == 0 {
        return result;
    }
    if remainder < 100 {
        let mid = if remainder >= 10 {
            convert_tens(remainder, true)
        } else {
            digit(remainder).to_string()
        };
        return format!("{result}零{mid}");
    }
    format!("{result}{}", convert_hundreds(remainder))
}

fn convert_large(n: u128) -> String {
    // group by 10000s with 万/亿/兆
    let mut groups: Vec<(u128, usize)> = Vec::new();
    let mut temp = n;
    let mut unit_idx = 0usize;
    while temp > 0 {
        groups.push((temp % 10000, unit_idx));
        temp /= 10000;
        unit_idx += 1;
    }
    let mut result = String::new();
    for i in (0..groups.len()).rev() {
        let (group_val, uidx) = groups[i];
        if group_val == 0 {
            continue;
        }
        let leading = result.is_empty();
        let group_str = convert_group_of_4(group_val, leading);
        let unit = LARGE_UNITS[uidx];
        if !result.is_empty() && group_val < 1000 {
            result.push('零');
        }
        result.push_str(&group_str);
        result.push_str(unit);
    }
    result
}

fn convert_group_of_4(n: u128, leading: bool) -> String {
    if n < 10 {
        return digit(n).to_string();
    }
    if n < 100 {
        return convert_tens(n, !leading);
    }
    if n < 1000 {
        return convert_hundreds(n);
    }
    convert_thousands(n)
}

/// Year as digit-by-digit chinese (二零二五).
pub fn to_year_zh(year: u128) -> String {
    year.to_string()
        .chars()
        .filter(|c| c.is_ascii_digit())
        .map(|c| DIGITS[(c as u8 - b'0') as usize])
        .collect()
}

pub static MONTHS_ZH: LazyLock<std::collections::HashMap<String, String>> =
    LazyLock::new(|| {
        [
            ("1", "一"), ("2", "二"), ("3", "三"), ("4", "四"), ("5", "五"),
            ("6", "六"), ("7", "七"), ("8", "八"), ("9", "九"), ("10", "十"),
            ("11", "十一"), ("12", "十二"),
        ]
        .into_iter()
        .map(|(k, v)| (k.to_string(), v.to_string()))
        .collect()
    });

static RE_PERCENT: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(\d+(?:\.\d+)?)%").unwrap());
static RE_DECIMAL: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"(\d+)\.(\d+)").unwrap());
static RE_NUMBER: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"\d+").unwrap());
static RE_COMMA_NUM: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?").unwrap());
static RE_DATE_DMY: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(?<!\d)(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})").unwrap());
static RE_DATE_YMD: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(?<!\d)(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})").unwrap());
static RE_CURRENCY: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)(?<![A-Za-z0-9_])(\$|£|€|RM|MYR|USD|EUR|GBP)(?:\s?)([\d,]+(?:[\.,]\d{1,2})?)(?:\s?(千|万|百万|千万|亿|百亿|千亿|万亿|兆))?").unwrap()
});
static RE_DASHED_DIGIT: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(?<![A-Za-z])([+\d]+(?:-[\d]+)+)(?![A-Za-z])").unwrap());
static RE_DASHED_ALNUM: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"([A-Za-z0-9]+(?:-[A-Za-z0-9]+)+)").unwrap());
static RE_ALNUM: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"((?=[A-Za-z0-9]*[A-Za-z])(?=[A-Za-z0-9]*\d)[A-Za-z0-9]+)").unwrap()
});
static RE_TIME: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(?i)(\d{1,2})[:\.](\d{2})\s*(?:(am|pm|a\.m\.|p\.m\.))").unwrap());
static RE_TIME_ZH: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)((?:凌晨|早上|中午|下午|傍晚|晚上))\s*(\d{1,2})[:\.](\d{2})").unwrap()
});
static RE_TIME_NO_MERIDIAN: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)(?<!凌晨)(?<!早上)(?<!中午)(?<!下午)(?<!傍晚)(?<!晚上)(?<!\d)(\d{1,2}):(\d{2})(?!\s*(?:am|pm|a\.m\.|p\.m\.))(?!\s*%)").unwrap()
});
static RE_TIME_SHORTFORM: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?i)(?<!\d)([1-9]|1[0-2])\s*(am|pm|a\.m\.|p\.m\.)(?![A-Za-z0-9])").unwrap()
});
static RE_LEFTOVER_DOT: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(?<=\w)\.(?=\w)").unwrap());

fn zh_digit(ch: char) -> String {
    match ch {
        '0' => "零".into(), '1' => "一".into(), '2' => "二".into(), '3' => "三".into(),
        '4' => "四".into(), '5' => "五".into(), '6' => "六".into(), '7' => "七".into(),
        '8' => "八".into(), '9' => "九".into(),
        _ => ch.to_string(),
    }
}

fn month_zh(m: &str) -> String {
    MONTHS_ZH.get(m).cloned().unwrap_or_else(|| m.to_string())
}

/// Chinese normalization pass — text_normalize_zh (zh variant).
pub fn normalize_zh(text: &str) -> String {
    normalize_zh_variant(text, false)
}

/// zh_my variant: percentage spoken as 巴仙 (colloquial), not 百分之.
pub fn normalize_zh_my(text: &str) -> String {
    normalize_zh_variant(text, true)
}

fn normalize_zh_variant(text: &str, zh_my: bool) -> String {
    let t = RE_PERCENT.replace_all(text, |c: &fancy_regex::Captures<str>| {
        let num = &c[1];
        let (pre, _post) = if zh_my { ("", "巴仙") } else { ("百分之", "") };
        if let Some((w, f)) = num.split_once('.') {
            let fw: String = f.chars().map(|d| to_cardinal_zh(d.to_digit(10).unwrap_or(0) as u128)).collect();
            if zh_my {
                return format!("{}点{fw}巴仙", to_cardinal_zh(w.parse().unwrap_or(0)));
            }
            format!("{pre}{}点{fw}", to_cardinal_zh(w.parse().unwrap_or(0)))
        } else {
            if zh_my {
                return format!("{}巴仙", to_cardinal_zh(num.parse::<f64>().unwrap_or(0.0) as u128));
            }
            format!("百分之{}", to_cardinal_zh(num.parse::<f64>().unwrap_or(0.0) as u128))
        }
    });

    let t = RE_DATE_DMY.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        let (mut day, mut month) = (c[1].to_string(), c[2].to_string());
        if month.parse::<u32>().unwrap_or(0) > 12 && day.parse::<u32>().unwrap_or(0) <= 12 {
            std::mem::swap(&mut day, &mut month);
        }
        format!(
            "{}年{}月{}日",
            to_year_zh(c[3].parse().unwrap_or(0)),
            month_zh(&month),
            to_cardinal_zh(day.parse().unwrap_or(0))
        )
    });
    let t = RE_DATE_YMD.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        format!(
            "{}年{}月{}日",
            to_year_zh(c[1].parse().unwrap_or(0)),
            month_zh(&c[2]),
            to_cardinal_zh(c[3].parse().unwrap_or(0))
        )
    });

    let t = RE_CURRENCY.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        let symbol = c[1].to_uppercase();
        let amount = c[2].replace(',', "");
        let magnitude = c.get(3).map(|m| m.as_str()).unwrap_or("");
        let (unit_main, unit_sub) = match symbol.as_str() {
            "RM" | "MYR" => ("令吉", "仙"),
            "$" | "USD" => ("美元", "分"),
            "£" | "GBP" => ("英镑", "便士"),
            "€" | "EUR" => ("欧元", "分"),
            _ => ("元", "分"),
        };
        if let Some((w, f_raw)) = amount.split_once('.') {
            let mut f = f_raw.to_string();
            while f.len() < 2 {
                f.push('0');
            }
            let f = &f[..2];
            if f != "00" {
                return format!(
                    "{}{magnitude}{unit_main}{}{unit_sub}",
                    to_cardinal_zh(w.parse().unwrap_or(0)),
                    to_cardinal_zh(f.parse().unwrap_or(0))
                );
            }
            return format!("{}{magnitude}{unit_main}", to_cardinal_zh(w.parse().unwrap_or(0)));
        }
        format!("{}{magnitude}{unit_main}", to_cardinal_zh(amount.parse().unwrap_or(0)))
    });

    let t = RE_TIME_NO_MERIDIAN.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        let (h, m): (u32, u32) = (c[1].parse().unwrap_or(0), c[2].parse().unwrap_or(0));
        if h == 0 && m == 0 {
            return "凌晨十二点".to_string();
        }
        if h == 12 && m == 0 {
            return "中午十二点".to_string();
        }
        if m == 0 {
            format!("{}点", to_cardinal_zh(h as u128))
        } else {
            format!("{}点{}分", to_cardinal_zh(h as u128), to_cardinal_zh(m as u128))
        }
    });
    let t = RE_TIME.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        let h: u32 = c[1].parse().unwrap_or(0);
        let m: u32 = c[2].parse().unwrap_or(0);
        let mer = c[3].to_lowercase();
        let word = if mer.starts_with('a') { "上午" } else { "下午" };
        if m == 0 {
            format!("{word}{}点", to_cardinal_zh(h as u128))
        } else {
            format!("{word}{}点{}分", to_cardinal_zh(h as u128), to_cardinal_zh(m as u128))
        }
    });
    let t = RE_TIME_ZH.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        let h: u32 = c[2].parse().unwrap_or(0);
        let m: u32 = c[3].parse().unwrap_or(0);
        if m == 0 {
            format!("{}{}点", &c[1], to_cardinal_zh(h as u128))
        } else {
            format!("{}{}点{}分", &c[1], to_cardinal_zh(h as u128), to_cardinal_zh(m as u128))
        }
    });
    let t = RE_TIME_SHORTFORM.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        let h: u32 = c[1].parse().unwrap_or(0);
        let word = if c[2].to_lowercase().starts_with('a') { "上午" } else { "下午" };
        format!("{word}{}点", to_cardinal_zh(h as u128))
    });

    let t = RE_COMMA_NUM.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        let num = c[0].replace(',', "");
        if let Some((w, f)) = num.split_once('.') {
            let fw: String = f.chars().map(|d| to_cardinal_zh(d.to_digit(10).unwrap_or(0) as u128)).collect();
            format!("{}点{fw}", to_cardinal_zh(w.parse().unwrap_or(0)))
        } else {
            to_cardinal_zh(num.parse().unwrap_or(0))
        }
    });
    let t = RE_DECIMAL.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        let fw: String = c[2].chars().map(|d| to_cardinal_zh(d.to_digit(10).unwrap_or(0) as u128)).collect();
        format!("{}点{fw}", to_cardinal_zh(c[1].parse().unwrap_or(0)))
    });
    let t = RE_DASHED_DIGIT.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        c[1].chars().filter(|ch| ch.is_ascii_digit()).map(zh_digit).collect::<Vec<_>>().join(" ")
    });
    let t = RE_DASHED_ALNUM.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        c[1].chars().filter(|ch| *ch != '-').map(zh_digit).collect::<Vec<_>>().join(" ")
    });
    let t = RE_ALNUM.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        c[1].chars().map(zh_digit).collect::<Vec<_>>().join(" ")
    });
    let t = RE_NUMBER.replace_all(&t, |c: &fancy_regex::Captures<str>| {
        let s = c[0].to_string();
        let num: u128 = s.parse().unwrap_or(0);
        if s.len() == 4 && (1000..=2099).contains(&num) {
            to_year_zh(num)
        } else {
            to_cardinal_zh(num)
        }
    });
    RE_LEFTOVER_DOT
        .replace_all(&t, "点")
        .trim()
        .to_string()
}

#[cfg(test)]
mod tests {
    use super::{to_cardinal_zh, to_year_zh};

    #[test]
    fn zh_cardinals() {
        assert_eq!(to_cardinal_zh(0), "零");
        assert_eq!(to_cardinal_zh(3), "三");
        assert_eq!(to_cardinal_zh(10), "十");
        assert_eq!(to_cardinal_zh(15), "十五");
        assert_eq!(to_cardinal_zh(50), "五十");
        assert_eq!(to_cardinal_zh(101), "一百零一");
        assert_eq!(to_cardinal_zh(10001), "一万零一");
        assert_eq!(to_cardinal_zh(1234567), "一百二十三万四千五百六十七");
    }

    #[test]
    fn zh_years() {
        assert_eq!(to_year_zh(2025), "二零二五");
        assert_eq!(to_year_zh(1990), "一九九零");
    }
}
