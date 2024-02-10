"""
things to look into:
  - correlatives

https://object.pouta.csc.fi/OPUS-Tatoeba/v2023-04-12/moses/en-eo.txt.zip

"""

import string

SUBWORD_MARKER = "@"
TAG_SEP = "分"

d = {
    # 'nuntempe': [('nun', 'ROOT'), ('temp', 'ROOT'), ('e', 'ENDING')],
    # 'riprocxindajo':[('riprocx', 'ROOT'), ('ind', 'ROOT'), ('aj', 'ROOT'), ('o', 'ENDING')],
    # 'malpliigi':[('mal', 'AFFIX'), ('pli', 'ROOT'), ('ig', 'AFFIX'), ('i', 'ENDING')]
}

tagged_text = [("tom_", "ROOT"), ("hejm", "ROOT"), ("en", "ENDING")]

weird = set(string.digits + string.punctuation + "!',-.'?€" + "'" + "„”„”…₫‘’–—»«¨²")

# moses("hundo!") -> "hundo !"
# "hundo !".split() -> ["hundo", "!"]

# moses("what?!?") -> "what ? ! ?" or "what ?!?"

circumflex = {"ŭ": "ux", "ĉ": "cx", "ĝ": "gx", "ĥ": "hx", "ĵ": "jx", "ŝ": "sx"}

special_words = set(
    [
        "nenies",
        "ĉiel",
        "cxiel",
        "ĉies",
        "iel",
        "ĉiam",
        "kie",
        "kiu",
        "tiu",
        "iom",
        "cxiu",
        "nenio",
        "tiel",
        "cxio",
        "kiom",
        "nenie",
        "cxia",
        "tio",
        "ĉiom",
        "ial",
        "neniu",
        "tiam",
        "kia",
        "cxiom",
        "ie",
        "ĉia",
        "kiam",
        "cxie",
        "io",
        "kio",
        "tia",
        "kiel",
        "nenial",
        "tial",
        "ties",
        "e",
        "tie",
        "neniel",
        "ies",
        "neniom",
        "ĉie",
        "nenia",
        "iam",
        "ĉio",
        "kial",
        "tiom",
        "an",
        "cxial",
        "iu",
        "kies",
        "ia",
        "ĉial",
        "neniam",
        "ĉiu",
        "cxies",
        "cxiam",
        "desur",
        "depost",
        "disde",
    ]
)

to_root = set(
    [
        "onin",
        "ciis",
        "sxiis",
        "ŝiis",
        "cxuo",
        "ĉuo",
        "oli",
        "liu",
        "cin",
        "mio",
        "cia",
        "trea",
        "gxio",
        "ĝio",
        "cio",
        "cin",
        "tree",
        "onio",
    ]
)

pronouns_and_stuff = set(
    [
        a + b
        for a in ["mi", "vi", "li", "sxi", "gxi", "ni", "ili", "ĝi", "ŝi", "si"]
        for b in ["", "n", "a", "an", "j", "aj", "ajn"]
    ]
)

special_words = special_words | pronouns_and_stuff

make_root = set(
    [
        ("AFFIX", "AFFIX", "ROOT"),
        ("SPECIAL", "SPECIAL"),
        ("SPECIAL", "SPECIAL", "ENDING"),
        ("AFFIX", "ROOT"),
        ("ROOT", "AFFIX"),
    ]
)

SPECIAL = set(
    [
        "expression",
        "pronoun",
        "expression",
        "adverb",
        "article",
        "conjunction",
        "preposition",
    ]
)
AFFIX = set(["prefix", "suffix"])
ENDING = set(["ending"])


