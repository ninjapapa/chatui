import { test, expect } from '@playwright/test';

test('smoke: app boots + websocket connects + roundtrip', async ({ page, baseURL }) => {
  const errors: string[] = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  page.on('console', (msg) => {
    if (msg.type() === 'error') errors.push(msg.text());
  });

  await page.goto(baseURL!, { waitUntil: 'networkidle' });

  await expect(page.getByText('Chat Interface')).toBeVisible({ timeout: 15000 });
  await expect(page.getByText('Connected')).toBeVisible({ timeout: 15000 });

  const input = page.getByPlaceholder('Type your message...');
  await expect(input).toBeEnabled({ timeout: 15000 });

  await input.fill('hello');
  await input.press('Enter');

  // An assistant bubble should show up.
  await expect(page.getByText('assistant').first()).toBeVisible({ timeout: 15000 });

  if (errors.length) {
    throw new Error(`Console/page errors:\n${errors.join('\n')}`);
  }
});
