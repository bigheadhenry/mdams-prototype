import { test, expect } from '@playwright/test';

const sourceDetail = {
  id: 1,
  identifier: 'asset-1',
  title: 'test_image.jpg',
  resource_type: 'image_2d_cultural_object',
  resource_type_label: '二维影像资源',
  status: 'ready',
  process_message: '文件已上传并完成基础登记。',
  created_at: '2024-01-01T10:00:00Z',
  file: {
    filename: 'test_image.jpg',
    file_path: '/uploads/test_image.jpg',
    actual_filename: 'test_image.jpg',
    file_size: 2097152,
    mime_type: 'image/jpeg',
  },
  status_info: {
    code: 'ready',
    label: '就绪',
    message: '可用于预览与下载',
    preview_ready: true,
    has_error: false,
  },
  lifecycle: [
    {
      step: 'object_created',
      label: '对象创建',
      status: 'done',
      status_label: '完成',
      description: '对象已创建',
      timestamp: '2024-01-01T10:00:00Z',
      evidence: 'upload',
    },
  ],
  process_timeline: [
    {
      step: 'object_created',
      label: '对象创建',
      status: 'done',
      status_label: '完成',
      description: '对象已创建',
    },
  ],
  structure: {
    summary: '主文件为当前入库图像文件。',
    primary_file: {
      role: 'primary',
      role_label: '主文件',
      filename: 'test_image.jpg',
      file_path: '/uploads/test_image.jpg',
      mime_type: 'image/jpeg',
      file_size: 2097152,
      actual_filename: 'test_image.jpg',
      is_current: true,
      is_original: true,
      same_as_primary: true,
      derivation_method: 'upload',
    },
    original_file: {
      role: 'original',
      role_label: '原始文件',
      filename: 'test_image.jpg',
      file_path: '/uploads/test_image.jpg',
      mime_type: 'image/jpeg',
      file_size: 2097152,
      actual_filename: 'test_image.jpg',
      is_current: true,
      is_original: true,
      same_as_primary: true,
      derivation_method: 'upload',
    },
    derivatives: [],
    packaging: {
      bagit_supported: true,
      bagit_note: '支持 BagIt 打包下载',
    },
  },
  technical_metadata: {
    width: 1000,
    height: 800,
    fixity_sha256: 'abc123',
    ingest_method: 'upload',
    conversion_method: 'none',
    original_file_path: '/uploads/test_image.jpg',
  },
  access: {
    manifest_url: '/api/iiif/1/manifest',
    preview_enabled: true,
  },
  access_paths: {
    manifest: {
      label: 'IIIF Manifest',
      url: '/api/iiif/1/manifest',
    },
    mirador_preview: {
      label: 'Mirador 预览',
      manifest_url: '/api/iiif/1/manifest',
      enabled: true,
    },
    preview_enabled: true,
  },
  outputs: {
    download_url: '/api/assets/1/download',
    download_bag_url: '/api/assets/1/download-bag',
  },
  output_actions: {
    download_current_file: {
      label: '下载原文件',
      url: '/api/assets/1/download',
    },
    download_bag: {
      label: '下载 BagIt',
      url: '/api/assets/1/download-bag',
    },
  },
};

