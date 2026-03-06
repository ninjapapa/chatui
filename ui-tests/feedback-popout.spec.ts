import { test, expect } from '@playwright/test';

test('feedback popout opens and switches types + has changelog tab', async ({ page, baseURL }) => {
  await page.goto(baseURL!, { waitUntil: 'networkidle' });

  const openBtn = page.getByRole('button', { name: 'Feedback ↗' });
  await expect(openBtn).toBeVisible();

  const [popup] = await Promise.all([
    page.waitForEvent('popup'),
    openBtn.click(),
  ]);

  await popup.waitForLoadState('domcontentloaded');
  await expect(popup.getByRole('heading', { name: 'Feedback' })).toBeVisible({ timeout: 15000 });

  // Default: Feedback type shows single textarea
  await expect(popup.getByPlaceholder('Feedback')).toBeVisible();
  await expect(popup.getByPlaceholder('Description')).toHaveCount(0);

  // Switch to feature request
  await popup.getByLabel('Request feature').click();
  await expect(popup.getByPlaceholder('Description')).toBeVisible();
  await expect(popup.getByPlaceholder('Expected result / example')).toBeVisible();

  // Changelog tab
  await popup.getByRole('button', { name: 'Changelog' }).click();
  await expect(popup.getByRole('heading', { name: 'Changelog' })).toBeVisible();
});
