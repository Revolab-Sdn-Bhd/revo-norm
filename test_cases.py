"""
Test cases extracted from test_en.py and test_ms.py.

Each case: (input_text, language, expected_list, optional_kwargs)

Expected strings are checked as OR groups:
  - Plain strings: at least ONE must appear in result
  - Strings prefixed with '!': must NOT appear in result

Run: python test_cases.py
"""

TEST_CASES_EN = [
    # Basic
    ("Hello, this is a test.", "en", ["Hello", "hello"]),

    # Numbers
    ("Born in 1990, graduated 2012", "en", ["nineteen ninety", "twenty twelve"]),
    ("1,000,000 dollars at 3.5%", "en", ["million"]),
    ("I have 2 apples and 3kg flour", "en", ["two", "three kilogram"]),

    # Currency
    ("The price is $45.99", "en", ["forty-five"]),
    ("Salary RM50K per year", "en", ["fifty thousand ringgit"]),
    ("RM10M investment deal", "en", ["ten million ringgit"]),
    ("RM5B budget approved", "en", ["five billion ringgit"]),
    ("National debt RM2T", "en", ["two trillion ringgit"]),
    ("Price $10.50", "en", ["ten"]),
    ("Sale $0.99", "en", ["ninety-nine cents"]),
    ("Price $1.50 only", "en", ["one dollar", "fifty cents"]),
    ("Budget RM1.5M", "en", ["million"]),
    ("Cost $2.3B", "en", ["billion"]),
    ("Loss of -$50", "en", ["fifty"]),
    ("Price RM50 and $100", "en", ["ringgit", "dollar"]),
    ("predict RM 450000", "en", ["!meter"]),
    ("Budget RM30K for www.example.com hosting", "en", ["thirty thousand"]),

    # Dates
    ("Meeting on 15/08/2025 at 3:30 pm", "en", ["august", "fifteen"]),
    ("On 1/1/2025", "en", ["one", "twenty"]),
    ("On 15 January 2025", "en", ["january", "fifteen"]),
    ("On 15 Jan 2025", "en", ["jan"]),
    ("On 01/15/2025", "en", ["fifteen"]),
    ("In 2025", "en", ["twenty"]),
    ("On 15/08/2025 we completed 3/4 of the work", "en", ["three over four"]),

    # Times
    ("Meet at 3:30 PM", "en", ["three thirty", "three"]),
    ("Meet at 3:30:45 PM", "en", ["three"]),
    ("I'll be there in 30min at 2.30pm", "en", ["thirty"]),

    # Temperature
    ("It's 25C outside", "en", ["celsius"]),
    ("It was 25C yesterday and 30C today", "en", ["celsius"]),
    ("Temperatures: 20C, 25C, and 30C", "en", ["celsius"]),
    ("25C outside", "en", ["!celsius"], {"disable": ["temperature"]}),
    ("Breaking: Temperature hits 40C as 5x more people gather 10km away", "en", ["forty celsius"]),

    # Measurements
    ("5km away", "en", ["five kilometer"]),
    ("2kg of rice", "en", ["two kilogram"]),
    ("5km away", "en", ["!kilometers"], {"disable": ["measurements"]}),

    # Fractions
    ("10/4 of the students", "en", ["ten over four"]),
    ("10/4 of students", "en", ["ten", "!ten over four"], {"disable": ["fractions"]}),
    ("Results: 3/4 samples showed 2x improvement at 25C", "en", ["three over four", "celsius"]),

    # X-kali
    ("10x faster", "en", ["ten times"]),
    ("10x faster", "en", ["!ten times"], {"disable": ["x_kali"]}),
    ("10x 10x 10x faster", "en", ["ten times"]),

    # Hijri
    ("Year 1433H", "en", ["Hijri"]),
    ("1433H", "en", ["one four three three"], {"disable": ["hijri"]}),
    ("In 2025 and 1433H", "en", ["Hijri", "twenty"]),

    # Abbreviations
    ("Speed: 100 km/h", "en", ["kilometers"]),
    ("In the heart of the forest", "en", ["!inch"], {"disable": ["abbreviations"]}),
    ("The API uses 5GB of RAM and processes at 100km/h speed.", "en", ["gigabyte", "kilometers"]),

    # IC numbers
    ("IC: 911111-01-1111", "en", ["nine one"]),
    ("Please provide IC: 911111-01-1111 and ID: PASS1234", "en", ["nine one"]),

    # Emails
    ("Contact user@example.com for details", "en", ["at", "dot"]),
    ("Email: user_name-test@example.co.uk", "en", ["at", "underscore"]),
    ("Email alice@example.com and bob@test.com for info", "en", ["at"]),

    # URLs
    ("Visit http://192.168.1.1:8080 for details", "en", ["one nine two"]),
    ("Download from ftp://example.com/file.zip", "en", ["example"]),
    ("Visit blog.example.com for more info", "en", ["blog", "dot"]),
    ("Visit example.com?param=value&id=123", "en", ["dot com"]),
    ("Go to example.com#section", "en", ["example"]),
    ("Visit www.example.com and blog.example.com", "en", ["dot"]),
    ("Visit example.com/page/2/3 for info", "en", ["dot"]),

    # Pronunciation overrides
    ("1Malaysia achieved success", "en", ["satu malaysia"]),
    ("The cut-off point is here", "en", ["kad off"]),
    ("See item No. 123 for details", "en", ["number"]),
    ("The year is 1988", "en", ["nineteen", "eighty"]),

    # Special chars
    ("John & Jane", "en", ["and", "!&"]),
    ("1 + 1 equals 2", "en", ["plus"]),
    ("Price @ $10 per item", "en", ["at"]),
    ("Use #hashtag for trending", "en", ["hash", "hashtag"]),
    ("Important * note", "en", ["important", "note"]),

    # Contractions
    ("I'm happy and you're welcome", "en", ["I am", "i am"]),

    # Complex text
    ("Install 50GB of data, requires 4GB RAM, and 2CPU cores", "en", ["fifty", "gigabyte"]),
    ("I'm veryyyy happyy! Budget RM30K, Temp 25C, Email user@example.com", "en", ["I am", "thirty thousand", "celsius"]),

    # Edge cases
    ("", "en", []),
    ("   ", "en", []),
    ("@#$%^&*()", "en", ["at"]),
    ("Héllo wörld", "en", ["héllo"]),
    ("Hello​world", "en", ["hello"]),
    ("Hello\tworld\nhow are you?", "en", ["how are you"]),
]