def recover_surface_text(tagged_text, words):
    """
    take a sequence of tagged text and recover the original
    """
    s = ""
    for i in range(len(tagged_text)):
        text = tagged_text[i][0]
        tag = tagged_text[i][1]
        if text in weird:
            s = s.strip()
            s += " " + text + " "
        elif tag == "ROOT" and text[-1] == SUBWORD_MARKER:
            s += text[:-1] + " "
        elif tag in ("AFFIX", "ROOT"):
            s += text
        elif tag == "SPECIAL":
            if i != len(tagged_text) - 1 and tagged_text[i + 1][1] == "ENDING":
                s += text
            elif i != len(tagged_text) - 1 and (text + tagged_text[i + 1][0] in words):
                s += text
            else:
                s += text + " "
        else:
            s += text + " "
    return s.strip()


def convert_tag(tag):
    # input tag -> output tag
    for affix in AFFIX:
        if affix in tag or tag == "o":
            return "AFFIX"
    if "ending" in tag and tag != "midending":
        return "ENDING"
    elif tag in SPECIAL or tag == "":
        return "SPECIAL"
    return "ROOT"


def convert_tags(tags):
    l = []
    for tag in tags:
        tag = tag.lower()
        converted = convert_tag(tag)
        if tag == "NUMBER" and len(tags) > 1:
            l.append("ROOT")
        if ("special" in converted or "ending" in tag) and len(l) < len(tags) - 1:
            l.append("ROOT")
        else:
            l.append(converted)
    return l


def get_dictionary_and_set(path="test.txt"):
    f = open(path, "r")
    words = set()
    for line in f:
        # print(line)
        l = line.strip().split(",")
        if len(l) == 4:
            word = ","
            seg = ""
            tag = ""
        else:
            word, seg, tags = l
            for let in circumflex:
                word = word.replace(let, circumflex[let])

        if seg == "":
            seg = word

        if word in weird:
            tags = "ROOT"
        elif TAG_SEP not in seg:
            tags = "ENDING"

        words.add(word)

        seg, tags = wordsegtonew(seg, tags)

        if word in d:
            d[word] = d[word]
        else:
            d[word] = list(zip(seg.split(TAG_SEP), convert_tags(tags.split(TAG_SEP))))

    return words, d


def convert_sentence(sentence, dictionary):
    out = []
    for w in sentence.split():
        for seg, tag in dictionary[w]:
            if w in string.punctuation:
                out.append((w, "ROOT"))
            else:
                out.append((seg, tag))
    return out


def wordsegtonew(seg, tags):
    if "".join(seg.split(TAG_SEP)) in to_root:
        return seg, ("ROOT",)

    if "SPECIAL" in tags and len(tags) > 1 and tags != ("SPECIAL", "ENDING"):
        tagscopy = list(tags)
        for i in range(len(tags)):
            if tagscopy[i] == "SPECIAL":
                tagscopy[i] = "ROOT"
        tags = tuple(tagscopy)

    if "ROOT" in tags and tags.count("ROOT") > 1:
        firstroot = tags.index("ROOT")
        lastroot = len(tags) - tags[::-1].index("ROOT")
        tags = tags[:firstroot] + tags[lastroot - 1 :]
        seg = seg.split(TAG_SEP)
        seg = TAG_SEP.join(
            seg[:firstroot] + ["".join(seg[firstroot:lastroot])] + seg[lastroot:]
        )

    if tags in make_root:
        tags = ("ROOT",)
        seg = "".join(seg.split(TAG_SEP))

    if seg.split(TAG_SEP)[-1] in [
        "i",
        "ia",
        "as",
        "os",
        "us",
        "u",
        "o",
        "a",
        "e",
        "on",
        "an",
        "en",
        "oj",
        "aj",
        "ojn",
        "ajn",
        "aŭ",
    ]:
        tagcopy = list(tags)
        tagcopy[-1] = "ENDING"
        tags = tuple(tagcopy)

    return seg, tags


