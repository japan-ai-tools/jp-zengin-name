"""Format, check and compare Japanese bank-transfer account names (振込名義・口座名義カナ).

Standard library only. No network. Does not read kanji: give the reading in kana,
except for legal-entity words (株式会社, 合同会社, 医療法人 ...), which are mapped
to the bank abbreviations (ｶ) / (ｶ) / (ｶ).
"""
import re
import unicodedata

from .tables import (BASE_KANA, DASHES, DOTS, ENTITIES, HALF_ALLOWED, OLD_KANA, SMALL_TO_LARGE,
                     SPELLED, SYMBOLS, TO_HALF)

DEFAULT_MAX = 30
_ENTITY_BY_NAME = {e[0]: e for e in ENTITIES}
_ABBRS = sorted({e[1] for e in ENTITIES}, key=len, reverse=True)
_ABBR_HALF = {a: "".join(TO_HALF.get(c, c) for c in a) for a in _ABBRS}
# longest first so 医療法人社団 wins over 医療法人
_PATTERNS = sorted([(e[0].replace("ー", "-"), e[0]) for e in ENTITIES] + [(k, v) for k, v in SPELLED.items()],
                   key=lambda kv: len(kv[0]), reverse=True)
_ALLOWED_FULL = set(BASE_KANA) | set("ガギグゲゴザジズゼゾダヂヅデドバビブベボパピプペポヴ") | \
    set("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ") | set(SYMBOLS)


def _msg(level, code, message, message_ja, **extra):
    d = {"level": level, "code": code, "message": message, "message_ja": message_ja}
    d.update(extra)
    return d


def _is_kanji(ch):
    return "CJK" in unicodedata.name(ch, "")


def _prepare(text, changes):
    """NFKC, hiragana->katakana, small->large kana, upper-case, dashes/dots."""
    s = unicodedata.normalize("NFKC", text.replace("\u309b", "\u3099").replace("\u309c", "\u309a"))
    if s != text:
        changes.append("nfkc")
    out = []
    for ch in s:
        o = ch
        if "ぁ" <= ch <= "ゖ":
            o = chr(ord(ch) + 0x60)
            if "hiragana_to_katakana" not in changes:
                changes.append("hiragana_to_katakana")
        if o in SMALL_TO_LARGE:
            o = SMALL_TO_LARGE[o]
            if "small_kana_to_large" not in changes:
                changes.append("small_kana_to_large")
        elif o in OLD_KANA:
            o = OLD_KANA[o]
            if "old_kana" not in changes:
                changes.append("old_kana")
        elif o in DASHES:
            o = "-"
            if "long_vowel_to_hyphen" not in changes:
                changes.append("long_vowel_to_hyphen")
        elif o in DOTS:
            o = "."
            if "middle_dot_to_period" not in changes:
                changes.append("middle_dot_to_period")
        elif "a" <= o <= "z":
            o = o.upper()
            if "uppercase" not in changes:
                changes.append("uppercase")
        elif o in "　\t\n\r":
            o = " "
        out.append(o)
    return re.sub(r" +", " ", "".join(out)).strip()


def _split_entities(s):
    """Return list of parts: str or ('ENT', kanji_name)."""
    parts = [s]
    for pat, name in _PATTERNS:
        new = []
        for p in parts:
            if not isinstance(p, str) or pat not in p:
                new.append(p)
                continue
            chunks = p.split(pat)
            for i, c in enumerate(chunks):
                if i:
                    new.append(("ENT", name))
                new.append(c)
        parts = new
    return parts


def to_halfwidth(full):
    return "".join(TO_HALF.get(c, SYMBOLS.get(c, c)) for c in full)


