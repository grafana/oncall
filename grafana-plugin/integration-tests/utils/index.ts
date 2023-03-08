import type { Page } from '@playwright/test';
import { configureOnCallPlugin } from './configurePlugin';
import { login } from './login';
import { goToOnCallPage } from './navigation';

export const openOnCallPlugin = async (page: Page): Promise<void> => {
  await login(page);
  await configureOnCallPlugin(page);
  await goToOnCallPage(page);
};
