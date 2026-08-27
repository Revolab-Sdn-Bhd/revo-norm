"""Generate parity fixtures for revonorm-core from the Python library.

Repo-relative: run from the repo root (`uv run python revonorm-core/tests/gen_fixtures.py`).
Ground truth is ALWAYS current Python main — regenerate after any rule change
and fix the Rust side until the suite is green.

Milestone 3 ported (adds shared features): currency suffixes, negative signs, entity extraction
(URL/EMAIL/PHONE/VERSION/CURRENCY/DATE/TIME) with stash protection,
pronunciation layers (builtin + user), the malay normalizer pass, entity
restore with spoken converters, pack symbol spelling, '!' drop. The fixture
generator simulates THAT EXACT subset in python and splits cases by whether
the full pipeline agrees:

  fixtures/pipeline_ms.txt  — full == sim: Rust must byte-match
  fixtures/pending_ms.txt   — full != sim (shared features: measurements,
      fractions, x-kali, hijri, hari-bulan, temperature): both outputs
      recorded, asserted in milestone 3
  fixtures/num2word_ms.txt  — num2word cardinals

Cases exercising options/pronunciation layers assert separately in
parity.rs (options_* tests) — fixtures use default options.
"""

import random
import re
from pathlib import Path

from revo_norm.currency_utils import (
    CURRENCY_B_SUFFIX_PATTERN,
    CURRENCY_JUTA_PATTERN,
    CURRENCY_K_SUFFIX_PATTERN,
    CURRENCY_M_SUFFIX_PATTERN,
    CURRENCY_MILIAR_PATTERN,
    CURRENCY_RIBU_PATTERN,
    CURRENCY_T_SUFFIX_PATTERN,
    CURRENCY_TRILIUN_PATTERN,
    expand_currency_b_suffix,
    expand_currency_k_suffix,
    expand_currency_m_suffix,
    expand_currency_t_suffix,
)
from revo_norm import normalize_text
from revo_norm.entity_extractor import EntityExtractor, EntityType
from revo_norm.langpack import get_pack
from revo_norm.normalizer_ms import normalize_malay
from revo_norm.num2word_ms import to_cardinal
from revo_norm.pronunciation_mappings import (
    apply_pronunciation_mappings,
    resolve_pronunciations,
)
from revo_norm.text_normalizer import _stash_placeholders, _unstash_placeholders

HERE = Path(__file__).parent
FIXDIR = HERE / "fixtures"

RE_NEG = re.compile(r"(?<![\w\-])-(?=\d)")


def simulate_milestone3(text: str) -> str:
    """Mirror revonorm-core's milestone-2 pipeline::normalize('ms') steps."""
    pack = get_pack("ms")
    out = text
    for pat, fn in [
        (CURRENCY_T_SUFFIX_PATTERN, expand_currency_t_suffix),
        (CURRENCY_TRILIUN_PATTERN, expand_currency_t_suffix),
        (CURRENCY_B_SUFFIX_PATTERN, expand_currency_b_suffix),
        (CURRENCY_MILIAR_PATTERN, expand_currency_b_suffix),
        (CURRENCY_M_SUFFIX_PATTERN, expand_currency_m_suffix),
        (CURRENCY_JUTA_PATTERN, expand_currency_m_suffix),
        (CURRENCY_K_SUFFIX_PATTERN, expand_currency_k_suffix),
        (CURRENCY_RIBU_PATTERN, expand_currency_k_suffix),
    ]:
        out = pat.sub(fn, out)
    out = RE_NEG.sub(f" {pack.negative_word} ", out)

    # measurements pass (milestone 3) — before extraction/normalizer
    from revo_norm.shared_features import normalize_measurements
    out = normalize_measurements(out, "ms")

    ex = EntityExtractor()
    # milestone-3 extraction set: milestone-2 types + shared-feature types
    ms3 = [EntityType.URL, EntityType.EMAIL, EntityType.PHONE,
           EntityType.VERSION, EntityType.CURRENCY, EntityType.DATE, EntityType.TIME,
           EntityType.TEMPERATURE, EntityType.FRACTION, EntityType.X_KALI,
           EntityType.IC, EntityType.HARI_BULAN, EntityType.HIJRI]
    out, ents = ex.extract(out, enabled_entities=ms3)

    table = resolve_pronunciations("ms", profile="builtin")
    out = apply_pronunciation_mappings(out, "ms", table)

    out, stash = _stash_placeholders(out)
    out = normalize_malay(out)
    out = _unstash_placeholders(out, stash)

    out = ex.restore(out, "ms")

    for sym, spoken in pack.symbol_words.items():
        out = out.replace(sym, f" {spoken} ")
    if pack.drops_exclamation:
        out = re.sub(r"!+", "", out)
    return re.sub(r"\s+", " ", out.strip())


ALL_CASES = [
    "Harga barang ni RM10.50 sahaja",
    "Baki akaun anda ialah RM5,670.23 pada 31 Disember",
    "RM30K",
    "Kos RM1.5M",
    "RM500 ribu",
    "Belanja RM2 juta",
    "RM2 bilion untung",
    "Jumlah 1,000,000 orang",
    "Nombor 03-8888 8000",
    "Bertemu pada 15/08/2025",
    "Mesyuarat jam 3:30 petang",
    "Jam 09:00 pagi",
    "Baca https://contoh.com/cari?q=halo",
    "Email ali@revo.ai ya",
    "versi 3.14.159",
    "Diskaun 50%",
    "Kenaikan 3.5%",
    "Suhu -5 darajat",
    "Kerugian -RM20,000",
    "Jam 3 petang",
    "Jumpa jam 7 malam",
    "John & Jane",
    "Important * note",
    "Pasti!",
    "Wow!!! Bagus",
    "Guna 5km dan 2kg",
    "Separuh daripada 3/4 bahagian",
    "10x ganda",
    "Suhu 25C hari ini",
    "1433H",
    "10HB setiap tahun",
    "Berat 10.5 kg",
    "Hubungi 012-345 6789 sekarang",
    "Lihat www.example.com/page/2/3",
    "Kos USD50 dan EUR30",
]


def main() -> None:
    FIXDIR.mkdir(exist_ok=True)
    rng = random.Random(42)

    nums = [0, 1, 2, 10, 11, 15, 20, 21, 99, 100, 101, 110, 200, 999, 1000, 1001,
            1500, 2000, 10_000, 100_000, 1_000_000, 1_500_000, 10**7, 10**9, 10**12]
    nums += [rng.randrange(1, 10_000_000) for _ in range(150)]
    with open(FIXDIR / "num2word_ms.txt", "w", encoding="utf-8") as f:
        for n in nums:
            f.write(f"{n}\t{to_cardinal(n)}\n")

    done, pending = [], []
    for case in ALL_CASES:
        full = normalize_text(case, language="ms")
        sim = simulate_milestone3(case)
        (done if full == sim else pending).append((case, full, sim))

    with open(FIXDIR / "pipeline_ms.txt", "w", encoding="utf-8") as f:
        for case, full, _ in done:
            f.write(f"{case}\t{full}\n")
    with open(FIXDIR / "pending_ms.txt", "w", encoding="utf-8") as f:
        for case, full, sim in pending:
            f.write(f"{case}\t{full}\t{sim}\n")

    print(
        f"wrote {len(nums)} num2word; pipeline parity: {len(done)} green-tier, "
        f"{len(pending)} pending (milestone 3 shared features): {[c for c, _, _ in pending]}"
    )


if __name__ == "__main__":
    main()
