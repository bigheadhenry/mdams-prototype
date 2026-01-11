# MEAM Prototype - Image Preparation Script
# 自动拉取、导出并上传镜像到服务器

$ServerIP = "192.168.5.13"
$User = "bigheadhenry"

Write-Host "1. Checking Docker..." -ForegroundColor Cyan
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker is not installed or not in PATH. Please install Docker Desktop first."
    exit 1
}

Write-Host "2. Pulling OpenJDK 11 Image..." -ForegroundColor Cyan

# Try multiple mirrors (Switching to a known working personal mirror on Aliyun as last resort)
$mirrors = @(
    "registry.cn-hangzhou.aliyuncs.com/bigheadhenry/openjdk:11-jre-slim",
    "swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/library/openjdk:11-jre-slim"
)

$success = $false
foreach ($img in $mirrors) {
    Write-Host "   Trying to pull $img ..." -ForegroundColor Yellow
    docker pull $img
    if ($LASTEXITCODE -eq 0) {
        # Retag to standard name expected by Dockerfile
        docker tag $img openjdk:11-jre-slim
        $success = $true
        break
    }
}

if (-not $success) {
    Write-Error "Failed to pull OpenJDK image from all tried mirrors. Please check your network or VPN."
    exit 1
}

Write-Host "3. Saving Image to file (openjdk11.tar)..." -ForegroundColor Cyan
docker save -o openjdk11.tar openjdk:11-jre-slim
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "4. Uploading Image to Server ($ServerIP)..." -ForegroundColor Cyan
Write-Host "   (Please enter server password if prompted)" -ForegroundColor Yellow
scp openjdk11.tar "${User}@${ServerIP}:~"
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "5. Uploading Config Files..." -ForegroundColor Cyan
scp meam-prototype\cantaloupe\Dockerfile "${User}@${ServerIP}:~/meam-prototype/cantaloupe/"

Write-Host ""
Write-Host "Success! Now please go to the server and run:" -ForegroundColor Green
Write-Host "   docker load -i ~/openjdk11.tar" -ForegroundColor White
Write-Host "   cd ~/meam-prototype && ./deploy.sh" -ForegroundColor White
Write-Host ""
Read-Host -Prompt "Press Enter to exit"
