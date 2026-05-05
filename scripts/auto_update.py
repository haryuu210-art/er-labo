"""
auto_update.py
ERラボ自動更新パイプライン（完全無料）

処理フロー:
  1. 公式サイトでパッチノートを確認
  2. 新キャラが検出されたら:
     a. Geminiで対策情報をリサーチ
     b. ファンキットから画像をDL
     c. characters.js を更新
     d. HTML内のdriveIdsマップを更新

使い方:
  python auto_update.py               # 通常実行（更新チェックのみ）
  python auto_update.py --force       # 強制的に新キャラ追加処理を実行
  python auto_update.py --add-char "Coraline" "コラライン"  # 手動で1キャラ追加

定期実行（Windowsタスクスケジューラ）:
  タスクスケジューラ → 新規タスク → 毎日 or 週1回
  プログラム: python
  引数: C:\Users\TAKA\Desktop\ERラボ\scripts\auto_update.py
"""

import sys
import os
import json
import re
import argparse
from datetime import datetime

# 同ディレクトリのモジュールをインポート
sys.path.insert(0, os.path.dirname(__file__))
from check_update import check_for_updates
from download_fankit import download_new_characters
from research_character import research_character, get_japanese_name

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARACTERS_JS = os.path.join(BASE_DIR, "js", "characters.js")
CHARACTERS_HTML = os.path.join(BASE_DIR, "characters.html")
LOG_FILE = os.path.join(os.path.dirname(__file__), "update_log.json")


def load_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"updates": []}


def save_log(log):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def read_characters_js():
    """characters.js から現在のキャラ配列を読み込む"""
    with open(CHARACTERS_JS, "r", encoding="utf-8") as f:
        content = f.read()
    return content


def append_character_to_js(char_data):
    """
    characters.js の末尾（配列の最後）に新キャラを追加する。
    """
    content = read_characters_js()

    # 既に存在するか確認
    if f'"name": "{char_data["name"]}"' in content or f"name: \"{char_data['name']}\"" in content:
        print(f"  ⚠ {char_data['name']} はすでに characters.js に存在します。スキップ。")
        return False

    note_val = f'"{char_data["note"]}"' if char_data["note"] else '""'
    new_entry = f"""  {{
    name: "{char_data['name']}",
    caution: "{char_data['caution'].replace('"', '\\"')}",
    counter: "{char_data['counter'].replace('"', '\\"')}",
    invincible: {'true' if char_data['invincible'] else 'false'}, ccImmune: {'true' if char_data['ccImmune'] else 'false'}, stealth: {'true' if char_data['stealth'] else 'false'}, note: {note_val}
  }},"""

    # 配列の最後の }]; の前に挿入
    content = re.sub(r'\];\s*$', f'\n{new_entry}\n];', content.rstrip())

    with open(CHARACTERS_JS, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"  ✅ {char_data['name']} を characters.js に追加しました")
    return True


def append_role_and_skills(char_name_jp, char_data):
    """
    roles_skills.js の charRoles と charSkills に新キャラを追加する。
    """
    roles_js = os.path.join(BASE_DIR, "js", "roles_skills.js")
    if not os.path.exists(roles_js):
        print("  [WARN] roles_skills.js が見つかりません。スキップ。")
        return

    with open(roles_js, "r", encoding="utf-8") as f:
        content = f.read()

    role = char_data.get("role", "")
    skills = char_data.get("skills", {})

    # ロール追加
    if role and char_name_jp not in content:
        role_entry = f'  "{char_name_jp}":           "{role}",'
        content = re.sub(r'(const charRoles = \{)', r'\1', content)
        content = content.replace("// スキル情報はadd_roles_and_skills.py", f'{role_entry}\n// スキル情報はadd_roles_and_skills.py')
        print(f"  [OK] {char_name_jp} のロール ({role}) を roles_skills.js に追加")

    # スキル追加
    if skills:
        def esc(s): return str(s).replace('"', '\\"')
        sk_lines = [f'  "{char_name_jp}": {{']
        for key in ["passive", "q", "w", "e", "r"]:
            s = skills.get(key, {})
            sk_lines.append(f'    {key}: {{ name: "{esc(s.get("name",""))}", desc: "{esc(s.get("desc",""))}" }},')
        sk_lines.append('  },')
        sk_str = "\n".join(sk_lines)
        content = content.replace("const charSkills = {};",
                                  f"const charSkills = {{\n{sk_str}\n}};")
        print(f"  [OK] {char_name_jp} のスキル情報を roles_skills.js に追加")

    with open(roles_js, "w", encoding="utf-8") as f:
        f.write(content)


