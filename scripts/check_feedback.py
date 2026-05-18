# ERラボ フィードバック自動チェックスクリプト
# 起動30分後・インターネット接続確認後に実行される

import csv
import urllib.request
import urllib.error
import webbrowser
import os
import sys
import json
from datetime import datetime

# Windows PowerShell の文字化け対策
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ============================================================
# ★ 設定欄 — ここだけ変更すればOK
# ============================================================
# Google スプレッドシートのCSV公開URL
# 設定方法: feedback_setup_guide.txt を参照
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR6lOTrYEusIzi-0zIaKKb59zYf8jvPyq2oaUiClP1zLl4sb1NHLQYooMbwvqPPDOHsLowD43Tdh6LD/pub?gid=2032038044&single=true&output=csv"

# 既読済みの行数を記録するファイル
STATE_FILE = os.path.join(os.path.dirname(__file__), "feedback_state.json")

# 結果HTMLの出力先
OUTPUT_HTML = os.path.join(os.path.dirname(__file__), "feedback_report.html")
# ============================================================

# キーワード分類ルール（優先度高→低の順）
RULES = [
    {
        "label": "バグ・エラー",
        "priority": "HIGH",
        "color": "#ef4444",
        "keywords": ["バグ", "エラー", "壊れ", "表示されない", "動かない", "おかしい", "間違い", "誤字", "404"]
    },
    {
        "label": "情報追加リクエスト",
        "priority": "HIGH",
        "color": "#f97316",
        "keywords": ["追加", "載せて", "掲載", "知りたい", "教えて", "ほしい", "なかった", "ない"]
    },
    {
        "label": "内容の更新・修正",
        "priority": "MEDIUM",
        "color": "#eab308",
        "keywords": ["更新", "古い", "変わった", "パッチ", "アップデート", "修正", "直して"]
    },
    {
        "label": "デザイン・使いやすさ",
        "priority": "MEDIUM",
        "color": "#3b82f6",
        "keywords": ["見にくい", "わかりにくい", "デザイン", "色", "フォント", "スマホ", "モバイル", "レイアウト"]
    },
    {
        "label": "感想・その他",
        "priority": "LOW",
        "color": "#6b7280",
        "keywords": []
    },
]


