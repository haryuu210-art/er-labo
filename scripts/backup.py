# -*- coding: utf-8 -*-
"""
backup.py - 重要ファイルのバックアップ

使い方:
  python scripts/backup.py        # バックアップ作成
  python scripts/backup.py --list # バックアップ一覧表示

バックアップ先: scripts/backups/YYYYMMDD_HHMMSS/
保持数: 最新10件（古いものは自動削除）
"""

import os, shutil, sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backups")
MAX_BACKUPS = 10

TARGETS = [
    "js/characters.js",
    "js/roles_skills.js",
    "characters.html",
    "css/characters.css",
    "css/style.css",
    "rank-guide.html",
    "index.html",
]


def create_backup():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(BACKUP_DIR, timestamp)
    os.makedirs(dest, exist_ok=True)

    backed_up = []
    for rel in TARGETS:
        src = os.path.join(BASE_DIR, rel)
        if os.path.exists(src):
            dst = os.path.join(dest, rel.replace("/", os.sep))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            backed_up.append(rel)

    print(f"[OK] バックアップ完了: {timestamp}")
    for f in backed_up:
        print(f"  {f}")

    # 古いバックアップを削除
    entries = sorted(os.listdir(BACKUP_DIR))
    while len(entries) > MAX_BACKUPS:
        old = os.path.join(BACKUP_DIR, entries.pop(0))
        shutil.rmtree(old)
        print(f"[削除] 古いバックアップを削除: {os.path.basename(old)}")


def list_backups():
    if not os.path.exists(BACKUP_DIR):
        print("バックアップはまだありません。")
        return
    entries = sorted(os.listdir(BACKUP_DIR), reverse=True)
    print(f"=== バックアップ一覧 ({len(entries)}件) ===")
    for e in entries:
        path = os.path.join(BACKUP_DIR, e)
        size = sum(os.path.getsize(os.path.join(r, f))
                   for r, _, fs in os.walk(path) for f in fs)
        print(f"  {e}  ({size/1024:.1f} KB)")


if __name__ == "__main__":
    if "--list" in sys.argv:
        list_backups()
    else:
        create_backup()
