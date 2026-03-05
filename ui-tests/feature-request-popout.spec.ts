import { test, expect } from '@playwright/test';

test('feature request opens in a popout window', async ({ page, baseURL }) => {
  await page.goto(baseURL!, { waitUntil: 'networkidle' });

  // Inline form should not exist on main page.
  await expect(page.getByPlaceholder('Title')).toHaveCount(0);

  const openBtn = page.getByRole('button', { name: 'Request a feature ↗' });
  await expect(openBtn).toBeVisible();

  const [popup] = await Promise.all([
    page.waitForEvent('popup'),
    openBtn.click(),
  ]);

  await popup.waitForLoadState('domcontentloaded');
  await expect(popup.getByRole('heading', { name: 'Request a feature' })).toBeVisible({ timeout: 15000 });

  await expect(popup.getByPlaceholder('Title')).toBeVisible();
  await expect(popup.getByPlaceholder('Description')).toBeVisible();
  await expect(popup.getByPlaceholder('Expected outcome')).toBeVisible();
});
