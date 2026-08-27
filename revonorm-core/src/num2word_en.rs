//! num2word_en — English number-to-words matching inflect's number_to_words
//! default formatting: "one hundred and one", "two thousand, five hundred"
//! (comma+space between magnitude groups, "and" before final tens/units).

const ONES: [&str; 20] = [
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
    "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
    "sixteen", "seventeen", "eighteen", "nineteen",
];
const TENS: [&str; 10] = [
    "", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety",
];
const MAGNITUDES: [&str; 7] = [
    "", "thousand", "million", "billion", "trillion", "quadrillion", "quintillion",
];

/// 0..=999 -> words with inflect's "and" placement (nonzero hundreds +
/// nonzero remainder -> "X hundred and Y").
fn under_1000(n: u64) -> String {
    let mut parts: Vec<String> = Vec::new();
    let hundreds = n / 100;
    let rem = n % 100;
    if hundreds > 0 {
        parts.push(format!("{} hundred", ONES[hundreds as usize]));
    }
    if rem > 0 {
        let rem_words = if rem < 20 {
            ONES[rem as usize].to_string()
        } else {
            let t = TENS[(rem / 10) as usize];
            let o = rem % 10;
            if o == 0 { t.to_string() } else { format!("{t}-{}", ONES[o as usize]) }
        };
        if hundreds > 0 {
            parts.push(format!("and {rem_words}"));
        } else {
            parts.push(rem_words);
        }
    }
    parts.join(" ")
}

/// Cardinal with inflect default formatting: ", " between magnitude groups
/// when more than one group follows, "and" when only the last group remains
/// ("two thousand and five" vs "five thousand, six hundred and seventy").
pub fn to_cardinal_en(n: u128) -> String {
    if n == 0 {
        return "zero".to_string();
    }
    let mut groups: Vec<u64> = Vec::new();
    let mut rest = n;
    while rest > 0 {
        groups.push((rest % 1000) as u64);
        rest /= 1000;
    }
    // nonzero groups, most significant first
    let mut nz: Vec<(usize, u64)> = groups
        .iter()
        .enumerate()
        .filter(|(_, g)| **g > 0)
        .map(|(i, g)| (i, *g))
        .collect();
    nz.reverse();
    let mut out = String::new();
    let last = nz.len().saturating_sub(1);
    for (pos, (idx, g)) in nz.iter().enumerate() {
        let mag = MAGNITUDES[(*idx).min(MAGNITUDES.len() - 1)];
        let body = if mag.is_empty() {
            under_1000(*g)
        } else {
            format!("{} {mag}", under_1000(*g))
        };
        if pos == 0 {
            out.push_str(&body);
        } else if pos == last && *g < 100 && nz.len() > 1 {
            // inflect: final group under 100 joins with "and" not a comma
            out.push_str(&format!(" and {body}"));
        } else {
            out.push_str(&format!(", {body}"));
        }
    }
    out
}

/// Ordinal word for 1..=31 ("first", "second", ... "thirty-first").
pub fn ordinal_word(n: u64) -> String {
    const SPECIAL: [(&str, u64); 5] = [
        ("first", 1), ("second", 2), ("third", 3), ("fifth", 5), ("twelfth", 12),
    ];
    for (w, v) in SPECIAL {
        if n == v {
            return w.to_string();
        }
    }
    if n % 100 / 10 == 1 {
        // 10th-19th share "ieth": twentieth.. nineteenth handled by <20 above? no:
        // inflect: 20 -> twentieth
    }
    if n < 20 {
        return format!("{}th", ONES[n as usize]);
    }
    let tens = n / 10;
    let ones = n % 10;
    let base = if ones == 0 {
        // twenty -> twentieth
        let t = TENS[tens as usize];
        format!("{}ieth", &t[..t.len() - 1])
    } else {
        format!("{}-{}", TENS[tens as usize], ONES[ones as usize])
    };
    if ones == 0 {
        return base;
    }
    match ones {
        1 => format!("{}-first", TENS[tens as usize]),
        2 => format!("{}-second", TENS[tens as usize]),
        3 => format!("{}-third", TENS[tens as usize]),
        5 => format!("{}-fifth", TENS[tens as usize]),
        _ => format!("{}-{}th", TENS[tens as usize], ONES[ones as usize]),
    }
}

/// Digit word for URL/phone speech.
pub fn digit_word_en(ch: char) -> &'static str {
    match ch {
        '0' => "zero", '1' => "one", '2' => "two", '3' => "three", '4' => "four",
        '5' => "five", '6' => "six", '7' => "seven", '8' => "eight", '9' => "nine",
        _ => "",
    }
}

#[cfg(test)]
mod tests {
    use super::{ordinal_word, to_cardinal_en};

    #[test]
    fn inflect_format() {
        assert_eq!(to_cardinal_en(0), "zero");
        assert_eq!(to_cardinal_en(5), "five");
        assert_eq!(to_cardinal_en(15), "fifteen");
        assert_eq!(to_cardinal_en(21), "twenty-one");
        assert_eq!(to_cardinal_en(100), "one hundred");
        assert_eq!(to_cardinal_en(101), "one hundred and one");
        assert_eq!(to_cardinal_en(115), "one hundred and fifteen");
        assert_eq!(to_cardinal_en(2000), "two thousand");
        assert_eq!(to_cardinal_en(2005), "two thousand and five");
        assert_eq!(to_cardinal_en(5670), "five thousand, six hundred and seventy");
        assert_eq!(to_cardinal_en(1_000_000), "one million");
        assert_eq!(
            to_cardinal_en(1_234_567),
            "one million, two hundred and thirty-four thousand, five hundred and sixty-seven"
        );
    }

    #[test]
    fn ordinals() {
        assert_eq!(ordinal_word(1), "first");
        assert_eq!(ordinal_word(2), "second");
        assert_eq!(ordinal_word(3), "third");
        assert_eq!(ordinal_word(4), "fourth");
        assert_eq!(ordinal_word(5), "fifth");
        assert_eq!(ordinal_word(12), "twelfth");
        assert_eq!(ordinal_word(21), "twenty-first");
        assert_eq!(ordinal_word(20), "twentieth");
    }
}
