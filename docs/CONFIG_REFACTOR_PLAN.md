# CONFIG_REFACTOR_PLAN

> 归档说明：这份文件记录的是早期的配置整理思路，当前可执行的部署与配置说明已经迁移到 [`SETUP_AND_DEPLOYMENT.md`](SETUP_AND_DEPLOYMENT.md)。
>
> 新增环境变量、启动步骤和部署约束，以新文档为准。这里不再作为日常维护入口。

## 历史背景

这份计划最初只想做一件事：把 `.env.example` 和 `docker-compose.yml` 之间的配置来源理顺，避免把宿主机路径、对外 URL 和容器内路径混在一起。

现在这件事已经在代码和文档里落实了，所以这份文件仅保留归档价值。
