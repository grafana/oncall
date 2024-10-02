import { AppFeature } from 'state/features';

import { test, expect } from '../fixtures';
import { goToOnCallPage } from '../utils/navigation';

test('Google Calendar connector and Google Calendar tab are visible if google_oauth2 feature enabled', async ({
  adminRolePage: { page },
}) => {
  goToOnCallPage(page, 'users/me');

  const featuresResponse = await page.waitForResponse((resp) => {
    return resp.url().includes('/features/') && resp.status() === 200;
  });

  const features = await featuresResponse.json();

  if (features.includes(AppFeature.GoogleOauth2)) {
    await expect(page.getByTestId('google-calendar-connector-title')).toBeVisible();
    await expect(page.getByTestId('google-calendar-tab')).toBeVisible();
  }
});
