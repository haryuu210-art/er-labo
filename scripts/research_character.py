# -*- coding: utf-8 -*-
"""
research_character.py
Gemini 2.0 Flash + Google Search グラウンディングで
外部サイトに依存せず独自リサーチしてキャラ対策を生成する。

【禁止サイト】
- asatamin-eternalreturn.com  (利用禁止)
- w.atwiki.jp/erjp            (利用禁止)

無料枠: 通常API 1,500req/日、Searchグラウンディング 500req/日
"""

import urllib.request
import urllib.error
import json
import os
import re
import sys
import time

API_KEY_ENV = "GEMINI_API_KEY"
MODEL = "gemini-2.0-flash"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

# 独自リサーチ用プロンプト（外部サイト参照なし）
RESEARCH_PROMPT = """
あなたはEternal Return（エターナルリターン）の攻略専門家です。

キャラクター「{char_name_en}」（日本語名: {char_name_jp}）について、
公式情報・パッチノート・コミュニティの知識をもとに独自に調査し、
**このキャラと対戦する相手側の視点**で対策情報をまとめてください。

調査すべき観点:
- ロール（役割）: アサシン / ファイター / レンジャー / サポート / タンク / メイジ のいずれか
- 主要スキルの危険な使い方・コンボ
- 無敵・CC無効・ステルスの有無
- 弱点・対策として有効なアプローチ
- スキル情報（パッシブ・Q・W・E・R のスキル名と20〜40文字の説明）

【出力形式】JSONのみ出力してください。

{{
  "role": "アサシン",
  "caution": "注意点（危険なスキル・行動パターン）100〜150文字",
  "counter": "対策・立ち回り方法 100〜150文字",
  "invincible": true/false,
  "ccImmune": true/false,
  "stealth": true/false,
  "note": "特記事項（なければ空文字）",
  "skills": {{
    "passive": {{"name": "スキル名", "desc": "説明"}},
    "q": {{"name": "スキル名", "desc": "説明"}},
    "w": {{"name": "スキル名", "desc": "説明"}},
    "e": {{"name": "スキル名", "desc": "説明"}},
    "r": {{"name": "スキル名", "desc": "説明"}}
  }}
}}
"""


def get_api_key():
    key = os.environ.get(API_KEY_ENV, "")
    if key:
        return key
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from gemini_config import GEMINI_API_KEY
        if GEMINI_API_KEY:
            return GEMINI_API_KEY
    except ImportError:
        pass
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if line.startswith("GEMINI_API_KEY="):
                    return line.strip().split("=", 1)[1].strip('"\'')
    return None


def call_gemini_with_search(prompt, api_key):
    """Google Searchグラウンディングを使ってGeminiに最新情報を調査させる"""
    url = f"{API_URL}?key={api_key}"
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"google_search": {}}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 600,
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        data = json.loads(res.read().decode("utf-8"))

    text = data["candidates"][0]["content"]["parts"][0]["text"]
    # グラウンディングで参照したソースを確認（禁止サイトが混入していないかチェック）
    grounding_meta = data["candidates"][0].get("groundingMetadata", {})
    sources = grounding_meta.get("groundingChunks", [])
    blocked = ["asatamin-eternalreturn.com", "w.atwiki.jp/erjp"]
    for src in sources:
        uri = src.get("web", {}).get("uri", "")
        for b in blocked:
            if b in uri:
                print(f"[COMPLIANCE] 禁止サイト参照を検出・除外: {uri}")
    return text


def call_gemini_standard(prompt, api_key):
    """標準モード（検索なし）"""
    url = f"{API_URL}?key={api_key}"
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 600,
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        data = json.loads(res.read().decode("utf-8"))

    return data["candidates"][0]["content"]["parts"][0]["text"]


def extract_json(text):
    m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if m:
        return json.loads(m.group(1))
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if m:
        return json.loads(m.group(0))
    raise ValueError("JSON not found")


