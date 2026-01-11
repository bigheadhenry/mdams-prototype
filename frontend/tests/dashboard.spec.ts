import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Mock the assets API call
    await page.route('/api/assets', async route => {
      const json = [
        {
          id: 1,
          filename: 'test_image.jpg',
          file_size: 1024 * 1024 * 2.5, // 2.5 MB
          mime_type: 'image/jpeg',
          status: 'ready',
          created_at: '2024-01-01 10:00:00'
        },
        {
          id: 2,
          filename: 'document.png',
          file_size: 1024 * 500, // 500 KB
          mime_type: 'image/png',
          status: 'processing',
          created_at: '2024-01-01 11:00:00'
        }
      ];
      await route.fulfill({ json });
    });

    await page.goto('/');
  });

  test('should load the dashboard correctly', async ({ page }) => {
    // Check title or main layout presence
    await expect(page).toHaveTitle(/MEAM Prototype/); 
    
    // Check for Dashboard menu item
    await expect(page.getByRole('menuitem', { name: 'Dashboard' })).toBeVisible();
    
    // Check for Statistics
    await expect(page.getByText('Total Assets')).toBeVisible();
    // Since we mocked 2 assets, the value should be 2
    await expect(page.locator('.ant-statistic-content-value').first()).toHaveText('2');
  });

  test('should display assets in the table', async ({ page }) => {
    // Check table headers
    await expect(page.getByRole('columnheader', { name: 'Filename' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Status' })).toBeVisible();

    // Check mocked data in table
    await expect(page.getByText('test_image.jpg')).toBeVisible();
    await expect(page.getByText('document.png')).toBeVisible();
    
    // Check status tags
    await expect(page.getByText('READY')).toBeVisible();
    await expect(page.getByText('PROCESSING')).toBeVisible();
  });

  test('should show upload button', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'Upload New Asset' })).toBeVisible();
  });
});
