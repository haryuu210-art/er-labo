# ERラボ 自動更新スクリプト

## 初回セットアップ

### 1. Gemini APIキーを取得（無料）
1. https://aistudio.google.com/apikey にアクセス
2. 「APIキーを作成」をクリック
3. `.env.example` を `.env` にコピーしてキーを貼り付け

```
scripts/.env.example → scripts/.env
GEMINI_API_KEY=AIza...（取得したキー）
```

### 2. 動作確認
```bash
cd scripts
python check_update.py        # 公式サイトの確認テスト
python research_character.py --en Coraline --jp コラライン  # Geminiテスト
```

---

## 使い方

### 通常実行（アップデートを自動検知）
```bash
python auto_update.py
```

### 手動でキャラを1人追加
```bash
python auto_update.py --add-char Blair ブレア
```

### 画像だけ個別ダウンロード
```bash
python download_fankit.py --name Blair
```

---

## 定期自動実行（Windowsタスクスケジューラ）

1. スタートメニュー →「タスクスケジューラ」を検索
2. 「基本タスクの作成」
3. トリガー: 毎週（パッチは隔週が多い）
4. 操作: プログラムの開始
   - プログラム: `python`
   - 引数: `C:\Users\TAKA\Desktop\ERラボ\scripts\auto_update.py`

---

## 無料枠の制限

| サービス | 制限 | 用途 |
|---------|------|------|
| Gemini 2.0 Flash | 1,500req/日 / 15req/分 | キャラ情報リサーチ |
| Google Drive | 無制限（公開フォルダ） | 画像DL |
| 公式サイト | 制限なし | パッチ確認 |

月1〜2回のアップデートなら無料枠の1%以下で収まります。

---

## ファイル構成

```
scripts/
├── auto_update.py        # メインパイプライン
├── check_update.py       # パッチノート確認
├── download_fankit.py    # 画像ダウンロード
├── research_character.py # Geminiリサーチ
├── .env                  # APIキー（自分で作成）
├── .env.example          # テンプレート
├── last_state.json       # 最終確認状態（自動生成）
├── fankit_state.json     # DL済み画像管理（自動生成）
└── update_log.json       # 更新履歴（自動生成）
```
