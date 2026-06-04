"""
Chinese number-to-words conversion for TTS.

Supports cardinal numbers from 0 to 10^16 (兆).
Handles special Chinese number conventions:
- 十 (10) standalone, 一十 (10 embedded in compound)
- 一百零一 (101)
- 一万零一 (10001) — 零 between groups with skipped digits
"""

_DIGITS = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九"]
_LARGE_UNITS = ["", "万", "亿", "兆"]


def to_currency(value: int | float, currency: str = "ringgit") -> str:
    return f"{value}{currency}"


def to_cardinal(number: int | float) -> str:
    """Convert a number to Chinese cardinal words."""
    if number < 0:
        return "负" + to_cardinal(abs(number))

    if isinstance(number, float):
        int_part = int(number)
        dec_part = str(number).split(".", 1)[1]
        int_words = to_cardinal(int_part)
        dec_words = "".join(_DIGITS[int(d)] for d in dec_part)
        return f"{int_words}点{dec_words}"

    n = int(number)

    if n == 0:
        return "零"

    return _convert_integer(n)


def _convert_integer(n: int) -> str:
    if n < 10:
        return _DIGITS[n]
    if n < 100:
        return _convert_tens(n, embedded=False)
    if n < 1000:
        return _convert_hundreds(n)
    if n < 10000:
        return _convert_thousands(n)
    return _convert_large(n)


def _convert_tens(n: int, embedded: bool = False) -> str:
    """Convert 10-99. embedded=True forces leading digit for 10-19."""
    tens = n // 10
    ones = n % 10
    if tens == 1 and not embedded:
        return "十" if ones == 0 else f"十{_DIGITS[ones]}"
    return f"{_DIGITS[tens]}十" if ones == 0 else f"{_DIGITS[tens]}十{_DIGITS[ones]}"


def _convert_hundreds(n: int) -> str:
    """Convert 100-999."""
    hundreds = n // 100
    remainder = n % 100
    result = f"{_DIGITS[hundreds]}百"
    if remainder == 0:
        return result
    if remainder < 10:
        return f"{result}零{_DIGITS[remainder]}"
    return f"{result}{_convert_tens(remainder, embedded=True)}"


def _convert_thousands(n: int) -> str:
    """Convert 1000-9999."""
    thousands = n // 1000
    remainder = n % 1000
    result = f"{_DIGITS[thousands]}千"
    if remainder == 0:
        return result
    if remainder < 100:
        mid = _convert_tens(remainder, embedded=True) if remainder >= 10 else _DIGITS[remainder]
        return f"{result}零{mid}"
    return f"{result}{_convert_hundreds(remainder)}"


def _convert_large(n: int) -> str:
    """Convert numbers >= 10000 using 万, 亿, 兆 grouping."""
    if n >= 10**16:
        raise OverflowError(f"Number {n} is too large (max 10^16)")

    groups: list[tuple[int, int]] = []
    unit_idx = 0
    temp = n
    while temp > 0:
        group = temp % 10000
        groups.append((group, unit_idx))
        temp //= 10000
        unit_idx += 1

    result = ""
    for i in range(len(groups) - 1, -1, -1):
        group_val, unit_idx = groups[i]
        if group_val == 0:
            continue
        group_str = _convert_group_of_4(group_val, leading=not result)
        unit = _LARGE_UNITS[unit_idx]
        if result and group_val < 1000:
            result += "零"
        result += f"{group_str}{unit}"

    return result


def _convert_group_of_4(n: int, leading: bool = False) -> str:
    """Convert a 1-4 digit number within a larger number."""
    if n < 10:
        return _DIGITS[n]
    if n < 100:
        return _convert_tens(n, embedded=not leading)
    if n < 1000:
        return _convert_hundreds(n)
    return _convert_thousands(n)


def to_year(year: int) -> str:
    """Convert a year to Chinese spoken form (digit by digit)."""
    return "".join(_DIGITS[int(d)] for d in str(abs(year)))

