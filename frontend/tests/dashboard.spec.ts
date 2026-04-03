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

const resourceUserAuthContext = {
  user_id: 'resource_user',
  display_name: 'Resource User',
  roles: ['resource_user'],
  permissions: ['dashboard.view', 'image.view', 'three_d.view', 'platform.view', 'application.create', 'application.view_own'],
  collection_scope: [],
  auth_mode: 'session',
};

const collectionOwnerAuthContext = {
  user_id: 'collection_owner',
  display_name: 'Collection Owner',
  roles: ['collection_owner'],
  permissions: ['dashboard.view', 'image.view', 'image.edit_scope', 'three_d.view', 'three_d.edit_scope', 'platform.view', 'collection.scope'],
  collection_scope: [101],
  auth_mode: 'session',
};

const availableUsers = [
  {
    username: 'system_admin',
    display_name: 'System Admin',
    roles: [{ key: 'system_admin', label: 'System Admin' }],
    collection_scope: [],
  },
  {
    username: 'resource_user',
    display_name: 'Resource User',
    roles: [{ key: 'resource_user', label: 'Resource User' }],
    collection_scope: [],
  },
  {
    username: 'collection_owner',
    display_name: 'Collection Owner',
    roles: [{ key: 'collection_owner', label: 'Collection Owner' }],
    collection_scope: [101],
  },
];

const sourceDetail = {
  id: 1,
  identifier: 'asset-1',
  title: 'test_image.jpg',
  resource_type: 'image_2d_cultural_object',
  resource_type_label: '2D Image',
  visibility_scope: 'open',
  collection_object_id: 101,
  status: 'ready',
  process_message: 'uploaded',
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
    label: 'Ready',
    message: 'Available for preview and download',
    preview_ready: true,
    has_error: false,
  },
  lifecycle: [
    {
      step: 'object_created',
      label: 'Object Created',
      status: 'done',
      status_label: 'Done',
      description: 'Asset created successfully',
      timestamp: '2024-01-01T10:00:00Z',
      evidence: 'upload',
    },
  ],
  process_timeline: [
    {
      step: 'object_created',
      label: 'Object Created',
      status: 'done',
      status_label: 'Done',
      description: 'Asset created successfully',
    },
  ],
  structure: {
    summary: 'Primary file is the current ingest image.',
    primary_file: {
      role: 'primary',
      role_label: 'Primary File',
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
      role_label: 'Original File',
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
      bagit_note: 'BagIt output is supported',
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
  metadata_layers: {
    schema_version: '2.0',
    core: {
      resource_id: 'asset-1',
      source_system: 'mdams_2d_image_subsystem',
      source_label: '2D Image Subsystem',
      resource_type: 'image_2d_cultural_object',
      resource_type_label: '2D Image',
      title: 'test_image.jpg',
      status: 'ready',
      preview_enabled: true,
      visibility_scope: 'open',
      collection_object_id: 101,
      profile_key: 'other',
      profile_label: 'Other',
      profile_sheet: 'Other',
    },
    management: {},
    technical: {},
    profile: {
      key: 'other',
      label: 'Other',
      sheet: 'Other',
      fields: {},
    },
    raw_metadata: {},
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
      label: 'Mirador Preview',
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
      label: 'Download current file',
      url: '/api/assets/1/download',
    },
    download_bag: {
      label: 'Download BagIt',
      url: '/api/assets/1/download-bag',
    },
  },
};

