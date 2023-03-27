import { test, expect } from '@playwright/test';
import { configureOnCallPlugin } from '../utils/configurePlugin';
import { generateRandomValue } from '../utils/forms';
import { createOnCallSchedule } from '../utils/schedule';

test.beforeEach(async ({ page }) => {
  await configureOnCallPlugin(page);
});

test('check schedule quality for simple 1-user schedule', async ({ page }) => {
  const onCallScheduleName = generateRandomValue();
  await createOnCallSchedule(page, onCallScheduleName);

  await expect(page.locator('div[class*="ScheduleQuality"]')).toHaveText('Quality: Great');

  await page.hover('div[class*="ScheduleQuality"]');
  await expect(page.locator('div[class*="ScheduleQualityDetails"] >> span[class*="Text"] >> nth=2 ')).toHaveText('Schedule has no gaps');
  await expect(page.locator('div[class*="ScheduleQualityDetails"] >> span[class*="Text"] >> nth=3 ')).toHaveText('Schedule is perfectly balanced');
});
