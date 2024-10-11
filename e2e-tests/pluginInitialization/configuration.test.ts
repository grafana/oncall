import { PLUGIN_CONFIG } from 'helpers/consts';

import { test, expect } from '../fixtures';
import { goToGrafanaPage } from '../utils/navigation';

test.describe('Plugin configuration', () => {
  test('Admin user can see currently applied URL', async ({ adminRolePage: { page } }) => {
    await goToGrafanaPage(page, PLUGIN_CONFIG);
    await page.waitForLoadState('networkidle');
    const currentlyAppliedURL = await page.getByTestId('oncall-api-url-input').inputValue();

    expect(currentlyAppliedURL).toBe('http://oncall-dev-engine:8080');
  });

  test('Admin user can see error when invalid OnCall API URL is entered and plugin is reconnected', async ({
    adminRolePage: { page },
  }) => {
    await goToGrafanaPage(page, PLUGIN_CONFIG);
    await page.waitForLoadState('networkidle');
    const correctURLAppliedByDefault = await page.getByTestId('oncall-api-url-input').inputValue();

    // show client-side validation errors
    const urlInput = page.getByTestId('oncall-api-url-input');
    await urlInput.fill('');
    await page.getByText('URL is required').waitFor();
    await urlInput.fill('invalid-url-format:8080');
    await page.getByText('URL is invalid').waitFor();

    // apply back correct url and verify plugin connected again
    await urlInput.fill(correctURLAppliedByDefault);
    await page.waitForTimeout(500);
    await page.getByTestId('connect-plugin').click();
    await page.waitForLoadState('networkidle');
    await page.getByText('Plugin is connected').waitFor();
  });
});
