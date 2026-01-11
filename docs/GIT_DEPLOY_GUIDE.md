# Git Push-to-Deploy Guide

This project uses a **Git Push-to-Deploy** workflow to synchronize code between the local development machine, GitHub, and the local laboratory server.

## 1. Environment Overview

- **Development Machine**: Windows (Powershell)
- **Code Hosting**: GitHub (`origin`)
- **Production Server**: Ubuntu Server @ `192.168.5.13` (`production`)
- **User**: `bigheadhenry`

## 2. Repositories

| Remote Name  | URL | Purpose |
|Data Transfer | --- | --- |
| `origin`     | `https://github.com/bigheadhenry/mdams-prototype.git` | Source Code Management & Backup |
| `production` | `ssh://bigheadhenry@192.168.5.13/home/bigheadhenry/repos/meam.git` | Deployment Trigger |

## 3. Workflow

### Step 1: Develop & Commit
Make changes locally and commit them.

```powershell
git add .
git commit -m "feat: your new feature"
```

### Step 2: Push to GitHub (Backup)
Push your changes to the cloud.

```powershell
git push origin main
```

### Step 3: Deploy to Server
Push to the local server to trigger the deployment.

**Important**: The server expects the `master` branch for deployment (configured in the post-receive hook). Since we develop on `main`, mapping is required.

```powershell
git push production main:master
```

> **What happens next?**
> 1. The code is pushed to the bare repository on the server.
> 2. A `post-receive` hook triggers.
> 3. The hook checks out the code to `~/meam-prototype`.
> 4. Docker Compose rebuilds and restarts the services automatically.

## 4. Setup Scripts

If you need to re-initialize the environment:

### Local Setup (Run on Windows)
Run `setup_git_local.ps1` to configure the `production` remote.

```powershell
.\setup_git_local.ps1
```

### Server Setup (Run on 192.168.5.13)
Copy `setup_git_server.sh` to the server and run it. This creates the bare repo and the deployment hook.

```bash
# On Server
chmod +x setup_git_server.sh
./setup_git_server.sh
```

## 5. Troubleshooting

- **Permission Denied**: Ensure your SSH public key (`id_rsa.pub`) is added to `~/.ssh/authorized_keys` on the server.
- **Hook Failures**: Check the deployment log on the server:
  ```bash
  tail -f /home/bigheadhenry/deploy.log
  ```
