# -*- coding: utf-8 -*-
"""
set_role.py  - キャラのロールを1つ設定する

使い方:
  python set_role.py "Eleven" "ファイター"
  python set_role.py "ガーネット" "レンジャー"
  python set_role.py --list          # 現在の全ロール表示
  python set_role.py --list タンク   # 特定ロールのキャラ一覧

有効なロール: アサシン / ファイター / レンジャー / サポート / タンク / メイジ
"""

import sys
import os
import re

ROLES_JS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "js", "roles_skills.js")
VALID_ROLES = ["アサシン", "ファイター", "マークスマン", "サポート", "タンク", "メイジ"]


def load_roles():
    with open(ROLES_JS, encoding="utf-8") as f:
        content = f.read()
    matches = re.findall(r'"([^"]+)":\s+"([^"]+)"', content[:content.find("const charSkills")])
    return dict(matches), content


def set_role(char_name, new_role):
    if new_role not in VALID_ROLES:
        print(f"[ERROR] 無効なロール: {new_role}")
        print(f"  有効なロール: {' / '.join(VALID_ROLES)}")
        return False

    roles, content = load_roles()

    if char_name not in roles:
        print(f"[ERROR] キャラが見つかりません: {char_name}")
        print(f"  登録済みキャラ数: {len(roles)}")
        return False

    old_role = roles[char_name]
    if old_role == new_role:
        print(f"[INFO] {char_name} は既に {new_role} です。変更不要。")
        return True

    # 対象行を置換（日本語キャラ名は空白パディングが異なるため柔軟に対応）
    pattern = r'("' + re.escape(char_name) + r'")\s*:\s*"[^"]+"'
    replacement = lambda m: m.group(1) + (':' + ' ' * max(1, 20 - len(char_name))) + f'"{new_role}"'
    new_content, count = re.subn(pattern, replacement, content)

    if count == 0:
        print(f"[ERROR] 置換失敗。手動で編集してください。")
        return False

    with open(ROLES_JS, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"[OK] {char_name}: {old_role} -> {new_role}")
    return True


def list_roles(filter_role=None):
    roles, _ = load_roles()
    if filter_role:
        targets = [(n, r) for n, r in roles.items() if r == filter_role]
        print(f"[{filter_role}] {len(targets)}キャラ:")
        for name, role in targets:
            print(f"  {name}")
    else:
        from collections import Counter
        counts = Counter(roles.values())
        print("=== ロール分布 ===")
        for role in VALID_ROLES:
            chars = [n for n, r in roles.items() if r == role]
            print(f"  {role}({counts.get(role, 0)}): {', '.join(chars)}")


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args or args[0] == "--help":
        print(__doc__)
        sys.exit(0)

    if args[0] == "--list":
        list_roles(args[1] if len(args) > 1 else None)
    elif len(args) == 2:
        set_role(args[0], args[1])
    else:
        print("使い方: python set_role.py <キャラ名> <ロール>")
        print("        python set_role.py --list [ロール名]")
