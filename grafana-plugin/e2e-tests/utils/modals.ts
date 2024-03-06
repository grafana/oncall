import { Page } from '@playwright/test';

/**
 * in Grafana v9 the aria-label is "Close dialog"
 * in Grafana v10.0 the aria-label is "Close dialogue"
 * in Grafana v10.1 the aria-label is "Close"
 * 🙄
 *
 * https://playwright.dev/docs/other-locators#css-elements-matching-one-of-the-conditions
 */
const POSSIBLE_CLOSE_MODAL_BUTTON_DIALOGUE_ARIA_LABELS = ['Close dialog', 'Close dialogue', 'Close'];
const CLOSE_MODAL_BUTTON_ARIA_LABEL_SELECTOR = POSSIBLE_CLOSE_MODAL_BUTTON_DIALOGUE_ARIA_LABELS.map(
  (ariaLabel) => `button[aria-label="${ariaLabel}"]`
).join(', ');

export const closeModal = async (page: Page): Promise<void> =>
  (await page.waitForSelector(CLOSE_MODAL_BUTTON_ARIA_LABEL_SELECTOR))?.click();
