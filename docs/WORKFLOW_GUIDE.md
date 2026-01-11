# MDAMS 开发与部署工作流指南 (Workflow Guide)

本文档详细说明了如何在 MDAMS 项目中进行日常开发、代码管理以及自动化部署。本项目采用了 **Git Push to Deploy** 模式，实现了类似 Heroku 的开发体验。

## 1. 核心概念

*   **本地开发环境 (Windows)**: 你的个人电脑，用于编写代码、运行测试。
*   **生产服务器 (Ubuntu N100)**: 运行实际服务的服务器 (192.168.5.13)。
*   **自动化部署**: 当你将代码推送到服务器的 Git 仓库时，服务器会自动触发构建和重启流程。

## 2. 日常开发流程

### 2.1 编写代码
在本地 VS Code 中正常进行代码修改、添加新功能或修复 Bug。

### 2.2 提交更改 (Commit)
当完成一个阶段的工作后，将更改提交到本地 Git 仓库：

```powershell
# 添加所有更改
git add .

# 提交并附带说明
git commit -m "✨ 新增: 图片上传格式验证功能"
```

### 2.3 部署到服务器 (Deploy)
将代码推送到服务器的 `production` 远程仓库。这一步会触发自动部署：

```powershell
git push production master
```

**观察部署日志**:
推送后，终端会实时显示服务器端的部署进度，包括：
1.  代码检出 (Checkout)
2.  Docker 镜像构建 (Build)
3.  服务重启 (Restart)

当看到以下信息时，表示部署完成：
```
remote: ===============================================
remote:    DEPLOYMENT SUCCESSFUL!
remote: ===============================================
```

### 2.4 查看效果
打开浏览器访问 [http://192.168.5.13:3000](http://192.168.5.13:3000) 即可看到最新改动。

## 3. 常用 Git 命令速查

| 场景 | 命令 | 说明 |
| :--- | :--- | :--- |
| **查看状态** | `git status` | 查看哪些文件被修改了 |
| **查看日志** | `git log` | 查看历史提交记录 |
| **撤销修改** | `git checkout -- <file>` | 丢弃工作区对文件的修改 |
| **拉取代码** | `git pull production master` | (仅当服务器有独立修改时) 从服务器同步代码 |

## 4. 故障排查 (Troubleshooting)

### 4.1 推送被拒绝 (Rejected)
如果提示 `updates were rejected because the remote contains work that you do not have locally`，说明服务器上可能有你本地没有的修改（极少情况）。

**解决办法**:
```powershell
# 强制覆盖服务器代码 (慎用，除非你确定本地代码是最新的)
git push -f production master
```

### 4.2 部署过程中失败
如果 `git push` 显示部署脚本执行出错（例如 Docker 构建失败）：

1.  **检查日志**: 仔细阅读终端返回的错误信息。
2.  **SSH 登录排查**:
    ```bash
    ssh bigheadhenry@192.168.5.13
    cd meam-prototype
    docker compose logs -f --tail=100  # 查看容器运行日志
    ```

### 4.3 重新触发部署
如果上次部署中断或需要重启服务，可以直接在服务器执行：

```bash
ssh bigheadhenry@192.168.5.13
cd meam-prototype
./deploy.sh
```

## 5. 数据质量控制 (Data Quality Control)

为了确保归档数据的纯净度和后续处理（如 IIIF 预览、格式转换）的成功率，系统在前端实现了严格的文件预检机制。

### 5.1 图层与编辑数据检测
在文件上传前，系统会自动解析文件头，检查是否包含未合并的图层或 Photoshop 编辑数据。

| 文件格式 | 检测逻辑 | 行为 | 原因 |
| :--- | :--- | :--- | :--- |
| **PSD / PSB** | 使用 `ag-psd` 解析文件结构，检查 `layers.length`。 | **警告弹窗** (用户可确认跳过) | 多图层文件体积巨大且可能导致预览渲染不一致。 |
| **TIFF** | 使用 `utif` 解析 IFD 链表，检查是否多页；同时检查是否包含 Tag `37724` (ImageSourceData)。 | **警告弹窗** (用户可确认跳过) | 即使是单页 TIFF，如果包含 Photoshop 图层数据，也会导致 ImageMagick/Libvips 处理时出现色彩异常或错误。 |

### 5.2 大文件处理
*   **< 1GB**: 执行上述完整的图层检测。
*   **> 1GB**: 跳过深度检测（避免浏览器卡顿），直接弹出非阻塞提示，建议用户确认已合并图层。

## 6. 目录结构说明

*   `setup_git_local.ps1`: Windows 本地 Git 初始化脚本（一次性）。
*   `setup_git_server.sh`: 服务器端 Git 仓库初始化脚本（一次性）。
*   `.gitignore`: 指定哪些文件不需要上传（如 node_modules, 临时文件）。
*   `deploy.sh`: 服务器端的实际部署逻辑脚本。

---
**Happy Coding! 🚀**
