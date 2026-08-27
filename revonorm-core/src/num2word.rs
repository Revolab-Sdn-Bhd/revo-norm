//! num2word — Malay/Indonesian number-to-words, ports of num2word_ms.py and
//! num2word_id.py. Same block-splitting and spelling rules; the two languages
//! differ only in vocabulary, captured in NumberVocab.

const MAX_NUM: u128 = 10_u128.pow(36);

/// The per-language number vocabulary.
pub struct NumberVocab {
    pub zero: &'static str,
    pub eight: &'static str,
    /// magnitude words indexed by power-of-1000 / 3 (3 => ribu, 6 => juta, ...)
    pub tens_to: &'static [(&'static str, u32)],
}

pub static MS_VOCAB: NumberVocab = NumberVocab {
    zero: "kosong",
    eight: "lapan",
    tens_to: &[
        ("ribu", 3), ("juta", 6), ("bilion", 9), ("trilion", 12),
        ("quadrillion", 15), ("quintillion", 18), ("sextillion", 21),
        ("septillion", 24), ("oktillion", 27), ("nonillion", 30),
        ("decillion", 33),
    ],
};

pub static ID_VOCAB: NumberVocab = NumberVocab {
    zero: "nol",
    eight: "delapan",
    tens_to: &[
        ("ribu", 3), ("juta", 6), ("miliar", 9), ("triliun", 12),
        ("kuadriliun", 15), ("kuintiliun", 18), ("sekstiliun", 21),
        ("septiliun", 24), ("oktiliun", 27), ("noniliun", 30),
        ("desiliun", 33),
    ],
};

fn vocab_digit(v: &NumberVocab, d: u8) -> Vec<&'static str> {
    match d {
        0 => vec![],
        1 => vec!["satu"],
        2 => vec!["dua"],
        3 => vec!["tiga"],
        4 => vec!["empat"],
        5 => vec!["lima"],
        6 => vec!["enam"],
        7 => vec!["tujuh"],
        8 => vec![v.eight],
        9 => vec!["sembilan"],
        _ => vec![],
    }
}

fn vocab_tens_to(v: &NumberVocab, pow: u32) -> Option<&'static str> {
    v.tens_to.iter().find(|(_, p)| *p == pow).map(|(w, _)| *w)
}

/// hundreds digit -> words ("seratus" for 1)
fn ratus(d: u8) -> Vec<&'static str> {
    match d {
        1 => vec!["seratus"],
        0 => vec![],
        d => {
            let mut v = vocab_digit(&MS_VOCAB, d); // digits 1-9 identical in both langs
            v.push("ratus");
            v
        }
    }
}

/// tens pair -> words (puluh/belas). python: 10 sepuluh, 11 sebelas,
/// 12+ = digit + "belas"; 20+ = digit + "puluh" + digit.
fn puluh(block: &str, vocab: &NumberVocab) -> Vec<&'static str> {
    let b = block.as_bytes();
    let d0 = b[0] - b'0';
    let d1 = b[1] - b'0';
    match (d0, d1) {
        (0, 0) => vec![],
        (0, _) => vocab_digit(vocab, d1),
        (1, 0) => vec!["sepuluh"],
        (1, 1) => vec!["sebelas"],
        (1, _) => {
            let mut v = vocab_digit(vocab, d1);
            v.push("belas");
            v
        }
        (_, 0) => {
            let mut words = vocab_digit(vocab, d0);
            words.push("puluh");
            words
        }
        (_, _) => {
            let mut words = vocab_digit(vocab, d0);
            words.push("puluh");
            words.extend(vocab_digit(vocab, d1));
            words
        }
    }
}

fn split_by_3(number: &str) -> Vec<&str> {
    // python: [number[max(0, i-3):i] for i in range(len(number), 0, -3)] reversed
    let mut blocks = Vec::new();
    let bytes = number.as_bytes();
    let mut i = bytes.len();
    while i > 0 {
        let start = i.saturating_sub(3);
        blocks.push(&number[start..i]);
        i = start;
    }
    blocks.reverse();
    blocks
}

