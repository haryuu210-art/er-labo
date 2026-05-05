# -*- coding: utf-8 -*-
"""
add_roles_and_skills.py
Gemini 1回のリクエストで全キャラのロール＋スキル情報を取得し、
js/roles_skills.js を生成する。

使い方:
  python add_roles_and_skills.py           # ロール+スキル取得
  python add_roles_and_skills.py --roles-only  # ロールのみ
"""

import urllib.request
import json
import os
import re
import sys
import time
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

API_KEY_ENV = "GEMINI_API_KEY"
MODEL = "gemini-2.0-flash"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_JS = os.path.join(BASE_DIR, "js", "roles_skills.js")

# 全87キャラの英語名リスト
ALL_CHARS_EN = [
    "Eleven", "Isaac", "Isol", "Adina", "Adela", "Adriana", "Abigail",
    "Aya", "Alda", "Alex", "Alonso", "Lyanh", "Irem", "Vanya", "William",
    "Aiden", "Eva", "Echion", "Estelle", "Emma", "Elena", "Garnet",
    "Karla", "Katja", "Camilo", "Chiara", "Cathy", "Chloe", "Kenneth",
    "Zahir", "Xiukai", "Jenny", "Sissela", "Charlotte", "Jackie", "Silvia",
    "Sua", "Celine", "LiDailin", "Tazia", "Daniel", "Darko", "Tsubame",
    "Tia", "Theodore", "Debbie", "Nathapon", "Nadine", "Nicky", "Hart",
    "Barbara", "Bianca", "Piolo", "Hyunwoo", "Fiora", "Felix", "Priya",
    "Haze", "Hyejin", "Markus", "Mai", "Magnus", "Martina", "Mirka",
    "Johann", "Laura", "Luke", "Leon", "Leni", "Lenore", "Lenox",
    "Shoichi", "Yuki", "Rio", "Banis", "Hisui", "Yang", "Justina",
    "Yumin", "Lodge", "Istvan", "Nia", "Shirin", "Henry", "Blair",
    "Fenrir", "Coraline", "Rozzi", "bERnice",
]

# JP名マッピング（characters.htmlのdriveIdsから）
EN_TO_JP = {
    "Eleven": "Eleven", "Isaac": "アイザック", "Isol": "アイソル",
    "Adina": "アディナ", "Adela": "アデラ", "Adriana": "アドリアナ",
    "Abigail": "アビゲイル", "Aya": "アヤ", "Alda": "アルダ",
    "Alex": "アレックス", "Alonso": "アロンソ", "Lyanh": "イアン",
    "Irem": "イレム", "Vanya": "ヴァーニャ", "William": "ウィリアム",
    "Aiden": "エイデン", "Eva": "エヴァ", "Echion": "エキオン",
    "Estelle": "エステル", "Emma": "エマ", "Elena": "エレナ",
    "Garnet": "ガーネット", "Karla": "カーラ", "Katja": "カティア",
    "Camilo": "カミロ", "Chiara": "キアラ", "Cathy": "キャッシー",
    "Chloe": "クロエ", "Kenneth": "ケネス", "Zahir": "ザヒル",
    "Xiukai": "シウカイ", "Jenny": "ジェニー", "Sissela": "シセラ",
    "Charlotte": "シャーロット", "Jackie": "ジャッキー", "Silvia": "シルヴィア",
    "Sua": "スア", "Celine": "セリーヌ", "LiDailin": "ダイリン",
    "Tazia": "タジア", "Daniel": "ダニエル", "Darko": "ダルコ",
    "Tsubame": "つばめ", "Tia": "ティア", "Theodore": "テオドール",
    "Debbie": "デビー&マーリン", "Nathapon": "ナタポン", "Nadine": "ナディン",
    "Nicky": "ニッキー", "Hart": "ハート", "Barbara": "バーバラ",
    "Bianca": "ビアンカ", "Piolo": "ピオロ", "Hyunwoo": "ヒョヌ",
    "Fiora": "フィオラ", "Felix": "フェリックス", "Priya": "プリヤ",
    "Haze": "ヘイズ", "Hyejin": "ヘジン", "Markus": "マーカス",
    "Mai": "マイ", "Magnus": "マグヌス", "Martina": "マルティナ",
    "Mirka": "ミルカ", "Johann": "ヨハン", "Laura": "ラウラ",
    "Luke": "ルク", "Leon": "レオン", "Leni": "レニ",
    "Lenore": "レノア", "Lenox": "レノックス", "Shoichi": "彰一",
    "Yuki": "雪", "Rio": "莉央", "Banis": "バニス",
    "Hisui": "ヒスイ", "Yang": "ヤン", "Justina": "ユスティナ",
    "Yumin": "ユミン", "Lodge": "ロッジ", "Istvan": "イシュトヴァーン",
    "Nia": "ニア", "Shirin": "シュリン", "Henry": "ヘンリー",
    "Blair": "ブレア", "Fenrir": "フェンリル", "Coraline": "コラライン",
    "Rozzi": "ロッジ", "bERnice": "バニス",
}

ROLES_PROMPT = """
あなたはEternal Return（エターナルリターン）の専門家です。

以下の実験体キャラクター全員のロール（役割）を教えてください。
ロールは必ず以下の6つのいずれかにしてください:
- アサシン
- ファイター
- レンジャー
- サポート
- タンク
- メイジ

英語名リスト:
{char_list}

JSONのみ出力してください（コードブロック不要）:
{{
  "Eleven": "ファイター",
  "Isaac": "ファイター",
  ...（全キャラ）
}}
"""

