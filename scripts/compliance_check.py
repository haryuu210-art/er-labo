# -*- coding: utf-8 -*-
"""
compliance_check.py
自動化スクリプト実行前のコンプライアンスチェック。
違反リスクのある操作を自動でブロックする。
"""

import os
import json
import urllib.request
import re
from datetime import datetime, date

COMPLIANCE_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "compliance_log.json")

# ===== 制限値（COMPLIANCE.mdと同期） =====
MAX_SCRAPE_PER_DAY = 50        # asataminへの1日最大リクエスト数
SCRAPE_INTERVAL_SEC = 3        # スクレイピング間隔（秒）
MAX_GEMINI_PER_DAY = 100       # Gemini APIの1日自主制限

# robots.txtで禁止されているパス
ROBOTS_DISALLOW = {
    "asatamin-eternalreturn.com": ["/wp-admin/"],
    "playeternalreturn.com": [],
}

# 絶対に触らないドメイン（著作権・規約上リスクが高い、または利用禁止に設定）
BLOCKED_DOMAINS = [
    "store.steampowered.com",
    "playeternalreturn.com/api",
    "asatamin-eternalreturn.com",   # 利用禁止（独自リサーチ方式に移行）
    "w.atwiki.jp/erjp",             # 利用禁止（独自リサーチ方式に移行）
]


def load_log():
    if os.path.exists(COMPLIANCE_LOG):
        with open(COMPLIANCE_LOG, encoding="utf-8") as f:
            return json.load(f)
    return {"scrape_counts": {}, "gemini_counts": {}, "violations": []}


def save_log(log):
    with open(COMPLIANCE_LOG, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def today():
    return str(date.today())


def check_robots_txt(url):
    """URLがrobots.txtのDisallowに該当しないか確認"""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    domain = parsed.netloc
    path = parsed.path

    disallowed = ROBOTS_DISALLOW.get(domain, [])
    for d in disallowed:
        if path.startswith(d):
            return False, f"robots.txt違反: {domain}{d} はDisallowされています"

    return True, "OK"


def check_blocked_domain(url):
    """ブロック対象ドメインでないか確認"""
    for blocked in BLOCKED_DOMAINS:
        if blocked in url:
            return False, f"ブロック対象URL: {url}"
    return True, "OK"


def can_scrape(url):
    """
    スクレイピング可否チェック。
    False + 理由 を返す場合はスクレイピングを中止すること。
    """
    # robots.txtチェック
    ok, reason = check_robots_txt(url)
    if not ok:
        log_violation("scrape_blocked", reason)
        return False, reason

    # ブロックドメインチェック
    ok, reason = check_blocked_domain(url)
    if not ok:
        log_violation("scrape_blocked", reason)
        return False, reason

    # 1日あたりリクエスト数チェック
    log = load_log()
    today_count = log["scrape_counts"].get(today(), 0)
    if today_count >= MAX_SCRAPE_PER_DAY:
        reason = f"1日の上限({MAX_SCRAPE_PER_DAY}回)に達しました。明日再試行してください。"
        log_violation("scrape_limit", reason)
        return False, reason

    # カウントアップ
    log["scrape_counts"][today()] = today_count + 1
    save_log(log)
    return True, "OK"


def can_use_gemini():
    """Gemini API呼び出し可否チェック"""
    log = load_log()
    today_count = log["gemini_counts"].get(today(), 0)
    if today_count >= MAX_GEMINI_PER_DAY:
        reason = f"Gemini 1日の自主制限({MAX_GEMINI_PER_DAY}回)に達しました。"
        log_violation("gemini_limit", reason)
        return False, reason

    log["gemini_counts"][today()] = today_count + 1
    save_log(log)
    return True, "OK"


def log_violation(violation_type, reason):
    """違反ログを記録"""
    log = load_log()
    log["violations"].append({
        "type": violation_type,
        "reason": reason,
        "timestamp": datetime.now().isoformat(),
    })
    save_log(log)
    print(f"[COMPLIANCE] {violation_type}: {reason}")


def check_content_before_publish(text):
    """
    サイトに掲載する前のコンテンツチェック。
    著作権リスクのあるテキストパターンを検出する。
    """
    warnings = []

    # asataminのURLが含まれていないか（転載チェック）
    if "asatamin-eternalreturn.com" in text and len(text) > 200:
        warnings.append("asataminのURLを含む長文テキストが検出されました。転載でないか確認してください。")

    # 「攻略サイト参照」など出典明記なしの転用
    if len(text) > 300 and "出典" not in text and "参考" not in text:
        warnings.append("200文字超のテキストに出典が明記されていません。AI生成コンテンツの場合はタグを付けてください。")

    return warnings


def get_today_stats():
    """今日の利用状況を表示"""
    log = load_log()
    scrape = log["scrape_counts"].get(today(), 0)
    gemini = log["gemini_counts"].get(today(), 0)
    print(f"[今日の利用状況] スクレイピング: {scrape}/{MAX_SCRAPE_PER_DAY}  Gemini: {gemini}/{MAX_GEMINI_PER_DAY}")
    return scrape, gemini


if __name__ == "__main__":
    get_today_stats()