def segmentation_pattern_counter(path="segs.txt"):
    d = {}

    f = open(path, "r")

    for line in f:
        if ",," not in line:
            surface, seg, tags = line.strip().split(",")

            if surface in special_words:
                tags = ("SPECIAL",)
            else:
                tags = tuple(convert_tags(tags.split(TAG_SEP)))

            seg, tags = wordsegtonew(seg, tags)

            if tags not in d:
                d[tags] = [1, set(((surface, seg),))]
            else:
                d[tags][0] += 1
                d[tags][1].add((surface, seg))

    f.close()
    return d


if __name__ == "__main__":
    # errors = 0

    # words, d = get_dictionary_and_set()

    # tagged_text = [("tom@", "ROOT"), ("vol", "ROOT"), ("is", "ENDING"),
    #                ("neni", "ROOT"), ("on", "ENDING"), ("krom", "SPECIAL"),
    #                ("ir", "ROOT"), ("i", "ENDING"), ("hejm", "ROOT"),
    #                ("en", "ENDING")]
    # raw_text = 'tom volis nenion krom iri hejmen'

    # assert (recovered := recover_surface_text(
    #     tagged_text,
    #     words)) == raw_text, f'text doesnt match: {recovered} | {raw_text}'

    # for line in open('segs.txt', 'r'):
    #   line = line.strip()
    #   for let in circumflex:
    #     line = line.replace(let, circumflex[let])
    #   converted = convert_sentence(line, d)
    #   recovered = recover_surface_text(converted, words)
    #   if recovered != line:
    #     errors += 1
    #     print(f"BAD: {line} | {recovered}")
    #     print(converted)
    #     print()
    # print(errors)
    seg_dict = segmentation_pattern_counter()

    for s in sorted(seg_dict, key=lambda s: seg_dict[s][0], reverse=True):
        print(s, seg_dict[s][0])

# dictionary: morpheme_tag_seq -> (count of the total number of times this appears, set of all (words/segmented_version) that have that segmentation pattern)

# (verb, verb_ending) -> (100, set((estas, (est, as)), ...))

# ('PrepPrefix_Noun_VerbSuffix_VerbEnding') = ellitiĝis, alluniĝos, enterigis
"""
>>> seg_dict[("ROOT",)]
[941, {('iu', 'iu'), 'tio', ('tio', 'tio'), ('kiel', 'kiel'), ('ie', 'ie'), ('kie', 'kie'), ('tia', 'tia'), ('ia', 'ia'), ('iel', 'iel'), ('neniu', 'neniu'), ('ĉio', 'cxio'), ('ties', 'ties'), ('kio', 'kio'), ('tiel', 'tiel'), ('ĉiu', 'cxiu'), ('kies', 'kies'), ('iom', 'iom'), ('ĉie', 'cxie'), ('io', 'io'), ('kiu', 'kiu'), ('kiam', 'kiam'), ('tiam', 'tiam'), ('ĉia', 'cxia'), ('tial', 'tial'), ('ĉies', 'cxies'), ('kial', 'kial'), ('kia', 'kia'), ('tiom', 'tiom'), ('neniel', 'neniel'), ('ĉiam', 'cxiam'), ('tie', 'tie'), ('iam', 'iam'), ('neniam', 'neniam'), ('kiom', 'kiom'), ('neniom', 'neniom'), ('tiu', 'tiu'), ('nenio', 'nenio'), ('an', 'an')}]


>>> seg_dict[("ROOT","ROOT", "AFFIX", "ROOT")]
[1, {'italalingve', 'ital_al_ing_ve'}]

>>> seg_dict[("SPECIAL", "SPECIAL")]
[9, {('naŭdek', 'naux_dek'), ('naŭcent', 'naux_cent'), ('kvindek', 'kvin_dek'), ('dudek', 'du_dek'), ('tridek', 'tri_dek')}]

>>> seg_dict[("ROOT", "ROOT", "ROOT")]
[2, {('itallingve', 'ital_lingv_e'), ('baldaŭmalbaldaŭ', 'baldaux_mal_baldaux')}]
"""
