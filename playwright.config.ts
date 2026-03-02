import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: 'ui-tests',
  timeout: 30_000,
  use: {
    headless: true,
    viewport: { width: 1200, height: 800 },
    baseURL: process.env.PW_BASE_URL || 'http://127.0.0.1:8080',
  },
});