def format_name(text, max_length=DEFAULT_MAX):
    """Turn a name (kana reading + optional legal-entity words) into a Zengin transfer name.

    Returns dict: ok, zengin (half-width), display (full-width), length, max_length,
    entities, changes, errors, warnings.
    """
    if not isinstance(text, str) or not text.strip():
        return {"ok": False, "zengin": "", "display": "", "length": 0, "max_length": max_length,
                "entities": [], "changes": [], "warnings": [],
                "errors": [_msg("error", "E_EMPTY", "Name is empty.", "名義が空です。")]}
    changes, errors, warnings = [], [], []
    s = _prepare(text, changes)
    parts = _split_entities(s)
    ents = [i for i, p in enumerate(parts) if isinstance(p, tuple)]
    entities, pieces = [], []
    for i, p in enumerate(parts):
        if isinstance(p, tuple):
            name = p[1]
            _, abbr, group, merged = _ENTITY_BY_NAME[name]
            before = "".join(x for x in parts[:i] if isinstance(x, str)).strip()
            after = "".join(x for x in parts[i + 1:] if isinstance(x, str)).strip()
            if not before and not after:
                pos, tok = "only", abbr
                warnings.append(_msg("warning", "W_ENTITY_ONLY", "Only a legal-entity word was given.",
                                     "法人の種類だけで、名前がありません。"))
            elif not before:
                pos, tok = "start", abbr + ")"
            elif not after:
                pos, tok = "end", "(" + abbr
            else:
                pos, tok = "middle", "(" + abbr + ")"
            entities.append({"word": name, "abbreviation": abbr, "position": pos, "group": group,
                             "from_merged_table_row": merged})
            if merged:
                warnings.append(_msg("warning", "W_MERGED_ROW",
                                     f"'{name}' uses the abbreviation of the row above in the source table (merged cell). Confirm with the bank.",
                                     f"「{name}」は元の表で空欄(結合セル)のため、上の行の略語を使いました。銀行に確かめてください。",
                                     word=name))
            pieces.append(("ENT", tok))
        else:
            pieces.append(p)
    # join: no spaces next to an abbreviation token
    buf = ""
    for i, p in enumerate(pieces):
        if isinstance(p, tuple):
            buf += p[1]
            continue
        if i > 0 and isinstance(pieces[i - 1], tuple):
            p = p.lstrip()
        if i + 1 < len(pieces) and isinstance(pieces[i + 1], tuple):
            p = p.rstrip()
        buf += p
    display = re.sub(r" +", " ", buf).strip()
    alts = "|".join(re.escape(a) for a in _ABBRS)
    tidy = re.sub(r"\s*\((%s)\)\s*" % alts, r"(\1)", display)
    tidy = re.sub(r"^(%s)\)\s*" % alts, r"\1)", tidy)
    tidy = re.sub(r"\s*\((%s)$" % alts, r"(\1", tidy)
    if tidy != display:
        changes.append("spaces_around_abbreviation")
        display = tidy
    stripped = re.sub(r"^(?:%s)\)|\((?:%s)\)|\((?:%s)$" % (alts, alts, alts), "", display)
    if entities:
        changes.append("legal_entity_abbreviation")
    kanji = sorted({c for c in display if _is_kanji(c)})
    if kanji:
        errors.append(_msg("error", "E_KANJI_NEEDS_READING",
                           "Kanji other than legal-entity words cannot be converted. Give the reading in kana.",
                           "法人の種類以外の漢字は読めません。読みをカナで渡してください。", chars="".join(kanji)))
    bad = sorted({c for c in display if c not in _ALLOWED_FULL and not _is_kanji(c)})
    if bad:
        errors.append(_msg("error", "E_CHAR_NOT_ALLOWED",
                           "Characters not allowed in a bank transfer name.",
                           "振込名義に使えない文字があります。", chars="".join(bad)))
    zengin = to_halfwidth(display)
    length = len(zengin)
    if max_length and length > max_length:
        warnings.append(_msg("warning", "W_TOO_LONG",
                             f"{length} half-width characters (voiced kana count as 2). Some banks reject names over {max_length}.",
                             f"半角{length}文字(濁点・半濁点は1文字に数える)。{max_length}文字を超えると振込できない場合があります。",
                             length=length))
    if stripped.count("(") != stripped.count(")"):
        warnings.append(_msg("warning", "W_PARENS", "Unbalanced parentheses.", "かっこの数が合いません。"))
    return {"ok": not errors, "zengin": zengin, "display": display, "length": length,
            "max_length": max_length, "entities": entities, "changes": changes,
            "errors": errors, "warnings": warnings}


