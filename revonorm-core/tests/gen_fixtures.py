"""Snapshot fixtures for revonorm-core, generated from the engine itself.

Post-SSOT-flip the rust engine IS the source of truth: fixtures record its
output per case so CI catches regressions on every PR. (The pre-flip
python-parity machinery — simulate_milestone*, tier splitting — retired with
the pure-python implementation.)

Run from the repo root: `uv run python revonorm-core/tests/gen_fixtures.py`
"""

import random
from pathlib import Path

from revonorm._core import normalize as engine_normalize
from revonorm._core import to_cardinal_ms

HERE = Path(__file__).parent
FIXDIR = HERE / "fixtures"

CASES = {
    "ms": [
        "Harga barang ni RM10.50 sahaja",
        "Baki akaun anda ialah RM5,670.23 pada 31 Disember",
        "RM30K", "Kos RM1.5M", "RM500 ribu", "Belanja RM2 juta",
        "RM2 bilion untung", "Jumlah 1,000,000 orang",
        "Nombor 03-8888 8000", "Bertemu pada 15/08/2025",
        "Mesyuarat jam 3:30 petang", "Jam 09:00 pagi",
        "Baca https://contoh.com/cari?q=halo", "Email ali@revo.ai ya",
        "versi 3.14.159", "Diskaun 50%", "Kenaikan 3.5%",
        "Suhu -5 darajat", "Kerugian -RM20,000", "Jam 3 petang",
        "Jumpa jam 7 malam", "John & Jane", "Important * note",
        "Pasti!", "Wow!!! Bagus", "Guna 5km dan 2kg",
        "Separuh daripada 3/4 bahagian", "10x ganda",
        "Suhu 25C hari ini", "1433H", "10HB setiap tahun",
        "Berat 10.5 kg", "Hubungi 012-345 6789 sekarang",
        "Lihat www.example.com/page/2/3", "Kos USD50 dan EUR30",
        "No. 12, Jalan SS2/72, Petaling Jaya",
        "betuiii sekali", "dial *120# now", "Exit 5 please",
        "test test test test done", "sambung WiFi now",
    ],
    "id": [
        "Harga Rp1.500.000 saja", "Saldo Rp5.670,23 hari ini",
        "Rp5rb dan 5jt", "Rp5M", "diskon 3,5 persen",
        "jam 3:30 sore", "suhu -5 derajat", "total 1.000.000 orang",
        "pakai 5km jalan kaki", "suhu 25C disini", "jam 8:00 malam",
        "tanggal 15/08/2025", "15/4 dari penduduk", "10x lipat", "1433H",
        "pada 18/6/2025",
    ],
    "en": [
        "It costs $5.50", "Born in 1990", "3:30 pm meeting", "25C today",
        "I'm here don't know", "1st place 21st century",
        "RM2.5 million profit", "The API is fast", "50% off",
        "3.14 value", "call 03-8888 now", "meeting at 7 pm",
        "15/08/2025 deadline", "123,456 items", "you're 100% right",
        "The GUI uses JSON", "version 3.14.159", "No. 5 Jalan Bukit",
        "On 8/15/2025 we ship", "Visit www.revo.ai",
    ],
    "zh": [
        "价格是RM50", "温度25C", "百分之50", "现在3:30 pm",
        "共有1234567人", "上午9点开会", "2025年8月15日", "买3个",
        "3/4的人", "10x更快", "RM10.50打折", "共1,234,567件",
        "凌晨2:00出发", "10000块", "Email me at test@example.com",
        "2025-08-15开会", "10kg大米",
    ],
    "zh_my": [
        "价格是RM50", "温度25C", "买3个", "3/4的人", "2025年8月15日",
        "$100", "50%", "9:00 am",
    ],
}


def main() -> None:
    FIXDIR.mkdir(exist_ok=True)
    rng = random.Random(42)

    nums = [0, 1, 2, 10, 11, 15, 20, 21, 99, 100, 101, 110, 200, 999, 1000, 1001,
            1500, 2000, 10_000, 100_000, 1_000_000, 1_500_000, 10**7, 10**9, 10**12,
            8, 18, 28, 88, 108, 888]
    nums += [rng.randrange(1, 10_000_000) for _ in range(150)]
    with open(FIXDIR / "num2word_ms.txt", "w", encoding="utf-8") as f:
        for n in nums:
            f.write(f"{n}\t{to_cardinal_ms(n)}\n")

    total = 0
    for lang, cases in CASES.items():
        with open(FIXDIR / f"pipeline_{lang}.txt", "w", encoding="utf-8") as f:
            for case in cases:
                f.write(f"{case}\t{engine_normalize(case, lang, '')}\n")
                total += 1
        # profiles as separate matrices
        with open(FIXDIR / f"pipeline_{lang}_minimal.txt", "w", encoding="utf-8") as f:
            for case in cases:
                f.write(f"{case}\t{engine_normalize(case, lang, chr(123)+chr(34)+'profile'+chr(34)+':'+chr(34)+'minimal'+chr(34)+chr(125))}\n")
        with open(FIXDIR / f"pipeline_{lang}_basic.txt", "w", encoding="utf-8") as f:
            for case in cases:
                f.write(f"{case}\t{engine_normalize(case, lang, chr(123)+chr(34)+'profile'+chr(34)+':'+chr(34)+'basic'+chr(34)+chr(125))}\n")

    # retire pre-flip artifacts
    for stale in ("pending_ms.txt", "pending_id.txt", "pending_en.txt", "pending_zh.txt"):
        (FIXDIR / stale).unlink(missing_ok=True)

    print(f"snapshotted {total} pipeline cases x3 profiles + {len(nums)} num2word")


if __name__ == "__main__":
    main()