TEST_CASES_MS = [
    # Basic
    ("Hai, ini adalah ujian.", "ms", ["Hai", "hai"]),

    # Numbers
    ("Nilai adalah 0", "ms", ["kosong"]),
    ("Saya ada 5 ekor kucing", "ms", ["lima"]),
    ("Jumlahnya 1,000,000", "ms", ["satu juta"]),
    ("Harga 3.14", "ms", ["tiga"]),
    ("Diskaun 50%", "ms", ["lima puluh peratus"]),
    ("Ada 115 orang", "ms", ["seratus lima belas"]),

    # Currency
    ("Harga RM10", "ms", ["sepuluh ringgit"]),
    ("Harga RM10.50", "ms", ["sepuluh", "ringgit"]),
    ("Gaji RM50K setahun", "ms", ["lima puluh ribu ringgit"]),
    ("Project RM1M itu besar", "ms", ["satu juta ringgit"]),
    ("Harga RM1.5M", "ms", ["satu juta lima ratus ribu ringgit"]),
    ("Peruntukan RM2B kerajaan", "ms", ["dua bilion ringgit"]),
    ("GDP RM1T", "ms", ["satu trilion ringgit"]),
    ("Harga RM0.50 sahaja", "ms", ["lima puluh sen"]),
    ("Diskaun RM0.99", "ms", ["sembilan puluh sembilan sen"]),
    ("Bayar RM0.05", "ms", ["lima sen"]),
    ("Hanya RM0.01", "ms", ["satu sen"]),
    ("Harga RM1.50", "ms", ["satu ringgit", "lima puluh sen"]),
    ("predict RM 450000", "ms", ["!meter"]),
    ("Contohnya, rumah seribu dua ratus persegi kaki predict RM 450000", "ms", ["!meter"]),

    # Dates
    ("Tarikh: 15/08/2025", "ms", ["lima belas", "Ogos", "dua ribu"]),
    ("2025-08-15", "ms", ["lima belas", "Ogos"]),
    ("Tarikh 2025-08-15 adalah penting", "ms", ["lima belas", "Ogos"]),
    ("15/08/2025", "ms", ["lima belas", "Ogos"]),
    ("2025/08/15", "ms", ["lima belas", "Ogos"]),
    ("2025.08.15", "ms", ["lima belas", "Ogos"]),
    ("2025-01-05", "ms", ["lima", "Januari"]),
    ("Bayar RM500 pada 2025-08-15", "ms", ["lima ratus ringgit", "Ogos"]),
    ("Dari 2025-01-01 hingga 2025-12-31", "ms", ["satu Januari", "tiga puluh satu Disember"]),
    ("Pada 15/08/2025 dan 2025-09-01", "ms", ["lima belas Ogos", "satu September"]),

    # Times
    ("Jumpa jam 9 malam", "ms", ["sembilan"]),
    ("Jumpa jam 5 petang", "ms", ["lima"]),

    # Temperature
    ("Suhu 25C", "ms", ["dua puluh lima celcius"]),

    # Measurements
    ("Berat 5kg, jarak 10km", "ms", ["kilometer"]),
    ("Server 5GB dan 100km/h speed", "ms", ["gigabyte", "kilometer"]),

    # Fractions
    ("10/4 daripada pelajar", "ms", ["sepuluh per empat"]),

    # X-kali
    ("10x lebih cepat", "ms", ["sepuluh kali"]),

    # Hari bulan
    ("10HB every year", "ms", ["sepuluh hari bulan"]),
    ("10HB every year", "ms", ["!sepuluh hari bulan"], {"disable": ["hari_bulan"]}),
    ("10HB is the date", "ms", ["sepuluh hari bulan", "!satu kosong hari bulan"]),
    ("There are 10 people and 10HB is the date", "ms", ["sepuluh hari bulan"]),
    ("In 1433H, Ramadan was on 10HB", "ms", ["Hijri", "hari bulan"]),

    # Hijri
    ("Suhu 25C dan perlu travel 5km. Tahun 1433H.", "ms", ["Hijri"]),

    # Elongated words
    ("saya betuii sangat celakaaa", "ms", ["betui", "celaka"]),

    # Emails
    ("Hubungi user@example.com untuk butiran", "ms", ["at", "dot"]),

    # Complex text
    ("Suhu 25C dan perlu travel 5km dalam 2 jam. Kos RM1.5M dan ambil 10x lebih usaha daripada 10/4 projek lepas.", "ms", ["celcius", "kilometer", "sepuluh kali", "sepuluh per empat"]),

    # Feature ordering
    ("Budget RM30K for www.example.com hosting", "ms", ["ribu", "dot"]),
    ("10HB is the date", "ms", ["sepuluh hari bulan", "!satu kosong hari bulan"]),
]


if __name__ == "__main__":
    from revo_norm import normalize_text

    failed = 0
    passed = 0

    for name, cases in [("EN", TEST_CASES_EN), ("MS", TEST_CASES_MS)]:
        for case in cases:
            text, lang, expected = case[0], case[1], case[2]
            kwargs = case[3] if len(case) > 3 else {}
            result = normalize_text(text, language=lang, **kwargs)
            result_lower = result.lower()

            if not text.strip():
                if result == "" or len(result.strip()) == 0:
                    passed += 1
                else:
                    failed += 1
                    print(f"FAIL [{name}] empty input got: {result!r}")
                continue

            ok = True
            for exp in expected:
                neg = exp.startswith("!")
                check = exp[1:] if neg else exp
                if neg:
                    if check.lower() in result_lower:
                        ok = False
                        print(f"FAIL [{name}] {text!r} → {result!r} (should NOT contain {check!r})")
                        break
                else:
                    if check.lower() not in result_lower:
                        ok = False
                        print(f"FAIL [{name}] {text!r} → {result!r} (expected {check!r})")
                        break

            if ok:
                passed += 1
            else:
                failed += 1

    print(f"\n{passed} passed, {failed} failed")
