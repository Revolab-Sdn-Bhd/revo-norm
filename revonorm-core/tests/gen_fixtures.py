"""Generate parity fixtures for revonorm-core from the Python library.

Repo-relative: run from the repo root (`uv run python revonorm-core/tests/gen_fixtures.py`).
Ground truth is ALWAYS current Python main — regenerate after any rule change
and fix the Rust side until the suite is green.

Milestone 1 implements a subset of the full python pipeline (currency
suffixes, negative signs, the malay normalizer pass, pack symbol words,
'!' drop). This generator SIMULATES that exact step subset in python and
classifies every case by whether the full pipeline agrees:

  fixtures/pipeline_ms.txt  — full == milestone-1 sim: Rust must byte-match
  fixtures/pending_ms.txt   — full != sim (entity extractor / shared features
      not ported yet): both outputs recorded, asserted in later milestones
  fixtures/num2word_ms.txt  — num2word cardinals (tier-independent)

When a milestone ports more steps, extend simulate_milestone1() to match the
Rust pipeline; cases migrate from pending to pipeline automatically.
"""

import random
import re
from pathlib import Path

from revo_norm import normalize_text
from revo_norm.langpack import get_pack
from revo_norm.normalizer_ms import normalize_malay
from revo_norm.num2word_ms import to_cardinal

HERE = Path(__file__).parent
FIXDIR = HERE / "fixtures"

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
    "Diskaun 50%",
    "Kenaikan 3.5%",
    "Berat 10.5 kg",
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
]

RE_NEG = re.compile(r"(?<![\w\-])-(?=\d)")


def simulate_milestone1(text: str) -> str:
    """Mirror revonorm-core's pipeline::normalize 'ms' steps exactly."""
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

    pack = get_pack("ms")
    out = text
    out = CURRENCY_T_SUFFIX_PATTERN.sub(expand_currency_t_suffix, out)
    out = CURRENCY_TRILIUN_PATTERN.sub(expand_currency_t_suffix, out)
    out = CURRENCY_B_SUFFIX_PATTERN.sub(expand_currency_b_suffix, out)
    out = CURRENCY_MILIAR_PATTERN.sub(expand_currency_b_suffix, out)
    out = CURRENCY_M_SUFFIX_PATTERN.sub(expand_currency_m_suffix, out)
    out = CURRENCY_JUTA_PATTERN.sub(expand_currency_m_suffix, out)
    out = CURRENCY_K_SUFFIX_PATTERN.sub(expand_currency_k_suffix, out)
    out = CURRENCY_RIBU_PATTERN.sub(expand_currency_k_suffix, out)
    out = RE_NEG.sub(f" {pack.negative_word} ", out)
    out = normalize_malay(out)
    for sym, spoken in pack.symbol_words.items():
        out = out.replace(sym, f" {spoken} ")
    if pack.drops_exclamation:
        out = re.sub(r"!+", "", out)
    return re.sub(r"\s+", " ", out.strip())


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
        sim = simulate_milestone1(case)
        (done if full == sim else pending).append((case, full, sim))

    with open(FIXDIR / "pipeline_ms.txt", "w", encoding="utf-8") as f:
        for case, full, _ in done:
            f.write(f"{case}\t{full}\n")
    # pending: input \t full \t milestone1-sim, for the next milestones
    with open(FIXDIR / "pending_ms.txt", "w", encoding="utf-8") as f:
        for case, full, sim in pending:
            f.write(f"{case}\t{full}\t{sim}\n")

    print(
        f"wrote {len(nums)} num2word; pipeline parity: {len(done)} green-tier, "
        f"{len(pending)} pending (unported steps): {[c for c, _, _ in pending]}"
    )


if __name__ == "__main__":
    main()
