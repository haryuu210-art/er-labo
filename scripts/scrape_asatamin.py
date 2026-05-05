# -*- coding: utf-8 -*-
"""
scrape_asatamin.py
【利用禁止】
asatamin-eternalreturn.com および w.atwiki.jp/erjp の利用は禁止されています。
このファイルは無効化されています。research_character.py が独自リサーチを行います。
"""

raise ImportError(
    "[COMPLIANCE] scrape_asatamin は利用禁止です。"
    " research_character.py の独自リサーチ機能を使用してください。"
)

# 以下は無効化済みコード（参考保存）
if False:
    pass

import urllib.request
import re
import time
import json
import os

BASE_URL = "https://asatamin-eternalreturn.com"
CHAR_LIST_URL = f"{BASE_URL}/characterlist/"
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "asatamin_url_cache.json")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read().decode("utf-8", errors="ignore")


def get_char_url_map():
    """キャラ英語名 -> ページURL のマップを返す（キャッシュあり）"""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)

    html = fetch(CHAR_LIST_URL)
    # /YYYY/MM/DD/charname/ 形式のURLを取得
    links = re.findall(
        r'href="(https://asatamin-eternalreturn\.com/\d{4}/\d{2}/\d{2}/([^/\"]+)/)"',
        html
    )
    url_map = {}
    for url, slug in links:
        url_map[slug.lower()] = url

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(url_map, f, ensure_ascii=False, indent=2)

    return url_map


def clean_html(html):
    """HTMLからテキストを抽出しクリーニング"""
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&[a-zA-Z#0-9]+;', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_main_content(html):
    """
    目次をスキップして本文の重要セクションを抽出する。
    「役割・特徴」「スキル紹介」が複数回出現する場合、2番目以降（本文）を使う。
    """
    results = []

    key_sections = ["役割・特徴", "スキル紹介", "キャラクターTips", "コンボ", "立ち回り"]

    for section in key_sections:
        positions = [m.start() for m in re.finditer(re.escape(section), html)]
        # 2番目以降の出現 = 本文（1番目は目次）
        idx = positions[1] if len(positions) >= 2 else (positions[0] if positions else -1)
        if idx == -1:
            continue

        # 次のh2/h3タグまで取得
        chunk = html[idx:idx + 2000]
        next_h = re.search(r'<h[23]', chunk[len(section):])
        if next_h:
            chunk = chunk[:len(section) + next_h.start()]

        text = re.sub(r'<[^>]+>', ' ', chunk)
        text = re.sub(r'&[a-zA-Z#0-9]+;', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()

        if len(text) > 50:
            results.append(f"【{section}】\n{text[:600]}")

    return "\n\n".join(results) if results else None


def get_character_info(char_name_en):
    """
    英語キャラ名からasataminの情報を取得する。
    戻り値: 攻略テキスト（文字列）または None
    """
    url_map = get_char_url_map()
    slug = char_name_en.lower()

    url = url_map.get(slug)
    if not url:
        for key, val in url_map.items():
            if slug in key or key in slug:
                url = val
                break

    if not url:
        print(f"  [scrape] {char_name_en} のページURLが見つかりません")
        return None

    # コンプライアンスチェック
    try:
        from compliance_check import can_scrape, SCRAPE_INTERVAL_SEC
        ok, reason = can_scrape(url)
        if not ok:
            print(f"  [COMPLIANCE BLOCK] {reason}")
            return None
    except ImportError:
        pass

    print(f"  [scrape] 取得中: {url}")
    try:
        html = fetch(url)
        result = extract_main_content(html)
        time.sleep(SCRAPE_INTERVAL_SEC)
        return result[:2000] if result else None

    except Exception as e:
        print(f"  [scrape] エラー: {e}")
        return None


if __name__ == "__main__":
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else "Jackie"
    info = get_character_info(name)
    print(info or "取得失敗")
