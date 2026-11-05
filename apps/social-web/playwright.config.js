import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './tests', timeout: 30000, workers: 1, retries: 0,
  outputDir: process.env.PW_OUTPUT_DIR || 'test-results',
  reporter: [['list']],
  use: {
    baseURL: process.env.SOCIAL_WEB_TEST_URL || 'http://127.0.0.1:5173',
    browserName: 'chromium', channel: process.env.PLAYWRIGHT_CHANNEL || 'chrome', headless: true,
    viewport: { width: 1440, height: 1050 }, trace: 'off', screenshot: 'only-on-failure',
  },
})
