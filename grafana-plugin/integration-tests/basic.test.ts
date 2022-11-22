import { test, expect } from '@playwright/test';
import { openOnCallPlugin } from './utils';

test.beforeEach(async ({ page }) => {
  await openOnCallPlugin(page);
});

test('we can open the Alert Groups page', async ({ page }) => {
  expect(await page.waitForSelector('text=Acknowledged alert groups')).not.toBeNull();
});
