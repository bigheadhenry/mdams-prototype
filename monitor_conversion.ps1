# Monitor Server Logs for PSB Conversion
# 监控服务器上的 Celery 和 Backend 日志，用于观察转码进度

$ServerIP = "192.168.5.13"
$User = "bigheadhenry"

Write-Host "Connecting to $ServerIP to monitor Celery worker logs..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop monitoring." -ForegroundColor Yellow

ssh -t $User@$ServerIP "cd ~/meam-prototype && docker compose logs -f --tail=10 celery_worker backend"