const unifiedDetail = {
  id: 'image_2d:1',
  source_system: 'image_2d',
  source_id: '1',
  source_label: '二维影像子系统',
  title: 'test_image.jpg',
  resource_type: 'image_2d_cultural_object',
  status: 'ready',
  preview_enabled: true,
  manifest_url: '/api/iiif/1/manifest',
  detail_url: '/api/platform/resources/image_2d:1',
  updated_at: '2024-01-01T10:00:00Z',
  source_detail_url: '/api/assets/1',
  source_record: sourceDetail,
};

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('/api/assets', async (route) => {
      await route.fulfill({
        json: [
          {
            id: 1,
            filename: 'test_image.jpg',
            file_size: 1024 * 1024 * 2.5,
            mime_type: 'image/jpeg',
            status: 'ready',
            created_at: '2024-01-01 10:00:00',
          },
          {
            id: 2,
            filename: 'document.png',
            file_size: 1024 * 500,
            mime_type: 'image/png',
            status: 'processing',
            created_at: '2024-01-01 11:00:00',
          },
        ],
      });
    });

    await page.route('**/api/assets/1', async (route) => {
      await route.fulfill({ json: sourceDetail });
    });

    await page.route('**/api/platform/sources**', async (route) => {
      await route.fulfill({
        json: [
          {
            source_system: 'image_2d',
            source_label: '二维影像子系统',
            resource_type: 'image_2d_cultural_object',
            resource_count: 2,
            status: 'healthy',
            healthy: true,
            last_synced_at: '2024-01-01T12:00:00Z',
            entrypoint: '/api/assets',
          },
        ],
      });
    });

    await page.route('**/api/platform/resources**', async (route) => {
      const url = new URL(route.request().url());
      if (url.pathname.includes('/api/platform/resources/image_2d:1') || url.pathname.includes('/api/platform/resources/image_2d%3A1')) {
        await route.fulfill({ json: unifiedDetail });
        return;
      }
      const query = url.searchParams.get('q')?.toLowerCase() || '';
      const status = url.searchParams.get('status');
      const previewEnabled = url.searchParams.get('preview_enabled');
      const resourceType = url.searchParams.get('resource_type');
      const allResources = [
        unifiedDetail,
        {
          ...unifiedDetail,
          id: 'image_2d:2',
          source_id: '2',
          title: 'document.png',
          status: 'processing',
          preview_enabled: false,
          manifest_url: '/api/iiif/2/manifest',
          detail_url: '/api/platform/resources/image_2d:2',
          updated_at: '2024-01-01T11:00:00Z',
          source_detail_url: '/api/assets/2',
        },
      ];

      const filtered = allResources.filter((item) => {
        const matchesQuery = !query || [item.id, item.title, item.resource_type, item.source_id]
          .some((value) => value.toLowerCase().includes(query));
        const matchesStatus = !status || item.status === status;
        const matchesPreview = !previewEnabled
          || (previewEnabled === 'true' && item.preview_enabled)
          || (previewEnabled === 'false' && !item.preview_enabled);
        const matchesResourceType = !resourceType || item.resource_type === resourceType;
        return matchesQuery && matchesStatus && matchesPreview && matchesResourceType;
      });

      await route.fulfill({ json: filtered });
    });

    await page.goto('/');
  });

  test('should load the dashboard correctly', async ({ page }) => {
    await expect(page).toHaveTitle(/MEAM Prototype/);
    await expect(page.locator('table')).toBeVisible();
    await expect(page.locator('.ant-statistic-content-value').first()).toHaveText('2');
  });

  test('should display assets in the table', async ({ page }) => {
    await expect(page.getByText('test_image.jpg')).toBeVisible();
    await expect(page.getByText('document.png')).toBeVisible();
    await expect(page.getByText('READY')).toBeVisible();
    await expect(page.getByText('PROCESSING')).toBeVisible();
    await expect(page.locator('tbody tr')).toHaveCount(2);
  });

  test('should open unified resource directory', async ({ page }) => {
    await page.getByText('统一资源').click();
    await expect(page.getByText('统一资源目录')).toBeVisible();
    await expect(page.getByRole('cell', { name: 'test_image.jpg' })).toBeVisible();
    await expect(page.getByRole('cell', { name: 'image_2d:1' })).toBeVisible();
  });

  test('should search unified resources', async ({ page }) => {
    await page.getByText('统一资源').click();
    await page.getByPlaceholder('搜索标题、文件名、MIME 或资源 ID').fill('document');
    await page.keyboard.press('Enter');
    await expect(page.getByRole('cell', { name: 'document.png' })).toBeVisible();
    await expect(page.getByRole('cell', { name: 'test_image.jpg' })).toHaveCount(0);
  });

  test('should open unified detail page', async ({ page }) => {
    await page.getByText('统一资源').click();
    await page.getByRole('button', { name: '统一详情' }).first().click();
    await expect(page.getByRole('heading', { name: 'test_image.jpg' })).toBeVisible();
    await expect(page.getByText('二维影像子系统').first()).toBeVisible();
    await expect(page.getByRole('button', { name: '查看源详情' })).toBeVisible();
    await expect(page.getByText('生命周期')).toBeVisible();
    await page.screenshot({ path: 'unified-detail-layout.png', fullPage: true });
  });
});
