import urllib.request
import os
import time

save_dir = os.path.join(os.path.dirname(__file__), 'images', 'characters')
os.makedirs(save_dir, exist_ok=True)

# キャラ名（日本語） → (保存ファイル名, DriveファイルID)
chars = [
    ("Eleven",        "Eleven",     "18q-qX5-eA62zimMJe3dhG6rCGWFqjnhw"),
    ("アイザック",    "Isaac",      "19SN1tlPCPuGQDSWRKBn90C2xWub8Sv6n"),
    ("アイソル",      "Isol",       "1Cjbm02nIZvs-ak3wOROH3RRJ-_LEu9AM"),
    ("アディナ",      "Adina",      "1Z38PM1QAqFyoeo5GjMWWPd8s5G1bLd0_"),
    ("アデラ",        "Adela",      "1JSADIgEJ4HaNQ_KQVUu9JnVt1XKV2FbV"),
    ("アドリアナ",    "Adriana",    "1juIeTO4-_cyMN4n9A9yTvRs_t3BOkY45"),
    ("アビゲイル",    "Abigail",    "1bFxB9z8eTCIfe_JBvkfpJDerCOpAZmfV"),
    ("アヤ",          "Aya",        "1e8eNKVy4QrQ-jq5z-M7h35vzyK8l7MK6"),
    ("アルダ",        "Alda",       "1SGE-Ox7dNVEmPM6ZIqrhFNXJPbS8EGnu"),
    ("アレックス",    "Alex",       "1t0705PaKx82k7ZZ9r7BUy80BYatfplEM"),
    ("アロンソ",      "Alonso",     "1zQd8iaQfCEqZy2Znk50c_KWa1m4po1yj"),
    ("イアン",        "Jan",        "1u-A5EgemEQIqO8M8Qee4AisddxAuMf0_"),
    ("イレム",        "Irem",       "103arki36SKYDI5v87a0xQdNrdBplBuiR"),
    ("ヴァーニャ",    "Vanya",      "1o6PsOFQhwhxDd9k9dM8dlvOYw4UT8aBF"),
    ("ウィリアム",    "William",    "1cq2oj0ocACrfoYwGzXq1b5xlAL8M3MbG"),
    ("エイデン",      "Aiden",      "1KK4yi6uRidIhrZyFAc1nzSSd1U5PIlqo"),
    ("エヴァ",        "Eva",        "1GT37uB5wVaMEEkmY43abMSMqn8gKgNfz"),
    ("エキオン",      "Echion",     "1ypH8wtlU41518B11iEuUbawALNA4XsdL"),
    ("エステル",      "Estelle",    "1zWFxgU5XE8V0N4SrPfxXeVafpPGd1-FC"),
    ("エマ",          "Emma",       "1FXYeY0v454xfNsHopYdVqDkjyDj4iJYE"),
    ("エレナ",        "Elena",      "19GIUCCs_p7u-SiTTLs-Uq2mTxZWDVoLm"),
    ("ガーネット",    "Garnet",     "1OZj-HsgAob-Fr1eJC2ztJXTOHx04LN9Z"),
    ("カーラ",        "Karla",      "1zPJquEOp_c95QgKJdCre_L1i46GGUgWs"),
    ("カティア",      "Katja",      "1AhO-twkZV1g_kcf3v_LDfReiyngDgyFI"),
    ("カミロ",        "Camilo",     "1SbjdzCMLCTde5kvrpdWvcURdw_D7F8kP"),
    ("キアラ",        "Chiara",     "1N-mxf3plg-443Zk_pSilc1IeKlcVhtjp"),
    ("キャッシー",    "Cathy",      "1shwLpgkiLU6juTSZoY0rO5NBlfo5P54j"),
    ("クロエ",        "Chloe",      "1ZRQeNMANF56ASC25rVP_pv3PDoNCsOJW"),
    ("ケネス",        "Kenneth",    "1BUs3qbOq-IjLctJdkOxgmZ1l3Kyx3LlB"),
    ("ザヒル",        "Zahir",      "1gx9GKihRXqQQTv7QEH2-NtC-QvmM0UEU"),
    ("シウカイ",      "Xiukai",     "1AabYQTXaaTMZfE4sYkEaIJxDocamEQ4A"),
    ("ジェニー",      "Jenny",      "1MMFfxzMQL2CEzTsRyx9y6woQ7vOXzmdX"),
    ("シセラ",        "Sissela",    "1RtthqiZwXpni8_MaabDs5JeJxDY-ZliH"),
    ("シャーロット",  "Charlotte",  "1I0epU_KADYHrshn2FgDZBE3OTXc_Xm4C"),
    ("ジャッキー",    "Jackie",     "1Dk0_ql9iIHJSr2iS36xSrM9J_r_mjoGF"),
    ("シルヴィア",    "Silvia",     "18ZXsfWUXjSlgsAdh-MEDh1HU9OKYNBXZ"),
    ("スア",          "Sua",        "1TDODfmpxrZOJHkLpCFW5yRo5CyXZGvs6"),
    ("セリーヌ",      "Celine",     "1s_AlxcFKjMZIzv4zUbBOvPdA6WppW8TS"),
    ("ダイリン",      "LiDailin",   "1A41fjTl-_Gm9lyLMqEmU0baLN4tv8n5S"),
    ("タジア",        "Tazia",      "163TRsNIeGfYhtmZ3ztsZyFw4zlDiClPp"),
    ("ダニエル",      "Daniel",     "19yRYf_xQnW_4LNdit8kACxE6rthOI9P8"),
    ("ダルコ",        "Darko",      "1lJ3egHi4mNy-Jhv_CI7xMl2HsIAOdGF1"),
    ("つばめ",        "Tsubame",    "1qmbRU_pamlbSK4_8nlFS8pynUxM-ivvr"),
    ("ティア",        "Tia",        "13rrgNv9yuN5KIcL9OVP9fzU9YSDND9IF"),
    ("テオドール",    "Theodore",   "1SScxO1PS6ErittbqSNeY07cl1xJtAMut"),
    ("デビー&マーリン","Debbie",    "1eDi5oLxMxnEJ3JGrKaYrV_f6TQMys4NU"),
    ("ナタポン",      "Nathapon",   "13gvJW0YVXzea4TSHLw7Bo2UIOZfyS1WG"),
    ("ナディン",      "Nadine",     "1dd39_qeeFcInjW-3mstWsxs3jbwYJHWV"),
    ("ニッキー",      "Nicky",      "1LUCo6euWcemreUXlpjQemNo6udJ7ZOVT"),
    ("ハート",        "Hart",       "1l3TINyC-6kIHHs0g3mMp7uzuybJPgMWo"),
    ("バーバラ",      "Barbara",    "1eaC3l28EZbTfvbNsgYoa83Nv8wmeR2Bz"),
    ("ビアンカ",      "Bianca",     "1lkMvRRzyqpWgDELh8wd1WoPKXLqj5LBC"),
    ("ピオロ",        "Piolo",      "1P3EhrOjIJFXLNmQzwphKcRGdqh5BI-yU"),
    ("ヒョヌ",        "Hyunwoo",    "1GeYsDPMiOLS0ff7PYkVjNDYP3ZomN4h-"),
    ("フィオラ",      "Fiora",      "1icy-uLPSSfmZBMydPyuaa2anaRmuFn9O"),
    ("プリヤ",        "Priya",      "1O65qPlPj9rT4gzdTAgV7p4YM5zGQw3mu"),
    ("ヘイズ",        "Haze",       "1KwLx-cc_iC1j5MCZl3edxB8nWrh9m2Hx"),
    ("ヘジン",        "Hyejin",     "17a9hmOUeLGcMuH7Bkx2YFRnfocwyWK9x"),
    ("マーカス",      "Markus",     "1nEJLzqgbsDmkjD9YC6d3ssYrqaMt5id6"),
    ("マイ",          "Mai",        "1ahxqYZGIjuSD2I3OA2kVK9DO8zh11AQB"),
    ("マルティナ",    "Martina",    "1R9ecgrKYWXqaaJ7c2K42zw1ELzf2y_jC"),
    ("ミルカ",        "Mirka",      "1DOsIhzmOgxy2nD52QZp5M93Ljob9wMDq"),
    ("ヨハン",        "Johann",     "1ersnnrpGw9RiC9TWXzbwKYgc-Hh-71qB"),
    ("ラウラ",        "Laura",      "173i3el3Xe6b5ihEgZnaSNNqqWUVLq75X"),
    ("ルク",          "Luke",       "14Y-wy0wqX28ke2FBKs1AkewNqrYiCXs0"),
    ("レオン",        "Leon",       "1AUEsbqdiiln6ZDOmt8dh6sk290HNYtMG"),
    ("レニ",          "Leni",       "1aImF-TnCBsvmsYmDgqpPA2swOhgBbcR9"),
    ("レノア",        "Lenore",     "1C_zh-Ihf6xjhijrUbiG_q5eV4mxZ9rVZ"),
    ("レノックス",    "Lenox",      "1mD2ARIOx_sot34ObIVnQxJHzNKKcpA2Y"),
    ("彰一",          "Shoichi",    "1Sbv9Hj3sbQl0GB0QWqc5Jsse5Ke9zAtI"),
    ("雪",            "Yuki",       "127v3dkhCndB0Isy0V_pJDHMYeOj1uh2V"),
    ("莉央",          "Rio",        "1o8eymosxt1c7yCt4_Vv40Ny_dx1LLdsg"),
    ("bERnice",       "bERnice",    "1UxX0EGZ3EHRP6QtRPCpGin92E4FaCpA-"),
    ("ロッジィ",      "Rozzi",      "101cXU4zcV1seJY4SNbjNAtQIswWKBH2o"),
    ("リアン",        "Lyanh",      "1TFL2N6jwlyEwOwh9kSRPDaM2UfEj7I5a"),
]

ok, skip, fail = 0, 0, 0
for jp, en, fid in chars:
    path = os.path.join(save_dir, f"{en}.png")
    if os.path.exists(path):
        print(f"  スキップ: {en}.png（既存）")
        skip += 1
        continue
    url = f"https://drive.google.com/uc?export=download&id={fid}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = r.read()
        if len(data) < 1000:
            print(f"  失敗: {en} ({jp}) — データが小さすぎます ({len(data)} bytes)")
            fail += 1
        else:
            with open(path, "wb") as f:
                f.write(data)
            print(f"  保存: {en}.png ({len(data)//1024} KB)")
            ok += 1
        time.sleep(0.3)
    except Exception as e:
        print(f"  エラー: {en} ({jp}) — {e}")
        fail += 1

print(f"\n完了: 保存 {ok}件 / スキップ {skip}件 / 失敗 {fail}件")
