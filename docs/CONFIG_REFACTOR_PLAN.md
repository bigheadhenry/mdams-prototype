# 配置重构说明（归档）

这份文档已经不再作为当前主入口使用。

当前配置说明和部署入口请以以下文档为准：

- [`SETUP_AND_DEPLOYMENT.md`](SETUP_AND_DEPLOYMENT.md)
- [`README.md`](../README.md)

当前仓库的配置原则已经收敛为：

- 尽量只通过 `.env` 调整
- 容器内路径保持稳定
- 对外 URL 通过环境变量统一控制