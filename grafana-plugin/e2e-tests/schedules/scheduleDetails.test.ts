import { test, expect } from '../fixtures';
import { generateRandomValue } from '../utils/forms';
import { createOnCallScheduleWithRotation, createRotation } from '../utils/schedule';

test(`user can see the other user's details`, async ({ adminRolePage, editorRolePage }) => {
  const { page, userName: adminUserName } = adminRolePage;
  const editorUserName = editorRolePage.userName;
  const onCallScheduleName = generateRandomValue();

  await createOnCallScheduleWithRotation(page, onCallScheduleName, adminUserName);
  await createRotation(page, editorUserName, false);

  await page.waitForTimeout(1_000);

  await page.getByTestId('user-avatar-in-schedule').first().hover();
  await expect(page.getByTestId('schedule-user-details')).toHaveText(new RegExp(editorUserName));
});
