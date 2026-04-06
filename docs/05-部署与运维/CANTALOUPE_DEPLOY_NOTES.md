# Cantaloupe IIIF Server 部署与调试记录

本文档记录了在 Docker 环境下部署 Cantaloupe IIIF 图像服务器时遇到的关键问题及其解决方案，特别是关于路径配置、反向代理和构建缓存的陷阱。

## 1. Cantaloupe 启动卡死问题

### 现象
容器启动后长时间卡在 `Loading config file: /etc/cantaloupe.properties`，无后续日志输出。

### 原因
Cantaloupe（及 Java 应用）在启动时需要初始化随机数生成器。在容器环境或某些服务器上，`/dev/random` 的熵池可能不足，导致 Java 进程阻塞等待。此外，文件日志的 I/O 锁也可能导致死锁。

### 解决方案
1.  **增加熵源**：在 `docker-compose.yml` 中将主机的 `/dev/urandom` 挂载到容器的 `/dev/random`。
    ```yaml
    volumes:
      - /dev/urandom:/dev/random:ro
    ```
    或者在 JVM 启动参数中添加 `-Djava.security.egd=file:/dev/./urandom`。

2.  **禁用文件日志**：将日志仅输出到控制台 (STDOUT)，避免文件系统 I/O 锁。
    修改 `cantaloupe.properties`：
    ```properties
    log.application.FileAppender.enabled = false
    log.application.ConsoleAppender.enabled = true
    ```

---

## 2. Nginx 反向代理与路径重写问题 (502 & 404)

### 现象
- 访问 `http://host:3000/iiif/2/` 返回 502 Bad Gateway。
- 访问后被重定向到 `http://host:3000/iiif/2/iiif/2/` (路径重复)。
- 图片信息 JSON 中的 `@id` 包含重复路径。

### 原因
1.  **Nginx 解析失败**：Nginx 启动时如果上游主机名（如 `cantaloupe`）不可解析或 IP 变动，会导致 502。
    *   **修复**：使用 Docker 容器名 `meam-cantaloupe` 并确保在同一网络中；重启 Nginx 容器。
2.  **`proxy_pass` 路径尾随斜杠陷阱**：
    *   错误配置：`proxy_pass http://cantaloupe:8182/iiif/2/;` —— Nginx 会剥离 `/iiif/2/`，导致发给 Cantaloupe 的请求路径缺失。
    *   **正确配置**：
        ```nginx
        location /iiif/2/ {
            proxy_pass http://meam-cantaloupe:8182; # 不带 URI，原样转发
            proxy_set_header Host $http_host;       # 传递带端口的 Host
        }
        ```
3.  **Base URI 配置错误**：Cantaloupe 在生成 `@id` 时，会将 `base_uri` 与解析出的 ID 拼接。如果 `base_uri` 包含了 `/iiif/2`，而 Cantaloupe 解析出的 ID 也包含了 `/iiif/2`（因为它认为自己部署在根路径），就会导致路径重复。

---

## 3. Base URI 与 ID 解析逻辑

这是最令人困惑的部分。

### 场景
- Nginx 转发路径：`/iiif/2/image.jpg` -> Cantaloupe 收到的路径：`/iiif/2/image.jpg`
- Cantaloupe API Endpoint：默认配置为 `/iiif/2`。

### 错误配置
```properties
base_uri = http://host:3000/iiif/2
```
在此配置下，Cantaloupe 似乎认为 ID 是 `iiif/2/image.jpg`（包含了路径前缀），拼接后变成 `http://host:3000/iiif/2/iiif/2/image.jpg`。

### 正确配置
```properties
# Base URI 设置为根域名，不带路径后缀
base_uri = http://192.168.5.13:3000
```
或者，如果不想硬编码 IP，可以注释掉 `base_uri`，让 Cantaloupe 根据 `Host` 头自动检测。但必须确保 Nginx 传递了正确的 `Host`（包含端口）。

**最终采用的方案**：
在 `cantaloupe.properties` 中显式设置 `base_uri` 为根域名（含端口），配合 Nginx 的原样转发。

---

## 4. Docker 构建缓存的陷阱

### 现象
修改了 `cantaloupe.properties` 并推送到服务器，但部署后配置似乎未生效（例如 `base_uri` 依然是旧值）。

### 原因
Dockerfile 中的 `COPY cantaloupe.properties ...` 指令被 Docker 缓存了。即使文件内容变了，如果 Git 检出时的元数据导致 Docker 认为层未变化，它就会直接使用旧的镜像层。

### 解决方案
1.  **修改 Dockerfile**：在 `COPY` 指令前添加注释或空行，强制破坏缓存。
    ```dockerfile
    # Force rebuild 2026-01-05
    COPY cantaloupe.properties /etc/cantaloupe.properties
    ```
2.  **强制无缓存构建**：
    ```bash
    docker-compose build --no-cache cantaloupe
    ```
3.  **手动验证**：进入容器检查文件内容。
    ```bash
    docker exec meam-cantaloupe cat /etc/cantaloupe.properties
    ```

## 总结最佳实践

1.  **Java 容器**：务必挂载 `/dev/urandom`。
2.  **Nginx 反代**：`proxy_pass` 尽量不带 URI 后缀（原样转发），并传递 `$http_host`。
3.  **Cantaloupe**：小心设置 `base_uri`，避免与 Nginx 的路径重写叠加。
4.  **调试**：使用 `curl -v` 在服务器内部直接测试容器端口，隔离防火墙和浏览器缓存干扰。
