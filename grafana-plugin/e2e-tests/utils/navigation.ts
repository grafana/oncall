import type { Page, Response } from '@playwright/test';
import { BASE_URL } from './constants';

type GrafanaPage = '/plugins/grafana-oncall-app';
type OnCallPage = 'alert-groups' | 'integrations' | 'escalations' | 'schedules' | 'users';

const _goToPage = (page: Page, url = ''): Promise<Response> => page.goto(`${BASE_URL}${url}`);

export const goToGrafanaPage = (page: Page, url: GrafanaPage): Promise<Response> => _goToPage(page, url);

export const goToOnCallPage = (page: Page, onCallPage: OnCallPage): Promise<Response> =>
  _goToPage(page, `/a/grafana-oncall-app/${onCallPage}`);
