我建议使用 **Playwright** 来实现前端的自动化测试。

### 为什么选择 Playwright？
1.  **速度快且稳定**：它是目前最流行的 E2E（端到端）测试框架，比 Selenium 和 Cypress 更快。
2.  **支持 React**：完美支持 React 和 Vite 项目。
3.  **自动等待**：不需要手动编写 sleep/wait，它会自动等待元素出现。
4.  **调试方便**：提供 UI 模式和代码生成器。

### 实施计划
我们将按照以下步骤在您的 `frontend` 项目中集成 Playwright：

1.  **安装依赖**：
    *   在 `frontend` 目录下安装 `@playwright/test`。
2.  **配置 Playwright**：
    *   创建 `frontend/playwright.config.ts` 配置文件。
    *   配置它自动启动 Vite 开发服务器 (`npm run dev`)，这样测试时不需要您手动启动项目。
3.  **编写测试用例**：
    *   创建 `frontend/tests/dashboard.spec.ts`。
    *   编写测试脚本：
        *   验证页面是否能正常加载。
        *   验证 "Dashboard" 菜单是否存在。
        *   验证 "Upload New Asset" 按钮是否可见。
        *   验证数据统计卡片是否显示。
4.  **添加运行脚本**：
    *   在 `package.json` 中添加 `test` 命令。

确认后，我将为您执行上述操作。