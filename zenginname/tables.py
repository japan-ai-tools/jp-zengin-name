"""Tables for Japanese bank-transfer account names (全銀 / Zengin).

Sources (summarised, not copied):
- Allowed characters and the abbreviation table as published by a Japanese
  broker for withdrawal account names: https://www.gaitame.com/account/zengin.html
  (digits, A-Z, 46 katakana, dakuten/handakuten, 9 symbols, half-width space;
  "・" -> ".", "ー" -> "-"; abbreviations in parentheses: start "ｶ)", middle "(ｶ)", end "(ｶ").
- Rows that are blank in that table sit under a filled row (merged cells). We give
  them the abbreviation of the row above and mark them merged=True. Check with
  your bank if you rely on one of those rows.
"""

# (name in kanji, abbreviation in full-width katakana, group, merged)
ENTITIES = [
    ("株式会社", "カ", "法人", False),
    ("有限会社", "ユ", "法人", False),
    ("合名会社", "メ", "法人", False),
    ("合資会社", "シ", "法人", False),
    ("合同会社", "ド", "法人", False),
    ("医療法人社団", "イ", "法人", True),
    ("医療法人財団", "イ", "法人", True),
    ("社会医療法人", "イ", "法人", True),
    ("医療法人", "イ", "法人", False),
    ("一般財団法人", "ザイ", "法人", False),
    ("公益財団法人", "ザイ", "法人", True),
    ("一般社団法人", "シヤ", "法人", False),
    ("公益社団法人", "シヤ", "法人", True),
    ("宗教法人", "シユウ", "法人", False),
    ("学校法人", "ガク", "法人", False),
    ("社会福祉法人", "フク", "法人", False),
    ("更生保護法人", "ホゴ", "法人", False),
    ("相互会社", "ソ", "法人", False),
    ("特定非営利活動法人", "トクヒ", "法人", False),
    ("地方独立行政法人", "チドク", "法人", False),
    ("独立行政法人", "ドク", "法人", False),
    ("弁護士法人", "ベン", "法人", False),
    ("有限責任中間法人", "チユウ", "法人", False),
    ("無限責任中間法人", "チユウ", "法人", True),
    ("行政書士法人", "ギヨ", "法人", False),
    ("司法書士法人", "シホウ", "法人", False),
    ("税理士法人", "ゼイ", "法人", False),
    ("国立大学法人", "ダイ", "法人", False),
    ("公立大学法人", "ダイ", "法人", True),
    ("農事組合法人", "ノウ", "法人", False),
    ("管理組合法人", "カンリ", "法人", False),
    ("社会保険労務士法人", "ロウム", "法人", False),
    ("営業所", "エイ", "営業所", False),
    ("出張所", "シユツ", "営業所", False),
    ("国民健康保険団体連合会", "コクホレン", "事業", False),
    ("国家公務員共済組合連合会", "コクキヨウレン", "事業", False),
    ("経済農業協同組合連合会", "ケイザイレン", "事業", False),
    ("共済農業協同組合連合会", "キヨウサイレン", "事業", False),
    ("農業協同組合連合会", "ノウキヨウレン", "事業", False),
    ("漁業協同組合連合会", "ギヨレン", "事業", False),
    ("社会保険診療報酬支払基金", "シヤホ", "事業", False),
    ("食糧販売協同組合", "シヨクハンキヨウ", "事業", False),
    ("国民健康保険組合", "コクホ", "事業", False),
    ("健康保険組合", "ケンポ", "事業", False),
    ("海上火災保険", "カイジヨウ", "事業", False),
    ("火災海上保険", "カサイ", "事業", False),
    ("生命保険", "セイメイ", "事業", False),
    ("厚生年金基金", "コウネン", "事業", False),
    ("従業員組合", "ジユウクミ", "事業", False),
    ("労働組合", "ロウクミ", "事業", False),
    ("生活協同組合", "セイキヨウ", "事業", False),
    ("漁業協同組合", "ギヨキヨウ", "事業", False),
    ("有限責任事業組合", "ユウクミ", "事業", False),
    ("公共職業安定所", "シヨクアン", "事業", False),
    ("社会福祉協議会", "シヤキヨウ", "事業", False),
    ("特別養護老人ホーム", "トクヨウ", "事業", False),
    ("共済組合", "キヨウサイ", "事業", False),
    ("協同組合", "キヨウクミ", "事業", False),
    ("連合会", "レン", "事業", False),
]

# Spelled-out readings (after small kana are made large) -> kanji name in ENTITIES.
SPELLED = {
    "カブシキガイシヤ": "株式会社", "カブシキカイシヤ": "株式会社",
    "ユウゲンガイシヤ": "有限会社", "ユウゲンカイシヤ": "有限会社",
    "ゴウドウガイシヤ": "合同会社", "ゴウドウカイシヤ": "合同会社",
    "ゴウメイガイシヤ": "合名会社", "ゴウシガイシヤ": "合資会社",
    "イリヨウホウジン": "医療法人",
    "イツパンシヤダンホウジン": "一般社団法人", "イツパンザイダンホウジン": "一般財団法人",
    "コウエキシヤダンホウジン": "公益社団法人", "コウエキザイダンホウジン": "公益財団法人",
    "トクテイヒエイリカツドウホウジン": "特定非営利活動法人",
    "ガツコウホウジン": "学校法人", "シヤカイフクシホウジン": "社会福祉法人",
    "シユウキヨウホウジン": "宗教法人", "ゼイリシホウジン": "税理士法人",
    "ベンゴシホウジン": "弁護士法人",
}

# 46 katakana allowed (full-width form), plus dakuten/handakuten combos that exist.
BASE_KANA = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン"
SMALL_TO_LARGE = {"ァ": "ア", "ィ": "イ", "ゥ": "ウ", "ェ": "エ", "ォ": "オ", "ッ": "ツ", "ャ": "ヤ",
                  "ュ": "ユ", "ョ": "ヨ", "ヮ": "ワ", "ヵ": "カ", "ヶ": "ケ"}
OLD_KANA = {"ヰ": "イ", "ヱ": "エ"}

# Full-width katakana -> half-width katakana (JIS X 0201), voiced split into two chars.
_FW = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン"
_HW = "ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜｦﾝ"
TO_HALF = dict(zip(_FW, _HW))
_VOICED = "ガギグゲゴザジズゼゾダヂヅデドバビブベボ"
_VOICED_BASE = "カキクケコサシスセソタチツテトハヒフヘホ"
for v, b in zip(_VOICED, _VOICED_BASE):
    TO_HALF[v] = TO_HALF[b] + "ﾞ"
for v, b in zip("パピプペポ", "ハヒフヘホ"):
    TO_HALF[v] = TO_HALF[b] + "ﾟ"
TO_HALF["ヴ"] = "ｳﾞ"

# Allowed symbols in the full-width display form -> half-width form.
SYMBOLS = {"(": "(", ")": ")", ".": ".", ",": ",", "-": "-", "/": "/", "「": "｢", "」": "｣", "¥": "¥", " ": " "}
DASHES = "ー‐‑‒–—―−ｰ~〜"
DOTS = "・･"

HALF_ALLOWED = set(_HW) | set("ﾞﾟ") | set("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ") | set("().,-/｢｣¥ ")