SKILLS_PROMPT = """
あなたはEternal Return（エターナルリターン）の専門家です。

以下の実験体キャラクター全員のスキル情報を教えてください。
スキル名は日本語で。説明は20〜40文字の簡潔な1行で。

英語名リスト:
{char_list}

JSONのみ出力してください:
{{
  "Eleven": {{
    "passive": {{"name": "スキル名", "desc": "説明"}},
    "q": {{"name": "スキル名", "desc": "説明"}},
    "w": {{"name": "スキル名", "desc": "説明"}},
    "e": {{"name": "スキル名", "desc": "説明"}},
    "r": {{"name": "スキル名", "desc": "説明"}}
  }},
  ...
}}
"""


def get_api_key():
    key = os.environ.get(API_KEY_ENV, "")
    if key:
        return key
    try:
        from gemini_config import GEMINI_API_KEY
        if GEMINI_API_KEY:
            return GEMINI_API_KEY
    except ImportError:
        pass
    return None


def call_gemini(prompt, api_key, max_tokens=4000):
    url = f"{API_URL}?key={api_key}"
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": max_tokens,
        }
    }).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=60) as res:
        data = json.loads(res.read().decode("utf-8"))
    return data["candidates"][0]["content"]["parts"][0]["text"]


def extract_json(text):
    # コードブロック除去
    m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if m:
        return json.loads(m.group(1))
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if m:
        return json.loads(m.group(0))
    raise ValueError("JSON not found in response")


def fetch_roles(api_key, char_list):
    print("[Gemini] ロール情報を取得中...")
    prompt = ROLES_PROMPT.format(char_list=", ".join(char_list))
    try:
        text = call_gemini(prompt, api_key, max_tokens=2000)
        roles = extract_json(text)
        print(f"[OK] {len(roles)} キャラのロールを取得")
        return roles
    except urllib.error.HTTPError as e:
        if e.code == 429:
            print("[WAIT] レート制限。60秒待機...")
            time.sleep(60)
            return fetch_roles(api_key, char_list)
        raise


def fetch_skills_batch(api_key, char_list):
    """キャラを20件ずつ分割してスキル取得"""
    all_skills = {}
    batch_size = 20
    for i in range(0, len(char_list), batch_size):
        batch = char_list[i:i + batch_size]
        print(f"[Gemini] スキル情報取得中 ({i+1}-{min(i+batch_size, len(char_list))}/{len(char_list)})...")
        prompt = SKILLS_PROMPT.format(char_list=", ".join(batch))
        try:
            text = call_gemini(prompt, api_key, max_tokens=4000)
            skills = extract_json(text)
            all_skills.update(skills)
            print(f"[OK] {len(batch)} キャラ完了")
        except Exception as e:
            print(f"[ERROR] バッチ {i//batch_size + 1}: {e}")
        if i + batch_size < len(char_list):
            time.sleep(5)
    return all_skills


def generate_js(roles, skills):
    """roles_skills.js を生成する"""
    lines = [
        "// roles_skills.js - キャラロール＆スキル情報（Gemini自動生成）",
        "// 生成日: " + __import__('datetime').datetime.now().strftime('%Y-%m-%d'),
        "",
        "const charRoles = {",
    ]

    for en_name in ALL_CHARS_EN:
        jp_name = EN_TO_JP.get(en_name, en_name)
        role = roles.get(en_name, "")
        if role:
            lines.append(f'  "{jp_name}": "{role}",')

    lines += ["};", "", "const charSkills = {"]

    for en_name in ALL_CHARS_EN:
        jp_name = EN_TO_JP.get(en_name, en_name)
        sk = skills.get(en_name, {})
        if sk:
            def esc(s):
                return str(s).replace('"', '\\"')
            p = sk.get("passive", {})
            q = sk.get("q", {})
            w = sk.get("w", {})
            e = sk.get("e", {})
            r = sk.get("r", {})
            lines.append(f'  "{jp_name}": {{')
            lines.append(f'    passive: {{ name: "{esc(p.get("name",""))}", desc: "{esc(p.get("desc",""))}" }},')
            lines.append(f'    q: {{ name: "{esc(q.get("name",""))}", desc: "{esc(q.get("desc",""))}" }},')
            lines.append(f'    w: {{ name: "{esc(w.get("name",""))}", desc: "{esc(w.get("desc",""))}" }},')
            lines.append(f'    e: {{ name: "{esc(e.get("name",""))}", desc: "{esc(e.get("desc",""))}" }},')
            lines.append(f'    r: {{ name: "{esc(r.get("name",""))}", desc: "{esc(r.get("desc",""))}" }},')
            lines.append(f'  }},')

    lines += ["};"]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--roles-only", action="store_true")
    parser.add_argument("--skills-only", action="store_true")
    args = parser.parse_args()

    api_key = get_api_key()
    if not api_key:
        print("[ERROR] GEMINI_API_KEY が設定されていません")
        sys.exit(1)

    # コンプライアンスチェック
    try:
        from compliance_check import can_use_gemini
        ok, reason = can_use_gemini()
        if not ok:
            print(f"[COMPLIANCE BLOCK] {reason}")
            sys.exit(1)
    except ImportError:
        pass

    roles = {}
    skills = {}

    if not args.skills_only:
        roles = fetch_roles(api_key, ALL_CHARS_EN)

    if not args.roles_only:
        time.sleep(3)
        skills = fetch_skills_batch(api_key, ALL_CHARS_EN)

    # 既存ファイルがあればマージ
    if os.path.exists(OUTPUT_JS):
        print(f"[INFO] 既存の roles_skills.js を上書きします")

    js_content = generate_js(roles, skills)
    with open(OUTPUT_JS, "w", encoding="utf-8") as f:
        f.write(js_content)

    print(f"\n[DONE] {OUTPUT_JS} を生成しました")
    print(f"  ロール: {len(roles)} キャラ")
    print(f"  スキル: {len(skills)} キャラ")


if __name__ == "__main__":
    main()
