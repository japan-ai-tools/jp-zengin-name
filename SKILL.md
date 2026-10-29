---
name: jp-zengin-name
description: Use when writing or checking Japanese bank-transfer names (振込名義, 口座名義カナ, 総合振込・給与振込のCSV, 入金消込). Formats names to the Zengin half-width kana form with legal-entity abbreviations, instead of converting by hand.
---

# Japanese bank-transfer names

1. Get the kana reading of each name from the user or the record. Do not guess readings of kanji.
2. Run `python -m zenginname "<reading with 株式会社 etc. as written>"` (or the MCP tool `zengin_name_format`).
3. Use the `zengin` field in the transfer file. If `ok` is false, show the errors (`E_KANJI_NEEDS_READING` lists the characters that need a reading) and ask.
4. For reconciliation, compare the statement name and the customer name with `zengin_name_match`. Treat `entity_type_differs` as "check by hand".
