# ERラボ フィードバックチェック タスクスケジューラ登録
$ScriptPath = "C:\Users\TAKA\Desktop\ERラボ\scripts\check_feedback.py"
$TaskName   = "ERLab_FeedbackCheck"
$PythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source

if (-not $PythonPath) {
    Write-Host "ERROR: Python not found." -ForegroundColor Red
    exit 1
}

Write-Host "Python: $PythonPath" -ForegroundColor Cyan

$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Removed existing task." -ForegroundColor Yellow
}

$Action = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument "`"$ScriptPath`"" `
    -WorkingDirectory (Split-Path $ScriptPath)

$Trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$Trigger.Delay = "PT30M"

$Settings = New-ScheduledTaskSettingsSet `
    -RunOnlyIfNetworkAvailable `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 5) `
    -MultipleInstances IgnoreNew

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "ERLab feedback auto check" `
    -RunLevel Limited | Out-Null

Write-Host ""
Write-Host "OK: Task registered successfully!" -ForegroundColor Green
Write-Host "Task name : $TaskName" -ForegroundColor Cyan
Write-Host "Trigger   : 30 min after login + network required" -ForegroundColor Cyan
Write-Host "Script    : $ScriptPath" -ForegroundColor Cyan
