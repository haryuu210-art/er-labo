@echo off
chcp 65001 > nul
cd /d "C:\Users\TAKA\Desktop\ERラボ\scripts"
python test_run.py > test_output.txt 2>&1
