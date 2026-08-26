//! num2word_ms — Malay number-to-words, a faithful port of
//! revo_norm/num2word_ms.py (same block-splitting and spelling rules).

const MAX_NUM: u128 = 10_u128.pow(36);

fn base(d: u8) -> Vec<&'static str> {
    match d {
        0 => vec![],
        1 => vec!["satu"],
        2 => vec!["dua"],
        3 => vec!["tiga"],
        4 => vec!["empat"],
        5 => vec!["lima"],
        6 => vec!["enam"],
        7 => vec!["tujuh"],
        8 => vec!["lapan"],
        9 => vec!["sembilan"],
        _ => vec![],
    }
}

fn tens_to(pow: u32) -> Option<&'static str> {
    match pow {
        3 => Some("ribu"),
        6 => Some("juta"),
        9 => Some("bilion"),
        12 => Some("trilion"),
        15 => Some("quadrillion"),
        18 => Some("quintillion"),
        21 => Some("sextillion"),
        24 => Some("septillion"),
        27 => Some("oktillion"),
        30 => Some("nonillion"),
        33 => Some("decillion"),
        _ => None,
    }
}

/// hundreds digit -> words ("seratus" for 1)
fn ratus(d: u8) -> Vec<&'static str> {
    match d {
        1 => vec!["seratus"],
        0 => vec![],
        d => {
            let mut v = base(d);
            v.push("ratus");
            v
        }
    }
}

/// two-digit string -> words (sepuluh/sebelas/belas/puluh forms)
fn puluh(two: &str) -> Vec<&'static str> {
    let b: Vec<u8> = two.bytes().map(|c| c - b'0').collect();
    match b[0] {
        1 => match b[1] {
            0 => vec!["sepuluh"],
            1 => vec!["sebelas"],
            x => {
                let mut v = base(x);
                v.push("belas");
                v
            }
        },
        0 => base(b[1]),
        x => {
            let mut v = base(x);
            v.push("puluh");
            v.extend(base(b[1]));
            v
        }
    }
}

/// Split digit string into <=3-char blocks, most significant first.
fn split_by_3(number: &str) -> Vec<&str> {
    let len = number.len();
    if len < 3 {
        return vec![number];
    }
    let first = len % 3;
    let mut blocks = Vec::new();
    if first > 0 {
        blocks.push(&number[..first]);
    }
    let mut i = first;
    while i < len {
        blocks.push(&number[i..i + 3]);
        i += 3;
    }
    blocks
}

/// Spell one block (up to 3 digits) -> words.
fn spell_block(block: &str) -> Vec<&'static str> {
    if block.len() == 1 {
        let d = block.as_bytes()[0] - b'0';
        return if d == 0 { vec!["kosong"] } else { base(d) };
    }
    if block.len() == 2 {
        return puluh(block);
    }
    let b = block.as_bytes();
    let mut v = ratus(b[0] - b'0');
    v.extend(puluh(&block[1..3]));
    v
}

/// Cardinal number (integer part as u128) to Malay words.
/// Mirrors to_cardinal() for ints; the normalizer only ever calls ints.
pub fn to_cardinal(n: u128) -> String {
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
        let spelled = spell_block(blocks[i as usize]);
        let empty = spelled.is_empty();
        words.extend(spelled);
        if empty {
            i += 1;
            continue;
        }
        if i == length - 1 {
            break;
        }
        if let Some(t) = tens_to((length - 1 - i) * 3) {
            words.push(t);
        }
        i += 1;
    }
    if words.is_empty() {
        return "kosong".to_string();
    }
    words.join(" ")
}

#[cfg(test)]
mod tests {
    use super::to_cardinal;

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
}
