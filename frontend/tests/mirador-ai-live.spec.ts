import { expect, test } from '@playwright/test';

const AUTH_TOKEN_KEY = 'mdams.auth.token';
const LIVE_ENABLED = process.env.LIVE_MIRADOR_AI === '1';

test.describe('Mirador AI live route', () => {
  test('runs through real frontend, backend, IIIF, and AI compare planning', async ({ page, request }) => {
    test.skip(!LIVE_ENABLED, 'Set LIVE_MIRADOR_AI=1 after seeding AI_SMOKE_TEST assets.');

    const loginResponse = await request.post('/api/auth/login', {
      data: { username: 'system_admin', password: 'mdams123' },
    });
    expect(loginResponse.ok()).toBeTruthy();
    const loginBody = (await loginResponse.json()) as { token: string };
    expect(loginBody.token).toBeTruthy();

    await page.addInitScript(
      ({ key, token }) => window.localStorage.setItem(key, token),
      { key: AUTH_TOKEN_KEY, token: loginBody.token },
    );

    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('assets-table')).toBeVisible({ timeout: 20000 });
    await expect(page.getByTestId('asset-preview-button-900001')).toBeVisible({ timeout: 20000 });
    await page.getByTestId('asset-preview-button-900001').click();

    await expect(page.getByTestId('mirador-ai-panel')).toBeVisible({ timeout: 30000 });
    await expect(page.getByTestId('mirador-ai-send')).toBeEnabled({ timeout: 30000 });

    await page.getByTestId('mirador-ai-prompt').fill('\u627e\u4e00\u5f20 blue vase \u7c7b\u4f3c\u56fe\u5e76\u6253\u5f00\u6bd4\u8f83');
    await page.getByTestId('mirador-ai-send').click();

    await expect(page.getByTestId('mirador-ai-plan')).toBeVisible({ timeout: 30000 });
    await expect(page.getByTestId('mirador-ai-plan')).toContainText('mirador.window.open_compare');
    await expect(page.getByTestId('mirador-ai-candidates')).toContainText('AI_SMOKE_TEST Blue Vase Study', {
      timeout: 30000,
    });
    await expect(page.getByTestId('mirador-ai-confirmation')).toContainText('AI_SMOKE_TEST Blue Vase Study', {
      timeout: 30000,
    });

    await page.getByTestId('mirador-ai-confirm').click();
    await expect(page.getByTestId('mirador-ai-error')).toHaveCount(0, { timeout: 30000 });
    await expect(page.getByText('已打开比较目标')).toBeVisible({ timeout: 30000 });
    await expect(page.getByText('2 个窗口', { exact: true })).toBeVisible({ timeout: 30000 });
  });
});
