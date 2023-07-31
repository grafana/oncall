import { test, expect } from '../fixtures';
import { clickButton, generateRandomValue } from '../utils/forms';
import { createOnCallSchedule, getOverrideFormDateInputs } from '../utils/schedule';
import dayjs from 'dayjs';

test('default dates in override creation modal are correct', async ({ adminRolePage }) => {
  const { page, userName } = adminRolePage;

  const onCallScheduleName = generateRandomValue();
  await createOnCallSchedule(page, onCallScheduleName, userName);

  await clickButton({ page, buttonText: 'Add override' });

  const overrideFormDateInputs = await getOverrideFormDateInputs(page);

  const expectedStart = dayjs().startOf('day'); // start of today
  const expectedEnd = expectedStart.add(1, 'day'); // end of today

  expect(overrideFormDateInputs.start.isSame(expectedStart)).toBe(true);
  expect(overrideFormDateInputs.end.isSame(expectedEnd)).toBe(true);
});
