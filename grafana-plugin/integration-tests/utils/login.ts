import type { Page } from '@playwright/test';
import { GRAFANA_PASSWORD, GRAFANA_USERNAME } from './constants';
import { clickButton, fillInInputByPlaceholderValue } from './forms';
import { goToGrafanaPage, waitForNoNetworkActivity } from './navigation';

export const login = async (page: Page): Promise<void> => {
  await goToGrafanaPage(page, '/login', 'load');

  await fillInInputByPlaceholderValue(page, 'email or username', GRAFANA_USERNAME);
  await fillInInputByPlaceholderValue(page, 'password', GRAFANA_PASSWORD);
  await clickButton({ page, buttonText: 'Log in' });
  await waitForNoNetworkActivity(page);
};
