import { Page } from '@playwright/test';

/**
 * in Grafana v9 the aria-label is "Close dialog"
 * in Grafana v10+ the aria-label is "Close dialogue"
 *
 * https://playwright.dev/docs/other-locators#css-elements-matching-one-of-the-conditions
 */
export const closeModal = async (page: Page): Promise<void> =>
  (await page.waitForSelector('button[aria-label="Close dialog"], button[aria-label="Close dialogue"]')).click();
