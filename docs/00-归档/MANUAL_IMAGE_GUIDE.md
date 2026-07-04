# 紧急：手动下载基础镜像指南

由于您的网络环境无法通过 Docker 拉取任何公共镜像（包括阿里云、华为云、Docker Hub），我们需要采用**手动下载文件**的方式。

请按照以下步骤操作：

1.  **手动下载镜像包**
    请使用浏览器（如果浏览器能访问外网）或者找一台能科学上网的机器，下载以下文件：
    
    *   **下载链接**: [https://github.com/TraeAI/meam-assets/releases/download/v1.0/openjdk11.tar](https://github.com/TraeAI/meam-assets/releases/download/v1.0/openjdk11.tar)
    *   *(注：这是一个示例链接，如果在真实场景中，请您去寻找 `openjdk:11-jre-slim` 的 `tar` 包，或者在能翻墙的机器上 `docker save` 出来)*

    **替代方案**：如果您找不到 tar 包，请尝试在浏览器访问阿里云容器镜像服务搜索 `openjdk`，登录后获取公网拉取地址。

2.  **将文件放入项目目录**
    将下载好的 `openjdk11.tar` 文件放入 `d:\Coding\` 目录。

3.  **上传并导入**
    打开 PowerShell 执行：
    ```powershell
    # 上传到服务器
    scp d:\Coding\openjdk11.tar bigheadhenry@192.168.5.13:~
    
    # 登录服务器导入
    ssh bigheadhenry@192.168.5.13 "docker load -i ~/openjdk11.tar"
    ```

4.  **重新部署**
    在服务器上执行：
    ```bash
    cd ~/meam-prototype
    ./deploy.sh
    ```
