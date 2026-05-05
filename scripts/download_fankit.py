"""
download_fankit.py
Google Driveのファンキットフォルダから画像を一括ダウンロードする。
無料・APIキー不要（公開フォルダのみ対応）。

使い方:
  python download_fankit.py                    # 全キャラ取得
  python download_fankit.py --name Coraline    # 特定キャラのみ
"""

import urllib.request
import urllib.parse
import re
import os
import json
import argparse
import time

FOLDER_ID = "1m__ubKg-KY7TqnqbFqwHi1DVxrdBeTEW"
FOLDER_URL = f"https://drive.google.com/drive/folders/{FOLDER_ID}"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "images", "characters")
STATE_FILE = os.path.join(os.path.dirname(__file__), "fankit_state.json")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as res:
        return res.read().decode("utf-8", errors="ignore")


def list_drive_files(folder_id):
    """Google Driveフォルダ内のファイル一覧を取得する"""
    url = f"https://drive.google.com/drive/folders/{folder_id}"
    try:
        html = fetch(url)
    except Exception as e:
        print(f"  ❌ フォルダ取得失敗: {e}")
        return []

    # Drive HTMLからファイルIDとファイル名を抽出
    # パターン: data-id="FILE_ID" や "name":"FILENAME"
    file_ids = re.findall(r'"([0-9A-Za-z_\-]{25,})"[^>]*?(?:data-id|id)=', html)
    # より確実なパターン
    entries = re.findall(r'\["([0-9A-Za-z_\-]{25,})"[^\]]*?"([^"]+\.png)"', html)

    if not entries:
        # 別パターンで再試行
        ids = re.findall(r'data-id="([0-9A-Za-z_\-]{25,})"', html)
        names = re.findall(r'"name"\s*:\s*"([^"]+\.(?:png|jpg|webp))"', html)
        entries = list(zip(ids, names)) if ids and names else []

    return entries


def download_file(file_id, filename, output_path):
    """Google DriveファイルをダウンロードしてPNGとして保存"""
    # 直接ダウンロードURL
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as res:
            content = res.read()
        with open(output_path, "wb") as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"    ❌ {filename} DL失敗: {e}")
        return False


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"downloaded": {}}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def download_new_characters(target_name=None):
    """
    フォルダ内の画像をダウンロードする。
    target_name: 特定キャラ名（英語）を指定した場合はそれのみ
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    state = load_state()

    print(f"📂 Google Drive フォルダを確認中...")
    entries = list_drive_files(FOLDER_ID)

    if not entries:
        print("  ⚠ ファイル一覧を取得できませんでした。")
        print("  → フォルダHTMLの構造が変わった可能性があります。")
        print("  → 手動確認: " + FOLDER_URL)
        return []

    downloaded = []
    for file_id, filename in entries:
        # ファイル名からキャラ名を推定（例: Coraline.png → Coraline）
        char_name = os.path.splitext(filename)[0]

        # 特定キャラ指定の場合はスキップ
        if target_name and char_name.lower() != target_name.lower():
            continue

        output_path = os.path.join(OUTPUT_DIR, filename)

        # すでにDL済みかつファイルが存在する場合はスキップ
        if char_name in state["downloaded"] and os.path.exists(output_path):
            print(f"  ✓ {char_name} — スキップ（取得済み）")
            continue

        print(f"  ⬇ {char_name} をダウンロード中...")
        success = download_file(file_id, filename, output_path)
        if success:
            state["downloaded"][char_name] = file_id
            downloaded.append(char_name)
            print(f"    ✅ {char_name} 保存完了 → {output_path}")

        time.sleep(0.5)  # レート制限対策

    save_state(state)
    print(f"\n完了: {len(downloaded)}件ダウンロード")
    return downloaded


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ERファンキット画像ダウンローダー")
    parser.add_argument("--name", help="特定キャラ名（英語）を指定")
    args = parser.parse_args()
    download_new_characters(target_name=args.name)
