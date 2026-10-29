# JP Zengin Name

<!-- mcp-name: io.github.ayatrader/jp-zengin-name -->

**Format, check and compare Japanese bank-transfer account names (振込名義・口座名義カナ) the way Japanese banks accept them. MCP server, CLI and Python library. Standard library only, no network, MIT.**

A Japanese bank transfer carries the payee and payer name in a restricted set: half-width katakana, digits, A-Z, a few symbols and a half-width space. Small kana are written large, `ー` becomes `-`, `・` becomes `.`, and words like 株式会社 are replaced by an abbreviation whose parentheses depend on where the word sits: `ｶ)` at the start, `(ｶ)` in the middle, `(ｶ` at the end ([rules as published by one broker](https://www.gaitame.com/account/zengin.html)). Get one of these wrong and the transfer file is rejected. Accounting software reports it as 「振込依頼人名に使用できない文字が含まれています。」 ([example FAQ](https://biz.moneyforward.com/support/payable/faq/office/of02.html)).

A language model asked to "convert to half-width kana" usually keeps the small kana, writes 株式会社 out in full, and counts `ガ` as one character when the bank counts two (`ｶﾞ`).

```text
株式会社 ガイタメドットコム                 -> ｶ)ｶﾞｲﾀﾒﾄﾞﾂﾄｺﾑ
ガイタメドットコム株式会社 オキナワシシャ    -> ｶﾞｲﾀﾒﾄﾞﾂﾄｺﾑ(ｶ)ｵｷﾅﾜｼｼﾔ
かぶしきがいしゃ にっぽんしょうじ           -> ｶ)ﾆﾂﾎﾟﾝｼﾖｳｼﾞ
合同会社 ネクサス・ツールズ                 -> ﾄﾞ)ﾈｸｻｽ.ﾂ-ﾙｽﾞ
キャット・フード                           -> ｷﾔﾂﾄ.ﾌ-ﾄﾞ
山田 タロウ                                -> error E_KANJI_NEEDS_READING (chars: 山田)
```

What it does:

- maps 59 legal-entity, branch and business words (株式会社, 合同会社, 医療法人, 一般社団法人, 特定非営利活動法人, 営業所, 健康保険組合 ...) to the bank abbreviation with the start / middle / end rule, also when spelled out in kana (カブシキガイシャ)
- makes small kana large, converts hiragana, full-width letters and digits, `ー` `・` and full-width spaces
- returns the half-width form for the transfer file and a full-width form for display
- counts length the way the file does (a voiced kana is two characters) and warns above 30 (configurable)
- refuses kanji other than entity words and tells you which characters need a reading. It never guesses a reading
- compares a statement name with a customer name for reconciliation (入金消込), ignoring abbreviations, spaces, punctuation and width, and tells you when the entity type differs (`ﾕ)` vs 株式会社)

Every message comes in English and Japanese.

## MCP server (for AI agents)

```json
{"mcpServers": {"jp-zengin-name": {"command": "python", "args": ["-m", "zenginname.server"], "cwd": "/path/to/jp-zengin-name"}}}
```

| Tool | Input | Returns |
|---|---|---|
| `zengin_name_format` | `name` (kana reading), `max_length` | `ok`, `zengin`, `display`, `length`, `entities`, `changes`, `errors`, `warnings` |
| `zengin_name_check` | `name` (half-width), `max_length` | `ok`, `length`, `errors`, `warnings`, `abbreviations` |
| `zengin_name_match` | `a`, `b` | `match`, `name_match`, `key_a`, `key_b`, `entity_a`, `entity_b`, `entity_type_differs` |

All tools are read-only and offline.

## CLI and Python

```bash
python -m zenginname "株式会社 にっぽんしょうじ"     # JSON, exit 1 on error
python -m zenginname --file names.txt               # TSV: input, zengin, ok/NG, codes
python -m zenginname.bench                          # score on the 30 test cases
```

```python
from zenginname import format_name, check_name, match_names
format_name("ホシ 税理士法人")["zengin"]        # 'ﾎｼ(ｾﾞｲ'
check_name("ｶ)ﾆｯﾎﾟﾝ")["errors"][0]["code"]     # 'E_SMALL_KANA'
match_names("ｶ)ｻｸﾗ", "サクラ株式会社")["match"]  # True
```

## Test cases

`data/zengin_name_cases_v1.jsonl` has 30 inputs and expected outputs (entity positions, spelled entities, small kana, width, `ヴ`, old kana, split dakuten). This package scores 30/30. A naive converter (NFKC, hiragana to katakana, katakana to half-width) scores 2/30. The rules and the cases were written together, so 30/30 shows consistency with the published rules, not accuracy on real bank files. Corrections from people who send transfers are welcome as Issues.

## Codes

Errors: `E_EMPTY` `E_KANJI_NEEDS_READING` `E_CHAR_NOT_ALLOWED` `E_SMALL_KANA`. Warnings: `W_TOO_LONG` `W_MERGED_ROW` `W_ENTITY_ONLY` `W_PARENS` `W_SPACES`.

## Limits

- It does not read kanji. Pass the reading (the agent should ask the user or use the reading on file).
- Banks differ in details (maximum length, some symbols). Rows that are blank in the source table (医療法人社団, 公益財団法人, 公立大学法人 ...) use the abbreviation of the row above and return `W_MERGED_ROW`; confirm with your bank.
- It formats names only. It does not handle account numbers, bank codes or money.

---

## 日本語

振込名義(口座名義カナ)を、銀行の振込で通る形(全銀の半角カナ)に整える道具です。小さいカナを大きく、`ー`→`-`、`・`→`.`、株式会社などは位置で変わる略語(先頭 `ｶ)`・途中 `(ｶ)`・末尾 `(ｶ`)にします。濁点は1文字に数えて字数を確かめます。漢字の読みは推測しません(法人の種類の言葉だけ変換し、ほかの漢字は `E_KANJI_NEEDS_READING` で返します)。入金消込で、通帳の名義と取引先名が同じかも比べられます。標準ライブラリだけ・外部通信なし・MIT。
