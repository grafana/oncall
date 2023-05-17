import { test, expect } from '@playwright/test';
import { generateRandomValue } from '../utils/forms';
import { createOnCallSchedule } from '../utils/schedule';

test('check schedule quality for simple 1-user schedule', async ({ page }) => {
  const onCallScheduleName = generateRandomValue();
  await createOnCallSchedule(page, onCallScheduleName);

  /**
   * this page.reload() call is a hack to temporarily get around this issue
   * https://github.com/grafana/oncall/issues/1968
   */
  await page.reload({ waitUntil: 'networkidle' });
  await expect(page.locator('div[class*="ScheduleQuality"]')).toHaveText('Quality: Great', { timeout: 15_000 });

  await page.hover('div[class*="ScheduleQuality"]');
  await expect(page.locator('div[class*="ScheduleQualityDetails"] >> span[class*="Text"] >> nth=2 ')).toHaveText(
    'Schedule has no gaps'
  );
  await expect(page.locator('div[class*="ScheduleQualityDetails"] >> span[class*="Text"] >> nth=3 ')).toHaveText(
    'Schedule is perfectly balanced'
  );
});
