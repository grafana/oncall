import { PLUGIN_CONFIG } from 'utils/consts';

import { test, expect } from '../fixtures';
import { goToGrafanaPage } from '../utils/navigation';

const DEFAULT_ONCALL_API_URL = 'http://oncall-dev-engine:8080';

test.describe('Plugin configuration', () => {
  test('Admin user can see currently applied URL', async ({ adminRolePage: { page } }) => {
    await goToGrafanaPage(page, PLUGIN_CONFIG);
    await page.waitForLoadState('networkidle');
    const currentlyAppliedURL = await page.getByTestId('oncall-api-url-input').inputValue();

    expect(currentlyAppliedURL).toBe(DEFAULT_ONCALL_API_URL);
  });

  test('Admin user can see error when invalid OnCall API URL is entered and plugin is reconnected', async ({
    adminRolePage: { page },
  }) => {
    await goToGrafanaPage(page, PLUGIN_CONFIG);

    // show client-side validation errors
    const urlInput = page.getByTestId('oncall-api-url-input');
    await urlInput.fill('');
    await page.getByText('URL is required').waitFor();
    await urlInput.fill('invalid-url-format:8080');
    await page.getByText('URL is invalid').waitFor();

    // apply back correct url and verify plugin connected again
    await urlInput.fill(DEFAULT_ONCALL_API_URL);
    await page.getByTestId('connect-plugin').click();
    await page.waitForLoadState('networkidle');
    await page.getByText('Plugin is connected').waitFor();
  });
});
