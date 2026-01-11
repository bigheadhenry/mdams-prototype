# Windows 安装 Docker Desktop 指南

本指南将帮助您在 Windows 开发机上安装 Docker Desktop，以便下载并导出镜像传输给实验室服务器。

## 1. 检查系统要求

*   **操作系统**: Windows 10 (Build 19044 或更高) 或 Windows 11。
*   **虚拟化**: 必须在 BIOS 中开启虚拟化 (VT-x / AMD-V)。
*   **WSL 2**: 推荐使用 WSL 2 后端（性能更好）。

## 2. 安装步骤

### 第一步：开启 WSL 2 (如果尚未开启)
以**管理员身份**打开 PowerShell，运行以下命令：
```powershell
wsl --install
```
*   如果提示已安装，可以直接跳过。
*   安装完成后，**重启电脑**。

### 第二步：下载并安装 Docker Desktop
1.  前往官网下载安装包：[Docker Desktop Installer.exe](https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe)
2.  双击运行安装程序。
3.  在配置界面，确保勾选 **"Use WSL 2 instead of Hyper-V"** (推荐)。
4.  等待安装完成，点击 "Close and restart"（可能需要再次重启电脑）。

### 第三步：启动并验证
1.  重启后，Docker Desktop 会自动启动（如果没有，请在开始菜单搜索并运行）。
2.  同意服务条款 (Accept Terms)。
3.  等待左下角的鲸鱼图标变绿（状态显示 `Engine running`）。
4.  打开 PowerShell，输入以下命令验证：
    ```powershell
    docker --version
    docker run hello-world
    ```
    如果看到 "Hello from Docker!" 的输出，说明安装成功。

## 3. 使用 Docker 下载并导出镜像

安装成功后，您就可以执行之前的操作来救急服务器了：

1.  **拉取 OpenJDK 镜像**：
    ```powershell
    docker pull openjdk:11-jre-slim
    ```

2.  **导出为文件**：
    ```powershell
    # 导出到 D 盘根目录或当前目录
    docker save -o d:\Coding\openjdk11.tar openjdk:11-jre-slim
    ```

3.  **上传到服务器**：
    ```powershell
    scp d:\Coding\openjdk11.tar bigheadhenry@192.168.5.13:~
    ```