def research_character(char_name_en, char_name_jp, use_search=True):
    """
    Geminiで独自リサーチしてキャラ対策データを生成する。
    外部サイトのスクレイピングは一切行わない。

    use_search=True  → Google Searchグラウンディングで最新情報を参照
    use_search=False → Geminiの学習データのみで生成（グラウンディング節約）
    """
    api_key = get_api_key()
    if not api_key:
        print("[ERROR] GEMINI_API_KEY が設定されていません。")
        return None

    # コンプライアンスチェック
    try:
        from compliance_check import can_use_gemini
        ok, reason = can_use_gemini()
        if not ok:
            print(f"[COMPLIANCE BLOCK] {reason}")
            return None
    except ImportError:
        pass

    prompt = RESEARCH_PROMPT.format(
        char_name_en=char_name_en,
        char_name_jp=char_name_jp
    )

    mode = "Searchグラウンディング" if use_search else "標準"
    print(f"[Gemini/{mode}] リサーチ中: {char_name_jp} ({char_name_en})")

    try:
        if use_search:
            response_text = call_gemini_with_search(prompt, api_key)
        else:
            response_text = call_gemini_standard(prompt, api_key)

        data = extract_json(response_text)
        char_data = {
            "name": char_name_jp,
            "role": data.get("role", ""),
            "caution": data.get("caution", "情報なし"),
            "counter": data.get("counter", "情報なし"),
            "invincible": bool(data.get("invincible", False)),
            "ccImmune": bool(data.get("ccImmune", False)),
            "stealth": bool(data.get("stealth", False)),
            "note": data.get("note", ""),
            "skills": data.get("skills", {}),
        }
        print(f"[OK] 取得完了 ({mode})")
        return char_data

    except urllib.error.HTTPError as e:
        if e.code == 429:
            print("[WAIT] レート制限。60秒待機して再試行します...")
            time.sleep(60)
            return research_character(char_name_en, char_name_jp, use_search)
        # Searchグラウンディングが使えない場合は標準モードで再試行
        if e.code == 400 and use_search:
            print("[FALLBACK] Searchグラウンディング不可。標準モードで再試行...")
            return research_character(char_name_en, char_name_jp, use_search=False)
        print(f"[ERROR] HTTP {e.code}: {e.reason}")
        return None
    except Exception as e:
        print(f"[ERROR] {e}")
        return None


def get_japanese_name(char_name_en, api_key=None):
    """
    英語キャラ名から日本語版の正式名称をGeminiで取得する。
    クォータ節約のため標準モード（検索なし）で実行。
    戻り値: 日本語名（文字列）または None（取得失敗時）
    """
    if api_key is None:
        api_key = get_api_key()
    if not api_key:
        return None

    prompt = (
        f"Eternal Return（エターナルリターン）の実験体キャラクター「{char_name_en}」の"
        f"日本語版での正式名称（カタカナ）のみを1行で出力してください。"
        f"説明・記号・改行は不要です。カタカナのみ出力。例: コラライン"
    )

    print(f"[Gemini] 日本語名を取得中: {char_name_en}")
    url = f"{API_URL}?key={api_key}"
    try:
        payload = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.0, "maxOutputTokens": 20}
        }).encode("utf-8")
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=20) as res:
            data = json.loads(res.read().decode("utf-8"))

        raw = data["candidates"][0]["content"]["parts"][0]["text"].strip()

        # カタカナ・ひらがな・漢字・中点のみ残す
        name_jp = re.sub(r'[^぀-ヿ一-鿿・·]', '', raw)

        if name_jp:
            print(f"[OK] 日本語名: {name_jp}")
            return name_jp

        # カタカナが取れなかった場合、rawをそのまま返す（後で人が確認）
        print(f"[WARN] カタカナ抽出失敗。raw='{raw}'")
        return raw.strip() if raw.strip() else None

    except urllib.error.HTTPError as e:
        if e.code == 429:
            print("[WAIT] レート制限。60秒待機して再試行します...")
            time.sleep(60)
            return get_japanese_name(char_name_en, api_key)
        print(f"[ERROR] 日本語名取得失敗 HTTP {e.code}")
        return None
    except Exception as e:
        print(f"[ERROR] 日本語名取得失敗: {e}")
        return None


def research_multiple(char_list, use_search=True):
    """
    複数キャラを順番にリサーチする。
    char_list: [{"en": "Blair", "jp": "ブレア"}, ...]
    """
    results = []
    for i, c in enumerate(char_list):
        result = research_character(c["en"], c["jp"], use_search=use_search)
        if result:
            results.append(result)
        if i < len(char_list) - 1:
            time.sleep(5)  # レート制限対策
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Gemini独自リサーチでキャラ対策生成")
    parser.add_argument("--en", required=True, help="英語名 (例: Blair)")
    parser.add_argument("--jp", required=True, help="日本語名 (例: ブレア)")
    parser.add_argument("--no-search", action="store_true", help="Searchグラウンディングを使わない")
    args = parser.parse_args()

    result = research_character(args.en, args.jp, use_search=not args.no_search)
    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2))
