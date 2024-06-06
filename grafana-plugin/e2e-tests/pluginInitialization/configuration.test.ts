import { PLUGIN_ID } from 'utils/consts';

import { test, expect } from '../fixtures';
import { goToGrafanaPage } from '../utils/navigation';

test.describe('Plugin configuration', () => {
  test('Admin user can see currently applied URL', async ({ adminRolePage: { page } }) => {
    const urlInput = page.getByTestId('oncall-api-url-input');

    await goToGrafanaPage(page, `/plugins/${PLUGIN_ID}`);
    const currentlyAppliedURL = await urlInput.inputValue();

    expect(currentlyAppliedURL).toBe('http://oncall-dev-engine:8080');
  });
});
