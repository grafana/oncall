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

  const scheduleQualityElement = page.getByTestId('schedule-quality');

  await expect(scheduleQualityElement).toHaveText('Quality: Great', { timeout: 15_000 });

  await scheduleQualityElement.hover();

  const scheduleQualityDetailsElement = page.getByTestId('schedule-quality-details');

  await expect(scheduleQualityDetailsElement.locator('span[class*="Text"] >> nth=2 ')).toHaveText(
    'Schedule has no gaps'
  );
  await expect(scheduleQualityDetailsElement.locator('span[class*="Text"] >> nth=3 ')).toHaveText(
    'Schedule is perfectly balanced'
  );
});
