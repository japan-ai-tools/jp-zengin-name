"""CLI: python -m zenginname "株式会社 ニッポンショウジ"   |   python -m zenginname --csv names.txt"""
import argparse
import json
import sys

from .name import DEFAULT_MAX, format_name


def main(argv=None):
    p = argparse.ArgumentParser(prog="zenginname", description="Format Japanese bank-transfer names (Zengin).")
    p.add_argument("name", nargs="?", help="name (kana reading); omit with --file")
    p.add_argument("--file", help="text file, one name per line (- for stdin); prints TSV: input, zengin, ok, codes")
    p.add_argument("--max-length", type=int, default=DEFAULT_MAX)
    a = p.parse_args(argv)
    for s in (sys.stdin, sys.stdout):
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8")
    if a.file:
        f = sys.stdin if a.file == "-" else open(a.file, encoding="utf-8")
        bad = 0
        for line in f:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            r = format_name(line, a.max_length)
            bad += not r["ok"]
            codes = ",".join(m["code"] for m in r["errors"] + r["warnings"])
            print(f"{line}\t{r['zengin']}\t{'ok' if r['ok'] else 'NG'}\t{codes}")
        return 1 if bad else 0
    if not a.name:
        p.error("give a name or --file")
    r = format_name(a.name, a.max_length)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