def check_name(zengin, max_length=DEFAULT_MAX):
    """Check an already formatted half-width transfer name (e.g. from a CSV or a bank file)."""
    errors, warnings = [], []
    if not isinstance(zengin, str) or not zengin.strip():
        return {"ok": False, "length": 0, "errors": [_msg("error", "E_EMPTY", "Name is empty.", "名義が空です。")],
                "warnings": [], "abbreviations": []}
    bad = sorted({c for c in zengin if c not in HALF_ALLOWED})
    if bad:
        small = [c for c in bad if c in "ｧｨｩｪｫｯｬｭｮ"]
        if small:
            errors.append(_msg("error", "E_SMALL_KANA", "Small kana are not allowed; use the large form (ｯ -> ﾂ).",
                               "小さいカナは使えません。大きいカナにします(ｯ→ﾂ)。", chars="".join(small)))
        other = [c for c in bad if c not in small]
        if other:
            errors.append(_msg("error", "E_CHAR_NOT_ALLOWED",
                               "Characters outside the half-width Zengin set (full-width or other symbols).",
                               "全銀の半角の文字以外(全角や使えない記号)があります。", chars="".join(other)))
    if "  " in zengin or zengin != zengin.strip():
        warnings.append(_msg("warning", "W_SPACES", "Double or leading/trailing spaces.", "空白が重なっているか、前後に空白があります。"))
    found = []
    for a in _ABBRS:
        h = _ABBR_HALF[a]
        if zengin.startswith(h + ")") or ("(" + h + ")") in zengin or zengin.endswith("(" + h):
            found.append(a)
    if max_length and len(zengin) > max_length:
        warnings.append(_msg("warning", "W_TOO_LONG", f"{len(zengin)} characters, over {max_length}.",
                             f"{len(zengin)}文字で{max_length}文字を超えています。", length=len(zengin)))
    return {"ok": not errors, "length": len(zengin), "errors": errors, "warnings": warnings,
            "abbreviations": found}


_ABBR_RE = None


def match_key(text):
    """Key for reconciliation (入金消込): formatted, abbreviations and punctuation removed."""
    r = format_name(text, max_length=0)
    s = r["zengin"]
    # also accept already half-width input: normalise to full-width then back
    global _ABBR_RE
    if _ABBR_RE is None:
        alts = "|".join(re.escape(_ABBR_HALF[a]) for a in _ABBRS)
        _ABBR_RE = re.compile(r"^(?:%s)\)|\((?:%s)\)|\((?:%s)$" % (alts, alts, alts))
    prev = None
    while prev != s:
        prev = s
        s = _ABBR_RE.sub(" ", s).strip()
    key = re.sub(r"[ .,\-/()｢｣¥]", "", s)
    return key, r


def match_names(a, b):
    """Compare two names the way a payment reconciler would (ignores entity abbreviations,
    spaces, punctuation, small/large kana, full/half width)."""
    ka, ra = match_key(a)
    kb, rb = match_key(b)
    ea = [e["abbreviation"] for e in ra["entities"]]
    eb = [e["abbreviation"] for e in rb["entities"]]
    # also read abbreviations from already-formatted input
    ea = ea or check_name(ra["zengin"], 0)["abbreviations"]
    eb = eb or check_name(rb["zengin"], 0)["abbreviations"]
    errors = ra["errors"] + rb["errors"]
    differs = bool(ea and eb and set(ea) != set(eb))
    same = bool(ka) and ka == kb and not errors
    return {"match": same and not differs, "name_match": same, "key_a": ka, "key_b": kb,
            "entity_a": ea, "entity_b": eb,
            "entity_type_differs": differs, "errors": errors}