def append_to_drive_ids(char_name_jp, char_name_en):
    """
    characters.html 内の driveIds に新キャラのマッピングを追加する。
    """
    with open(CHARACTERS_HTML, "r", encoding="utf-8") as f:
        html = f.read()

    entry = f'    "{char_name_jp}":           "{char_name_en}",'
    if char_name_jp in html:
        print(f"  ⚠ {char_name_jp} は driveIds にすでに存在します。スキップ。")
        return False

    # "// ---- 追加取得済み ----" セクションの後に追記
    marker = "// ---- 追加取得済み ----"
    if marker in html:
        html = html.replace(marker, f"{marker}\n{entry}")
    else:
        # マーカーがなければ }; の直前に追加
        html = re.sub(r'(\s*\};)', f'\n{entry}\n\\1', html, count=1)

    with open(CHARACTERS_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  ✅ {char_name_jp} ({char_name_en}) を driveIds に追加しました")
    return True


def process_new_character(char_name_en, char_name_jp):
    """新キャラを全工程で処理する"""
    print(f"\n{'='*50}")
    print(f"新キャラ処理: {char_name_jp} ({char_name_en})")
    print(f"{'='*50}")

    # Step 1: Geminiでリサーチ
    print("\n[1/3] Geminiでキャラ情報をリサーチ...")
    char_data = research_character(char_name_en, char_name_jp)
    if not char_data:
        print("  ❌ リサーチ失敗。手動入力が必要です。")
        char_data = {
            "name": char_name_jp,
            "caution": "情報収集中。パッチノートを確認してください。",
            "counter": "情報収集中。パッチノートを確認してください。",
            "invincible": False,
            "ccImmune": False,
            "stealth": False,
            "note": "※自動生成失敗。手動更新が必要です。",
        }

    # Step 2: characters.js に追加
    print("\n[2/3] characters.js を更新...")
    append_character_to_js(char_data)

    # Step 3: roles_skills.js にロール＆スキル追加
    append_role_and_skills(char_name_jp, char_data)

    # Step 4: driveIds マッピング追加
    append_to_drive_ids(char_name_jp, char_name_en)

    # Step 4: ファンキットから画像DL
    print("\n[3/3] ファンキットから画像をダウンロード...")
    downloaded = download_new_characters(target_name=char_name_en)
    if not downloaded:
        print(f"  ⚠ {char_name_en}.png の自動DLに失敗しました。")
        print(f"  → 手動でダウンロードして images/characters/{char_name_en}.png に配置してください。")

    return {
        "char": char_name_jp,
        "char_en": char_name_en,
        "processed_at": datetime.now().isoformat(),
        "image_downloaded": len(downloaded) > 0,
        "data": char_data,
    }


def run_pipeline(force=False):
    print(f"\n{'='*50}")
    print(f"ER LAB 自動更新パイプライン")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}\n")

    # アップデート確認
    if not force:
        result = check_for_updates()
        if not result or not result["has_update"]:
            print("→ 新規アップデートなし。終了します。")
            return

        new_chars = result.get("new_characters", [])
        if not new_chars:
            print("→ パッチはありましたが新キャラは検出されませんでした。")
            print("  (公式サイトのHTML構造が変わった場合は手動確認してください)")
            return
    else:
        print("⚡ 強制実行モード")
        new_chars = []

    # 新キャラを処理
    log = load_log()
    processed = []
    for char_en in new_chars:
        # 日本語名をGeminiで自動取得
        print(f"\n[日本語名取得] {char_en}...")
        char_jp = get_japanese_name(char_en)
        if not char_jp:
            print(f"  [WARNING] 日本語名の取得に失敗。英語名で仮登録します: {char_en}")
            char_jp = char_en
        else:
            print(f"  -> {char_jp}")
        import time; time.sleep(3)  # レート制限対策
        entry = process_new_character(char_en, char_jp)
        processed.append(entry)

    if processed:
        log["updates"].append({
            "date": datetime.now().isoformat(),
            "characters": processed,
        })
        save_log(log)
        print(f"\n✅ {len(processed)}キャラの処理が完了しました。")
    else:
        print("\n→ 処理するキャラはありませんでした。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ERラボ自動更新パイプライン")
    parser.add_argument("--force", action="store_true", help="強制実行")
    parser.add_argument("--add-char", nargs=2, metavar=("EN", "JP"),
                        help="手動で1キャラ追加 (例: --add-char Coraline コラライン)")
    args = parser.parse_args()

    if args.add_char:
        char_en, char_jp = args.add_char
        result = process_new_character(char_en, char_jp)
        print(f"\n完了: {json.dumps(result, ensure_ascii=False, indent=2)}")
    else:
        run_pipeline(force=args.force)
