import json
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from zenginname import check_name, format_name, match_names  # noqa: E402
from zenginname.bench import load, naive, score  # noqa: E402
from zenginname.server import handle  # noqa: E402
from zenginname.tables import ENTITIES  # noqa: E402


def codes(r):
    return [m["code"] for m in r["errors"] + r["warnings"]]


class TestFormat(unittest.TestCase):
    def test_position_rule(self):
        self.assertEqual(format_name("株式会社 ガイタメドットコム")["zengin"], "ｶ)ｶﾞｲﾀﾒﾄﾞﾂﾄｺﾑ")
        self.assertEqual(format_name("ガイタメドットコム 株式会社")["zengin"], "ｶﾞｲﾀﾒﾄﾞﾂﾄｺﾑ(ｶ")
        self.assertEqual(format_name("ガイタメドットコム株式会社 オキナワシシャ")["zengin"], "ｶﾞｲﾀﾒﾄﾞﾂﾄｺﾑ(ｶ)ｵｷﾅﾜｼｼﾔ")

    def test_entity_positions_reported(self):
        r = format_name("サクラショウジ株式会社 トウキョウ営業所")
        self.assertEqual([(e["abbreviation"], e["position"]) for e in r["entities"]], [("カ", "middle"), ("エイ", "end")])

    def test_spelled_entity(self):
        self.assertEqual(format_name("かぶしきがいしゃ にっぽんしょうじ")["zengin"], "ｶ)ﾆﾂﾎﾟﾝｼﾖｳｼﾞ")

    def test_small_kana_and_symbols(self):
        r = format_name("キャット・フード")
        self.assertEqual(r["zengin"], "ｷﾔﾂﾄ.ﾌ-ﾄﾞ")
        self.assertIn("small_kana_to_large", r["changes"])
        self.assertIn("middle_dot_to_period", r["changes"])

    def test_length_counts_dakuten(self):
        r = format_name("ガギグゲゴ", max_length=8)
        self.assertEqual(r["length"], 10)
        self.assertIn("W_TOO_LONG", codes(r))
        self.assertTrue(r["ok"])  # a warning, not an error

    def test_kanji_needs_reading(self):
        r = format_name("山田 タロウ")
        self.assertFalse(r["ok"])
        self.assertEqual(r["errors"][0]["code"], "E_KANJI_NEEDS_READING")
        self.assertEqual(r["errors"][0]["chars"], "山田")

    def test_char_not_allowed(self):
        r = format_name("A&B株式会社")
        self.assertIn("E_CHAR_NOT_ALLOWED", codes(r))

    def test_merged_row_warning(self):
        r = format_name("医療法人社団 サクラカイ")
        self.assertEqual(r["zengin"], "ｲ)ｻｸﾗｶｲ")
        self.assertIn("W_MERGED_ROW", codes(r))

    def test_already_formatted_is_stable(self):
        for s in ["ｶ)ﾃｽﾄ", "ﾃｽﾄ(ｶ", "ﾃｽﾄ(ｶ)ｵｵｻｶ"]:
            r = format_name(s)
            self.assertEqual(r["zengin"], s)
            self.assertEqual(codes(r), [])

    def test_empty(self):
        self.assertEqual(codes(format_name("  ")), ["E_EMPTY"])

    def test_every_entity_maps(self):
        for name, abbr, _, _ in ENTITIES:
            r = format_name(name + " テスト")
            self.assertTrue(r["zengin"].endswith(")ﾃｽﾄ"), name)


class TestCheck(unittest.TestCase):
    def test_ok(self):
        r = check_name("ｶ)ﾆﾂﾎﾟﾝ")
        self.assertTrue(r["ok"])
        self.assertEqual(r["abbreviations"], ["カ"])

    def test_small_kana(self):
        self.assertEqual(check_name("ｶ)ﾆｯﾎﾟﾝ")["errors"][0]["code"], "E_SMALL_KANA")

    def test_fullwidth(self):
        self.assertIn("E_CHAR_NOT_ALLOWED", codes(check_name("カ)ニツポン")))


class TestMatch(unittest.TestCase):
    def test_statement_vs_customer(self):
        r = match_names("ｶ)ｶﾞｲﾀﾒﾄﾞﾂﾄｺﾑ", "ガイタメドットコム株式会社")
        self.assertTrue(r["match"])

    def test_entity_type_differs(self):
        r = match_names("ﾕ)ﾔﾏﾀﾞｼﾖｳﾃﾝ", "株式会社 ヤマダショウテン")
        self.assertFalse(r["match"])
        self.assertTrue(r["name_match"])
        self.assertTrue(r["entity_type_differs"])

    def test_small_kana_ignored(self):
        self.assertTrue(match_names("ｷﾔﾂﾄﾌｰﾄﾞ", "キャットフード")["match"])

    def test_different(self):
        self.assertFalse(match_names("ﾔﾏﾀﾞ ﾀﾛｳ", "ヤマダ ハナコ")["match"])


class TestBench(unittest.TestCase):
    def test_cases(self):
        cases = load()
        self.assertEqual(len(cases), 30)
        ok, n = score(lambda t: format_name(t)["zengin"], cases)
        self.assertEqual(ok, n)
        self.assertLess(score(naive, cases)[0], n // 2)


class TestServer(unittest.TestCase):
    def call(self, name, args):
        return handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": args}})

    def test_list(self):
        r = handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        self.assertEqual([t["name"] for t in r["result"]["tools"]],
                         ["zengin_name_format", "zengin_name_check", "zengin_name_match"])

    def test_call(self):
        r = self.call("zengin_name_format", {"name": "合同会社 アオバ"})
        self.assertEqual(r["result"]["structuredContent"]["zengin"], "ﾄﾞ)ｱｵﾊﾞ")

    def test_bad_args(self):
        self.assertTrue(self.call("zengin_name_format", {"name": 3})["result"]["isError"])
        self.assertTrue(self.call("zengin_name_format", {"name": "ア", "max_length": -1})["result"]["isError"])

    def test_stdio(self):
        inp = "\n".join(json.dumps(m) for m in [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "zengin_name_check", "arguments": {"name": "ｶ)ﾃｽﾄ"}}}]) + "\n"
        out = subprocess.run([sys.executable, "-m", "zenginname.server"], input=inp, capture_output=True,
                             text=True, encoding="utf-8", cwd=ROOT, timeout=30).stdout.strip().splitlines()
        self.assertEqual(len(out), 2)
        self.assertEqual(json.loads(out[0])["result"]["serverInfo"]["name"], "jp-zengin-name")
        self.assertTrue(json.loads(out[1])["result"]["structuredContent"]["ok"])


if __name__ == "__main__":
    unittest.main()
