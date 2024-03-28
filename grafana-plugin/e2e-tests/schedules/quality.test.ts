import { test, expect } from '../fixtures';
import { generateRandomValue } from '../utils/forms';
import { createOnCallScheduleWithRotation } from '../utils/schedule';

test('check schedule quality for simple 1-user schedule', async ({ adminRolePage }) => {
  const { page, userName } = adminRolePage;
  const onCallScheduleName = generateRandomValue();

  await createOnCallScheduleWithRotation(page, onCallScheduleName, userName);

  const scheduleQualityElement = page.getByTestId('schedule-quality');
  await scheduleQualityElement.waitFor({ state: 'visible' });

  await expect(scheduleQualityElement).toHaveText('Quality: Great', { timeout: 15_000 });

  await scheduleQualityElement.hover();

  const scheduleQualityDetailsElement = page.getByTestId('schedule-quality-details');
  await scheduleQualityDetailsElement.waitFor({ state: 'visible' });

  await expect(scheduleQualityDetailsElement).toHaveText(/Schedule has no gaps/);
  await expect(scheduleQualityDetailsElement).toHaveText(/Schedule is perfectly balanced/);
});
