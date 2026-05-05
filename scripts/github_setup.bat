@echo off
echo ===================================
echo  ERラボ GitHub セットアップ
echo ===================================
echo.
echo 【事前準備】
echo 1. https://github.com でアカウント作成（無料）
echo 2. 新しいリポジトリを作成（名前例: erlab）
echo    ※ "Private" を選択すると非公開になります
echo 3. このスクリプトを実行
echo.
set /p REPO_URL="GitHubリポジトリのURLを入力 (例: https://github.com/yourname/erlab.git): "
echo.
cd /d "C:\Users\TAKA\Desktop\ERラボ"
git remote add origin %REPO_URL%
git branch -M main
git push -u origin main
echo.
echo 完了！以降は git push で同期できます。
pause
