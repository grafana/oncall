import type { Page, Response } from '@playwright/test';
import { BASE_URL } from './constants';

type WaitUntil = 'networkidle' | 'load';
type GrafanaPage = '/login' | '/plugins/grafana-oncall-app';
type OnCallPage = 'incidents' | 'integrations' | 'escalations';
type OnCallPluginTab = 'Integrations' | 'Escalation Chains' | 'Users' | 'Schedules' | 'Alert Groups';

const _goToPage = (page: Page, url = '', waitUntil: WaitUntil = 'networkidle'): Promise<Response> =>
  page.goto(`${BASE_URL}${url}`, { waitUntil });

export const goToGrafanaPage = (page: Page, url?: GrafanaPage, waitUntil?: WaitUntil): Promise<Response> =>
  _goToPage(page, url, waitUntil);

export const goToOnCallPage = (page: Page, onCallPage: OnCallPage = 'incidents'): Promise<Response> =>
  _goToPage(page, `/a/grafana-oncall-app/${onCallPage}`);

export const goToOnCallPageByClickingOnTab = async (page: Page, onCallTab: OnCallPluginTab): Promise<void> =>
  (await page.waitForSelector(`div[class*="LegacyNavTabsBar"] >> text=${onCallTab}`)).click();

export const waitForNoNetworkActivity = (page: Page): Promise<void> => page.waitForLoadState('networkidle');
