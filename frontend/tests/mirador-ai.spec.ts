import { expect, test } from '@playwright/test';

const systemAdminAuthContext = {
  user_id: 'system_admin',
  display_name: 'System Admin',
  roles: ['system_admin'],
  permissions: [
    'dashboard.view',
    'image.view',
    'image.edit',
    'image.delete',
    'image.upload',
    'image.ingest_review',
    'three_d.view',
    'three_d.edit',
    'three_d.upload',
    'platform.view',
    'application.create',
    'application.view_all',
    'application.review',
    'application.export',
    'system.manage',
  ],
  collection_scope: [],
  auth_mode: 'session',
};

const availableUsers = [
  {
    username: 'system_admin',
    display_name: 'System Admin',
    roles: [{ key: 'system_admin', label: 'System Admin' }],
    collection_scope: [],
  },
];

const assets = [
  {
    id: 1,
    filename: 'test_image.jpg',
    file_size: 1024 * 1024 * 2.5,
    mime_type: 'image/jpeg',
    status: 'ready',
    created_at: '2024-01-01 10:00:00',
  },
];

const manifest = {
  '@context': 'http://iiif.io/api/presentation/3/context.json',
  id: 'http://localhost:3000/api/iiif/1/manifest',
  type: 'Manifest',
  label: { en: ['test_image.jpg'] },
  metadata: [
    { label: { en: ['Asset ID'] }, value: { none: ['1'] } },
    { label: { en: ['Resource ID'] }, value: { none: ['image_2d:1'] } },
    { label: { en: ['Title'] }, value: { none: ['test_image.jpg'] } },
    { label: { en: ['Object Number'] }, value: { none: ['OBJ-1'] } },
  ],
  items: [
    {
      id: 'http://localhost:3000/api/iiif/1/canvas/1',
      type: 'Canvas',
      height: 1000,
      width: 1000,
      items: [
        {
          id: 'http://localhost:3000/api/iiif/1/page/1',
          type: 'AnnotationPage',
          items: [
            {
              id: 'http://localhost:3000/api/iiif/1/annotation/1',
              type: 'Annotation',
              motivation: 'painting',
              target: 'http://localhost:3000/api/iiif/1/canvas/1',
              body: {
                id: 'http://localhost:3000/iiif/2/test_image/full/full/0/default.jpg',
                type: 'Image',
                format: 'image/jpeg',
                height: 1000,
                width: 1000,
                service: [
                  {
                    id: 'http://localhost:3000/iiif/2/test_image',
                    type: 'ImageService3',
                    profile: 'level2',
                  },
                ],
              },
            },
          ],
        },
      ],
    },
  ],
};

const transparentPng = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aUeUAAAAASUVORK5CYII=',
  'base64',
);

async function bootstrapMiradorAi(page) {
  await page.addInitScript((token) => {
    window.localStorage.setItem('mdams.auth.token', token);
  }, 'test-token');

  await page.route('**/api/auth/users', async (route) => {
    await route.fulfill({ json: availableUsers });
  });

  await page.route('**/api/auth/context', async (route) => {
    await route.fulfill({ json: systemAdminAuthContext });
  });

  await page.route('**/api/auth/logout', async (route) => {
    await route.fulfill({ json: { status: 'ok' } });
  });

  await page.route('**/api/applications**', async (route) => {
    await route.fulfill({ json: [] });
  });

  await page.route('**/api/assets', async (route) => {
    await route.fulfill({ json: assets });
  });

  await page.route('**/api/assets/1/preview', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'image/png',
      body: transparentPng,
    });
  });

  await page.route('**/api/iiif/1/manifest', async (route) => {
    await route.fulfill({ json: manifest });
  });

  await page.route('**/iiif/2/test_image/info.json', async (route) => {
    await route.fulfill({
      json: {
        '@context': 'http://iiif.io/api/image/3/context.json',
        id: 'http://localhost:3000/iiif/2/test_image',
        type: 'ImageService3',
        protocol: 'http://iiif.io/api/image',
        width: 1000,
        height: 1000,
        profile: 'level2',
      },
    });
  });

  await page.route('**/iiif/2/test_image/**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'image/png',
      body: transparentPng,
    });
  });

  await page.route('**/api/ai/mirador/interpret', async (route) => {
    const body = route.request().postDataJSON() as { prompt?: string } | undefined;
    await route.fulfill({
      json: {
        action: 'open_compare',
        assistant_message: '我找到两张可对比的图像，请确认后打开对比。',
        requires_confirmation: true,
        search_query: 'blue vase',
        compare_mode: 'side_by_side',
        search_results: [
          {
            asset_id: 1,
            title: 'Blue Vase',
            manifest_url: 'http://localhost:3000/api/iiif/1/manifest',
            resource_id: 'image_2d:1',
            object_number: 'OBJ-1',
            filename: 'test_image.jpg',
            score: 2,
            reasons: ['blue', 'vase'],
          },
          {
            asset_id: 2,
            title: 'Blue Vase Study',
            manifest_url: 'http://localhost:3000/api/iiif/2/manifest',
            resource_id: 'image_2d:2',
            object_number: 'OBJ-2',
            filename: 'blue_vase_study.jpg',
            score: 1.8,
            reasons: ['blue', 'vase'],
          },
        ],
        target_asset: {
          asset_id: 1,
          title: 'Blue Vase',
          manifest_url: 'http://localhost:3000/api/iiif/1/manifest',
          resource_id: 'image_2d:1',
          object_number: 'OBJ-1',
          filename: 'test_image.jpg',
          score: 2,
          reasons: ['blue', 'vase'],
        },
        prompt_echo: body?.prompt || null,
      },
    });
  });
}

test.describe('Mirador AI panel', () => {
  test.beforeEach(async ({ page }) => {
    await bootstrapMiradorAi(page);
    await page.goto('/', { waitUntil: 'domcontentloaded' });
  });

  test('opens the AI panel and shows a confirmable compare plan', async ({ page }) => {
    await expect(page.getByTestId('assets-table')).toBeVisible();
    await page.getByTestId('asset-preview-button-1').click();

    await expect(page.getByTestId('mirador-ai-panel')).toBeVisible();
    await expect(page.getByText('Mirador Viewer')).toBeVisible();

    await page.getByTestId('mirador-ai-prompt').fill('帮我找一张类似的图并打开对比');
    await page.getByTestId('mirador-ai-send').click();

    await expect(page.getByTestId('mirador-ai-plan')).toBeVisible({ timeout: 15000 });
    await expect(page.getByTestId('mirador-ai-plan')).toContainText('blue vase');
    await expect(page.getByTestId('mirador-ai-candidates')).toBeVisible({ timeout: 15000 });
    await expect(page.getByTestId('mirador-ai-confirmation')).toContainText('Blue Vase', { timeout: 15000 });
    await expect(page.getByTestId('mirador-ai-confirm')).toBeVisible({ timeout: 15000 });

    await page.getByTestId('mirador-ai-candidate-2').click();
    await expect(page.getByTestId('mirador-ai-confirmation')).toContainText('Blue Vase Study', { timeout: 15000 });
  });
});