const unifiedDetail = {
  id: 'image_2d:1',
  source_system: 'image_2d',
  source_id: '1',
  source_label: '2D Image Subsystem',
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

async function bootstrapAuthenticatedState(page, authContext = systemAdminAuthContext) {
  await page.addInitScript((token) => {
    window.localStorage.setItem('mdams.auth.token', token);
  }, 'test-token');

  await page.route('**/api/auth/users', async (route) => {
    await route.fulfill({ json: availableUsers });
  });

  await page.route('**/api/auth/context', async (route) => {
    await route.fulfill({ json: authContext });
  });

  await page.route('**/api/auth/logout', async (route) => {
    await route.fulfill({ json: { status: 'ok' } });
  });

  await page.route('**/api/applications**', async (route) => {
    await route.fulfill({ json: [] });
  });
}

async function bootstrapCommonApi(page, authContext = systemAdminAuthContext) {
  const visibleAssets = [
    {
      id: 1,
      filename: 'test_image.jpg',
      file_size: 1024 * 1024 * 2.5,
      mime_type: 'image/jpeg',
      status: 'ready',
      created_at: '2024-01-01 10:00:00',
    },
  ];

  if (authContext.permissions.includes('system.manage') || authContext.collection_scope.includes(101)) {
    visibleAssets.push({
      id: 2,
      filename: 'owner_scope_image.jpg',
      file_size: 1024 * 700,
      mime_type: 'image/jpeg',
      status: 'ready',
      created_at: '2024-01-01 10:30:00',
    });
  }

  if (authContext.permissions.includes('system.manage')) {
    visibleAssets.push({
      id: 3,
      filename: 'other_owner_image.jpg',
      file_size: 1024 * 600,
      mime_type: 'image/jpeg',
      status: 'processing',
      created_at: '2024-01-01 11:00:00',
    });
  }

  const visibleUnifiedResources = [
    unifiedDetail,
    {
      ...unifiedDetail,
      id: 'image_2d:2',
      source_id: '2',
      title: 'owner_scope_image.jpg',
      status: 'ready',
      preview_enabled: true,
      manifest_url: '/api/iiif/2/manifest',
      detail_url: '/api/platform/resources/image_2d:2',
      updated_at: '2024-01-01T10:30:00Z',
      source_detail_url: '/api/assets/2',
      source_record: {
        ...sourceDetail,
        id: 2,
        identifier: 'asset-2',
        title: 'owner_scope_image.jpg',
        collection_object_id: 101,
        visibility_scope: 'owner_only',
        file: {
          ...sourceDetail.file,
          filename: 'owner_scope_image.jpg',
          actual_filename: 'owner_scope_image.jpg',
        },
        metadata_layers: {
          ...sourceDetail.metadata_layers,
          core: {
            ...sourceDetail.metadata_layers.core,
            resource_id: 'asset-2',
            title: 'owner_scope_image.jpg',
            visibility_scope: 'owner_only',
          },
        },
      },
    },
  ];

  if (authContext.permissions.includes('system.manage')) {
    visibleUnifiedResources.push({
      ...unifiedDetail,
      id: 'image_2d:3',
      source_id: '3',
      title: 'other_owner_image.jpg',
      status: 'processing',
      preview_enabled: false,
      manifest_url: '/api/iiif/3/manifest',
      detail_url: '/api/platform/resources/image_2d:3',
      updated_at: '2024-01-01T11:00:00Z',
      source_detail_url: '/api/assets/3',
      source_record: {
        ...sourceDetail,
        id: 3,
        identifier: 'asset-3',
        title: 'other_owner_image.jpg',
        collection_object_id: 102,
        visibility_scope: 'owner_only',
        file: {
          ...sourceDetail.file,
          filename: 'other_owner_image.jpg',
          actual_filename: 'other_owner_image.jpg',
        },
        metadata_layers: {
          ...sourceDetail.metadata_layers,
          core: {
            ...sourceDetail.metadata_layers.core,
            resource_id: 'asset-3',
            title: 'other_owner_image.jpg',
            visibility_scope: 'owner_only',
            collection_object_id: 102,
          },
        },
      },
    });
  }

  await page.route('/api/assets', async (route) => {
    await route.fulfill({ json: visibleAssets });
  });

  await page.route('**/api/assets/1', async (route) => {
    await route.fulfill({ json: sourceDetail });
  });

  await page.route('**/api/assets/2', async (route) => {
    await route.fulfill({
      json: {
        ...sourceDetail,
        id: 2,
        identifier: 'asset-2',
        title: 'owner_scope_image.jpg',
        visibility_scope: 'owner_only',
        collection_object_id: 101,
        file: {
          ...sourceDetail.file,
          filename: 'owner_scope_image.jpg',
          actual_filename: 'owner_scope_image.jpg',
        },
      },
    });
  });

  await page.route('**/api/assets/3', async (route) => {
    await route.fulfill({
      json: {
        ...sourceDetail,
        id: 3,
        identifier: 'asset-3',
        title: 'other_owner_image.jpg',
        visibility_scope: 'owner_only',
        collection_object_id: 102,
        file: {
          ...sourceDetail.file,
          filename: 'other_owner_image.jpg',
          actual_filename: 'other_owner_image.jpg',
        },
      },
    });
  });

  await page.route('**/api/platform/sources**', async (route) => {
    await route.fulfill({
      json: [
        {
          source_system: 'image_2d',
          source_label: '2D Image Subsystem',
          resource_type: 'image_2d_cultural_object',
          resource_count: visibleUnifiedResources.length,
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
    if (url.pathname.includes('/api/platform/resources/image_2d:2') || url.pathname.includes('/api/platform/resources/image_2d%3A2')) {
      await route.fulfill({ json: visibleUnifiedResources[1] });
      return;
    }
    if (url.pathname.includes('/api/platform/resources/image_2d:3') || url.pathname.includes('/api/platform/resources/image_2d%3A3')) {
      await route.fulfill({ json: visibleUnifiedResources[2] || visibleUnifiedResources[1] });
      return;
    }

    const query = url.searchParams.get('q')?.toLowerCase() || '';
    const status = url.searchParams.get('status');
    const previewEnabled = url.searchParams.get('preview_enabled');
    const resourceType = url.searchParams.get('resource_type');

    const filtered = visibleUnifiedResources.filter((item) => {
      const matchesQuery =
        !query || [item.id, item.title, item.resource_type, item.source_id].some((value) => value.toLowerCase().includes(query));
      const matchesStatus = !status || item.status === status;
      const matchesPreview =
        !previewEnabled
        || (previewEnabled === 'true' && item.preview_enabled)
        || (previewEnabled === 'false' && !item.preview_enabled);
      const matchesResourceType = !resourceType || item.resource_type === resourceType;
      return matchesQuery && matchesStatus && matchesPreview && matchesResourceType;
    });

    await route.fulfill({ json: filtered });
  });
}

test.describe('Dashboard permissions', () => {
  test.beforeEach(async ({ page }) => {
    await bootstrapAuthenticatedState(page, systemAdminAuthContext);
    await bootstrapCommonApi(page, systemAdminAuthContext);
    await page.goto('/');
  });

  test('system admin sees the dashboard and resource table', async ({ page }) => {
    await expect(page).toHaveTitle(/MEAM Prototype/);
    await expect(page.getByTestId('assets-table')).toBeVisible();
    await expect(page.locator('.ant-statistic-content-value').first()).toHaveText('3');
    await expect(page.getByTestId('menu-8')).toBeVisible();
  });

  test('system admin can open the unified resource directory', async ({ page }) => {
    await page.getByTestId('menu-5').click();
    await expect(page.getByTestId('platform-directory')).toBeVisible();
    await expect(page.getByRole('cell', { name: 'test_image.jpg' }).first()).toBeVisible();
    await expect(page.getByRole('cell', { name: 'image_2d:1' })).toBeVisible();
  });

  test('system admin can search unified resources', async ({ page }) => {
    await page.getByTestId('menu-5').click();
    await page.getByTestId('platform-search').fill('owner_scope');
    await page.keyboard.press('Enter');
    await expect(page.getByRole('cell', { name: 'owner_scope_image.jpg' }).first()).toBeVisible();
    await expect(page.getByRole('cell', { name: 'test_image.jpg' })).toHaveCount(0);
  });

  test('system admin can open unified detail page', async ({ page }) => {
    await page.getByTestId('menu-5').click();
    await page.getByTestId('platform-unified-detail-1').click();
    await expect(page.getByTestId('unified-resource-detail')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'test_image.jpg' })).toBeVisible();
  });
});

test.describe('Role visibility', () => {
  test.beforeEach(async ({ page }) => {
    await bootstrapAuthenticatedState(page, resourceUserAuthContext);
    await bootstrapCommonApi(page, resourceUserAuthContext);
    await page.goto('/');
  });

  test('resource user sees the dashboard but not admin menus', async ({ page }) => {
    await expect(page.getByTestId('assets-table')).toBeVisible();
    await expect(page.getByTestId('menu-3')).toBeVisible();
    await expect(page.getByTestId('menu-4')).toHaveCount(0);
    await expect(page.getByTestId('menu-8')).toHaveCount(0);
  });
});

test.describe('Collection owner scope', () => {
  test.beforeEach(async ({ page }) => {
    await bootstrapAuthenticatedState(page, collectionOwnerAuthContext);
    await bootstrapCommonApi(page, collectionOwnerAuthContext);
    await page.goto('/');
  });

  test('collection owner sees own scope resources but not other owner-only resources', async ({ page }) => {
    await expect(page.getByTestId('assets-table')).toBeVisible();
    await expect(page.getByRole('cell', { name: 'test_image.jpg' }).first()).toBeVisible();
    await expect(page.getByRole('cell', { name: 'owner_scope_image.jpg' }).first()).toBeVisible();
    await expect(page.getByRole('cell', { name: 'other_owner_image.jpg' })).toHaveCount(0);
  });

  test('collection owner can open scoped unified directory items', async ({ page }) => {
    await page.getByTestId('menu-5').click();
    await expect(page.getByTestId('platform-directory')).toBeVisible();
    await expect(page.getByRole('cell', { name: 'test_image.jpg' }).first()).toBeVisible();
    await expect(page.getByRole('cell', { name: 'owner_scope_image.jpg' }).first()).toBeVisible();
    await expect(page.getByRole('cell', { name: 'other_owner_image.jpg' })).toHaveCount(0);
  });
});

