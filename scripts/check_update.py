"""
check_update.py
公式サイトのパッチノートを監視し、新キャラが追加されたか検出する。
無料・外部API不要。
"""

import urllib.request
import json
import re
import os
from datetime import datetime

PATCH_URL = "https://playeternalreturn.com/posts/news"
STATE_FILE = os.path.join(os.path.dirname(__file__), "last_state.json")


def fetch_page(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as res:
        return res.read().decode("utf-8", errors="ignore")


def extract_patch_titles(html):
    """パッチノートのタイトル一覧を抽出する"""
    # ER公式サイトのニュース記事タイトルパターン
    titles = re.findall(r'(?:패치|Patch|パッチ)[^\<"]{0,60}', html, re.IGNORECASE)
    return list(set(titles))


def extract_new_characters(html):
    """HTMLからキャラ名らしき文字列を抽出する（英語名）"""
    # 公式サイトのキャラ紹介パターン: "New Character: NAME" や "신규 실험체" など
    found = []
    patterns = [
        r'[Nn]ew [Cc]haracter[:\s]+([A-Z][a-z]+)',
        r'신규 실험체[:\s]+([가-힣A-Za-z]+)',
        r'NEW SURVIVOR[:\s]+([A-Z][a-z]+)',
    ]
    for pat in patterns:
        found += re.findall(pat, html)
    return list(set(found))


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_titles": [], "known_characters": [], "last_checked": ""}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def check_for_updates():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] 公式サイトを確認中...")

    try:
        html = fetch_page(PATCH_URL)
    except Exception as e:
        print(f"  ❌ フェッチ失敗: {e}")
        return None

    state = load_state()
    current_titles = extract_patch_titles(html)
    new_titles = [t for t in current_titles if t not in state["last_titles"]]

    new_chars = extract_new_characters(html)
    truly_new_chars = [c for c in new_chars if c not in state["known_characters"]]

    result = {
        "has_update": len(new_titles) > 0,
        "new_patch_titles": new_titles,
        "new_characters": truly_new_chars,
        "checked_at": datetime.now().isoformat(),
    }

    if new_titles:
        print(f"  ✅ 新しいパッチノートを検出: {new_titles}")
    else:
        print(f"  — 新規パッチなし")

    if truly_new_chars:
        print(f"  🆕 新キャラ候補: {truly_new_chars}")

    # 状態を更新
    state["last_titles"] = current_titles
    state["known_characters"] = list(set(state["known_characters"] + truly_new_chars))
    state["last_checked"] = result["checked_at"]
    save_state(state)

    return result


if __name__ == "__main__":
    result = check_for_updates()
    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2))
