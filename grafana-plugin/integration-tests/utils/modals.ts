import { Page } from '@playwright/test';

// close the currently opened modal
export const closeModal = async (page: Page): Promise<void> =>
  (await page.waitForSelector('button[aria-label="Close dialogue"]')).click();
