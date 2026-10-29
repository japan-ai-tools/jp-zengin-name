"""Score a converter on data/zengin_name_cases_v1.jsonl.

python -m zenginname.bench            # this package vs a naive converter
The naive converter is what a quick script usually does: NFKC, hiragana->katakana,
katakana->half-width. No small-kana rule, no entity abbreviations.
"""
import json
import os
import sys
import unicodedata

from .name import format_name
from .tables import TO_HALF

CASES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "zengin_name_cases_v1.jsonl")
_SMALL_HALF = dict(zip("ァィゥェォッャュョ", "ｧｨｩｪｫｯｬｭｮ"))


def load(path=CASES):
    with open(path, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def naive(text):
    s = unicodedata.normalize("NFKC", text)
    s = "".join(chr(ord(c) + 0x60) if "ぁ" <= c <= "ゖ" else c for c in s)
    return "".join(TO_HALF.get(c, _SMALL_HALF.get(c, {"ー": "ｰ", "・": "･", "　": " "}.get(c, c))) for c in s)


def score(fn, cases=None):
    cases = cases or load()
    ok = sum(1 for c in cases if fn(c["input"]) == c["expected"])
    return ok, len(cases)


def main():
    for s in (sys.stdout,):
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8")
    a = score(lambda t: format_name(t)["zengin"])
    b = score(naive)
    print(json.dumps({"jp_zengin_name": f"{a[0]}/{a[1]}", "naive": f"{b[0]}/{b[1]}"}))


if __name__ == "__main__":
    main()
