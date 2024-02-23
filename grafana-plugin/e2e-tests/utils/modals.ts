import { Page } from '@playwright/test';

/**
 * in Grafana v9 the aria-label is "Close dialog"
 * in Grafana v10+ the aria-label is "Close dialogue"
 */
export const closeModal = async (page: Page): Promise<void> =>
  (await page.waitForSelector('button[aria-label*="Close dialog"]')).click();
