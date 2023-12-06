import type { Page } from '@playwright/test';

import { BASE_URL } from './constants';

type GrafanaPage = '/plugins/grafana-oncall-app';
type OnCallPage = 'alert-groups' | 'integrations' | 'escalations' | 'schedules' | 'users';

const _goToPage = async (page: Page, url = '') => page.goto(`${BASE_URL}${url}`);

export const goToGrafanaPage = async (page: Page, url: GrafanaPage) => _goToPage(page, url);

export const goToOnCallPage = async (page: Page, onCallPage: OnCallPage) => {
  await _goToPage(page, `/a/grafana-oncall-app/${onCallPage}`);
  await page.getByTestId('oncall-header').waitFor();
};