fn spell_block(v: &NumberVocab, block: &str) -> Vec<&'static str> {
    if block.len() == 1 {
        let d = block.as_bytes()[0] - b'0';
        return if d == 0 { vec![v.zero] } else { vocab_digit(v, d) };
    }
    if block.len() == 2 {
        return puluh(block, v);
    }
    let b = block.as_bytes();
    // hundreds digit words are identical across ms/id (seratus, X ratus)
    let mut out = ratus(b[0] - b'0');
    // ...except the 8 inside "X ratus": patch lapan->delapan for id
    if v.eight == "delapan" {
        out = out.iter().map(|w| if *w == "lapan" { "delapan" } else { *w }).collect();
    }
    let mut tail = puluh(&block[1..3], v);
    if v.eight == "delapan" {
        tail = tail.iter().map(|w| if *w == "lapan" { "delapan" } else { *w }).collect();
    }
    out.extend(tail);
    out
}

/// Cardinal to words using the given vocabulary.
pub fn to_cardinal_with(n: u128, v: &NumberVocab) -> String {
    if n >= MAX_NUM {
        return "terlalu besar".to_string(); // python raises; we degrade gracefully
    }
    let digits = n.to_string();
    let blocks = split_by_3(&digits);
    let length = blocks.len() as u32;

    let mut words: Vec<&str> = Vec::new();
    let mut start = 0;
    // python join(): "seribu" replaces ["1","ribu"] only when the first block
    // is 1 AND there is exactly one more block (i.e. 1000..=1999).
    if length == 2 && blocks[0] == "1" {
        words.push("seribu");
        start = 1;
    }

    let mut i = start;
    while i < length {
        let spelled = spell_block(v, blocks[i as usize]);
        let empty = spelled.is_empty();
        words.extend(spelled);
        if empty {
            i += 1;
            continue;
        }
        if i == length - 1 {
            break;
        }
        if let Some(t) = vocab_tens_to(v, (length - 1 - i) * 3) {
            words.push(t);
        }
        i += 1;
    }
    if words.is_empty() {
        return v.zero.to_string();
    }
    words.join(" ")
}

/// Malay cardinal (ms vocabulary).
pub fn to_cardinal(n: u128) -> String {
    to_cardinal_with(n, &MS_VOCAB)
}

/// Indonesian cardinal (id vocabulary).
pub fn to_cardinal_id(n: u128) -> String {
    to_cardinal_with(n, &ID_VOCAB)
}

#[cfg(test)]
mod tests {
    use super::{to_cardinal, to_cardinal_id};

    #[test]
    fn basics() {
        assert_eq!(to_cardinal(0), "kosong");
        assert_eq!(to_cardinal(1), "satu");
        assert_eq!(to_cardinal(10), "sepuluh");
        assert_eq!(to_cardinal(11), "sebelas");
        assert_eq!(to_cardinal(15), "lima belas");
        assert_eq!(to_cardinal(20), "dua puluh");
        assert_eq!(to_cardinal(21), "dua puluh satu");
        assert_eq!(to_cardinal(100), "seratus");
        assert_eq!(to_cardinal(111), "seratus sebelas");
        assert_eq!(to_cardinal(1000), "seribu");
        assert_eq!(to_cardinal(1990), "seribu sembilan ratus sembilan puluh");
        assert_eq!(to_cardinal(2000), "dua ribu");
        assert_eq!(to_cardinal(5670), "lima ribu enam ratus tujuh puluh");
        assert_eq!(to_cardinal(10_000), "sepuluh ribu");
        assert_eq!(to_cardinal(1_000_000), "satu juta");
    }

    #[test]
    fn id_basics() {
        assert_eq!(to_cardinal_id(0), "nol");
        assert_eq!(to_cardinal_id(8), "delapan");
        assert_eq!(to_cardinal_id(100), "seratus");
        assert_eq!(to_cardinal_id(1000), "seribu");
        assert_eq!(to_cardinal_id(1_000_000), "satu juta");
        assert_eq!(to_cardinal_id(1_000_000_000), "satu miliar");
        assert_eq!(to_cardinal_id(21), "dua puluh satu");
        assert_eq!(to_cardinal_id(35), "tiga puluh lima");
    }
}