def check_internet():
    try:
        urllib.request.urlopen("https://www.google.com", timeout=5)
        return True
    except Exception:
        return False


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_row": 1}  # 1行目はヘッダーなので2行目から


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def fetch_csv(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as res:
        content = res.read().decode("utf-8")
    reader = csv.reader(content.splitlines())
    rows = list(reader)
    return rows


def classify(text):
    text_lower = text.lower()
    for rule in RULES:
        for kw in rule["keywords"]:
            if kw in text_lower:
                return rule
    return RULES[-1]  # 感想・その他


def build_html(new_items, all_items):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    priority_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for item in new_items:
        priority_counts[item["rule"]["priority"]] += 1

    rows_html = ""
    for item in new_items:
        r = item["rule"]
        rows_html += f"""
        <tr>
          <td style="color:#94a3b8;font-size:12px;">{item['timestamp']}</td>
          <td>
            <span style="background:{r['color']}22;color:{r['color']};border:1px solid {r['color']}44;
              font-size:11px;padding:2px 10px;border-radius:100px;letter-spacing:0.1em;">
              {r['label']}
            </span>
          </td>
          <td style="font-size:13px;color:#e2e8f0;line-height:1.6;">{item['text']}</td>
          <td style="text-align:center;">
            <span style="font-size:11px;font-weight:700;color:{r['color']};">{r['priority']}</span>
          </td>
        </tr>"""

    if not new_items:
        rows_html = """<tr><td colspan="4" style="text-align:center;color:#475569;padding:40px;">
          新しいフィードバックはありません</td></tr>"""

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>フィードバックレポート — {now}</title>
  <style>
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{ font-family:'Noto Sans JP',sans-serif; background:#0a0a0a; color:#e2e8f0; padding:40px; }}
    h1 {{ font-size:24px; font-weight:700; margin-bottom:4px; }}
    .sub {{ font-size:13px; color:#475569; margin-bottom:32px; }}
    .stats {{ display:flex; gap:16px; margin-bottom:32px; }}
    .stat {{ background:#141414; border:1px solid #1e1e1e; border-radius:8px; padding:16px 24px; }}
    .stat-num {{ font-size:32px; font-weight:700; line-height:1; }}
    .stat-label {{ font-size:11px; color:#475569; letter-spacing:0.3em; text-transform:uppercase; margin-top:4px; }}
    .high {{ color:#ef4444; }} .medium {{ color:#eab308; }} .low {{ color:#6b7280; }} .total {{ color:#a3e635; }}
    h2 {{ font-size:13px; letter-spacing:0.3em; text-transform:uppercase; color:#475569; margin-bottom:16px; }}
    table {{ width:100%; border-collapse:collapse; background:#0f0f0f; border-radius:8px; overflow:hidden; }}
    th {{ font-size:11px; letter-spacing:0.3em; text-transform:uppercase; color:#475569;
          text-align:left; padding:12px 16px; border-bottom:1px solid #1e1e1e; }}
    td {{ padding:14px 16px; border-bottom:1px solid #111; vertical-align:top; }}
    tr:last-child td {{ border-bottom:none; }}
    .footer {{ margin-top:24px; font-size:12px; color:#334155; text-align:center; }}
  </style>
</head>
<body>
  <h1>フィードバックレポート</h1>
  <p class="sub">生成日時: {now} ／ 累計: {len(all_items)}件 ／ 今回の新着: {len(new_items)}件</p>

  <div class="stats">
    <div class="stat"><div class="stat-num total">{len(new_items)}</div><div class="stat-label">新着</div></div>
    <div class="stat"><div class="stat-num high">{priority_counts['HIGH']}</div><div class="stat-label">優先度 HIGH</div></div>
    <div class="stat"><div class="stat-num medium">{priority_counts['MEDIUM']}</div><div class="stat-label">優先度 MEDIUM</div></div>
    <div class="stat"><div class="stat-num low">{priority_counts['LOW']}</div><div class="stat-label">優先度 LOW</div></div>
  </div>

  <h2>新着フィードバック（HIGH優先度から表示）</h2>
  <table>
    <thead>
      <tr>
        <th style="width:140px;">日時</th>
        <th style="width:180px;">カテゴリ</th>
        <th>内容</th>
        <th style="width:90px;">優先度</th>
      </tr>
    </thead>
    <tbody>{rows_html}</tbody>
  </table>

  <p class="footer">ERラボ フィードバック自動チェックシステム — 完全無料・キーワード分類</p>
</body>
</html>"""


def main():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] フィードバックチェック開始")

    if SHEET_CSV_URL == "ここにCSV公開URLを貼る":
        print("⚠ SHEET_CSV_URL が未設定です。feedback_setup_guide.txt を参照してください。")
        return

    if not check_internet():
        print("⚠ インターネット未接続。スキップします。")
        return

    print("✓ インターネット接続OK")

    try:
        rows = fetch_csv(SHEET_CSV_URL)
    except Exception as e:
        print(f"✗ CSV取得失敗: {e}")
        return

    if len(rows) <= 1:
        print("新しいフィードバックはありません（0件）")
        return

    state = load_state()
    last_row = state.get("last_row", 1)
    new_rows = rows[last_row:]  # ヘッダー除いた新着行

    all_items = []
    new_items = []

    for i, row in enumerate(rows[1:], start=1):
        if not row:
            continue
        timestamp = row[0] if len(row) > 0 else ""
        text = row[1] if len(row) > 1 else ""
        rule = classify(text)
        item = {"timestamp": timestamp, "text": text, "rule": rule}
        all_items.append(item)
        if i > last_row - 1:
            new_items.append(item)

    # HIGH優先度を先頭に並べ替え
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    new_items.sort(key=lambda x: priority_order[x["rule"]["priority"]])

    html = build_html(new_items, all_items)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    state["last_row"] = len(rows)
    save_state(state)

    print(f"✓ 新着: {len(new_items)}件 / 累計: {len(all_items)}件")
    print(f"✓ レポート出力: {OUTPUT_HTML}")

    webbrowser.open(f"file:///{OUTPUT_HTML.replace(os.sep, '/')}")


if __name__ == "__main__":
    main()
