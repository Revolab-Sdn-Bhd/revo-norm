"""Indonesian number-to-word conversion for TTS normalization."""

BASE = {
    0: [],
    1: ["satu"],
    2: ["dua"],
    3: ["tiga"],
    4: ["empat"],
    5: ["lima"],
    6: ["enam"],
    7: ["tujuh"],
    8: ["delapan"],
    9: ["sembilan"],
}

TENS_TO = {
    3: "ribu",
    6: "juta",
    9: "miliar",
    12: "triliun",
    15: "kuadriliun",
    18: "kuintiliun",
    21: "sekstiliun",
    24: "septiliun",
    27: "oktiliun",
    30: "noniliun",
    33: "desiliun",
}

max_num = 10**36


def split_by_koma(number):
    return str(number).split(".")


def ratus(number):
    if number == "1":
        return ["seratus"]
    elif number == "0":
        return []
    else:
        return BASE[int(number)] + ["ratus"]


def puluh(number):
    if number[0] == "1":
        if number[1] == "0":
            return ["sepuluh"]
        elif number[1] == "1":
            return ["sebelas"]
        else:
            return BASE[int(number[1])] + ["belas"]
    elif number[0] == "0":
        return BASE[int(number[1])]
    else:
        return BASE[int(number[0])] + ["puluh"] + BASE[int(number[1])]


def split_by_3(number):
    blocks = ()
    length = len(number)
    if length < 3:
        blocks += ((number,),)
    else:
        len_of_first_block = length % 3
        if len_of_first_block > 0:
            blocks += ((number[0:len_of_first_block],),)
        for i in range(len_of_first_block, length, 3):
            blocks += ((number[i : i + 3],),)
    return blocks


def spell(blocks):
    word_blocks = ()
    first_block = blocks[0]
    if len(first_block[0]) == 1:
        spelling = ["nol"] if first_block[0] == "0" else BASE[int(first_block[0])]
    elif len(first_block[0]) == 2:
        spelling = puluh(first_block[0])
    else:
        spelling = ratus(first_block[0][0]) + puluh(first_block[0][1:3])
    word_blocks += ((first_block[0], spelling),)
    for block in blocks[1:]:
        spelling = ratus(block[0][0]) + puluh(block[0][1:3])
        block += (spelling,)
        word_blocks += (block,)
    return word_blocks


def spell_float(float_part):
    word_list = []
    for n in float_part:
        if n == "0":
            word_list += ["nol"]
            continue
        word_list += BASE[int(n)]
    return " ".join(["", "koma"] + word_list)


def join(word_blocks, float_part):
    word_list = []
    length = len(word_blocks) - 1
    first_block = (word_blocks[0],)
    start = 0

    if length == 1 and first_block[0][0] == "1":
        word_list += ["seribu"]
        start = 1

    for i in range(start, length + 1, 1):
        word_list += word_blocks[i][1]
        if not word_blocks[i][1]:
            continue
        if i == length:
            break
        word_list += [TENS_TO[(length - i) * 3]]

    return " ".join(word_list) + float_part


def to_cardinal(number):
    if number >= max_num:
        raise OverflowError(f"Too large: {number} >= {max_num}")
    minus = ""
    if number < 0:
        minus = "negatif "
    float_word = ""
    n = split_by_koma(abs(number))
    if len(n) == 2:
        float_word = spell_float(n[1])
    return minus + join(spell(split_by_3(n[0])), float_word)
