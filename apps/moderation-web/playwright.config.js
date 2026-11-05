import {defineConfig} from '@playwright/test'
export default defineConfig({testDir:'./tests',timeout:45000,workers:1,retries:0,
  testMatch:process.env.SHIELDVI_FULLSTACK_E2E==='1'?'fullstack.spec.js':'review.spec.js',
  outputDir:process.env.PW_OUTPUT_DIR||'test-results',reporter:[['list']],
  use:{baseURL:process.env.MODERATION_WEB_TEST_URL||'http://127.0.0.1:5174',browserName:'chromium',
    channel:process.env.PLAYWRIGHT_CHANNEL||'chrome',headless:true,viewport:{width:1440,height:1050},trace:'off',screenshot:'only-on-failure'}})
