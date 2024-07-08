import { PlaywrightTestProject, defineConfig, devices } from '@playwright/test';

import path from 'path';
/**
 * Read environment variables from file.
 * https://github.com/motdotla/dotenv
 */
require('dotenv').config({ path: path.resolve(process.cwd(), 'e2e-tests/.env') });

export const VIEWER_USER_STORAGE_STATE = path.join(__dirname, 'e2e-tests/.auth/viewer.json');
export const EDITOR_USER_STORAGE_STATE = path.join(__dirname, 'e2e-tests/.auth/editor.json');
export const ADMIN_USER_STORAGE_STATE = path.join(__dirname, 'e2e-tests/.auth/admin.json');

const IS_CI = !!process.env.CI;
const BROWSERS = process.env.BROWSERS || 'chromium';

const SETUP_PROJECT_NAME = 'setup';
const getEnabledBrowsers = (browsers: PlaywrightTestProject[]) =>
  browsers.filter(({ name }) => name === SETUP_PROJECT_NAME || BROWSERS.includes(name));

/**
 * See https://playwright.dev/docs/test-configuration.
 */
export default defineConfig({
  testDir: './e2e-tests',

  /* Maximum time all the tests can run for. */
  globalTimeout: 20 * 60 * 1_000, // 20 minutes

  reporter: [['html', { open: IS_CI ? 'never' : 'always' }]],

  /* Maximum time one test can run for. */
  timeout: 60_000,
  expect: {
    /**
     * Maximum time expect() should wait for the condition to be met.
     * For example in `await expect(locator).toHaveText();`
     */
    timeout: 10_000,
  },
  /* Run tests in files in parallel */
  fullyParallel: false,
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: IS_CI,
  /**
   * Retry on CI only
   *
   * NOTE: until we fix this issue (https://github.com/grafana/oncall/issues/1692) which occasionally leads
   * to flaky tests.. let's allow 1 retry per test
   */
  retries: 1,
  workers: '25%', // 25% of logical CPU cores, e.g. for 16 CPU cores it will use 4 workers
  /* Reporter to use. See https://playwright.dev/docs/test-reporters */
  // reporter: 'html',
  /* Shared settings for all the projects below. See https://playwright.dev/docs/api/class-testoptions. */
  use: {
    /* Maximum time each action such as `click()` can take. Defaults to 0 (no limit). */
    actionTimeout: 0,
    /* Base URL to use in actions like `await page.goto('/')`. */
    // baseURL: 'http://localhost:3000',

    trace: 'on',
    video: 'off',
    headless: true,
  },

  /* Configure projects for major browsers. The final list is filtered based on BROWSERS env var */
  projects: getEnabledBrowsers([
    {
      name: SETUP_PROJECT_NAME,
      testMatch: /globalSetup\.ts/,
    },
    {
      name: 'chromium',
      use: devices['Desktop Chrome'],
      dependencies: [SETUP_PROJECT_NAME],
    },
    {
      name: 'firefox',
      use: devices['Desktop Firefox'],
      dependencies: [SETUP_PROJECT_NAME],
    },
    {
      name: 'webkit',
      use: devices['Desktop Safari'],
      dependencies: [SETUP_PROJECT_NAME],
    },

    /* Test against mobile viewports. */
    // {
    //   name: 'Mobile Chrome',
    //   use: devices['Pixel 5'],
    // },
    // {
    //   name: 'Mobile Safari',
    //   use: devices['iPhone 12'],
    // },

    /* Test against branded browsers. */
    // {
    //   name: 'Microsoft Edge',
    //   use: {
    //     channel: 'msedge',
    //   },
    // },
    // {
    //   name: 'Google Chrome',
    //   use: {
    //     channel: 'chrome',
    //   },
    // },
  ]),

  /* Folder for test artifacts such as screenshots, videos, traces, etc. 
  Set outside of grafana-plugin to prevent refreshing Grafana UI during e2e test runs */
  outputDir: '../test-results/',

  /* Run your local dev server before starting the tests */
  // webServer: {
  //   command: 'npm run start',
  //   port: 3000,
  // },
});
