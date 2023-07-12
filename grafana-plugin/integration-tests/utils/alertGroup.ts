import { Page, expect } from '@playwright/test';
import { selectDropdownValue, selectValuePickerValue } from './forms';
import { goToOnCallPage } from './navigation';

const MAX_RETRIES = 5;

// const sleep = async (seconds: number) => new Promise((resolve) => setTimeout(resolve, seconds * 1000));

/**
 * recursively refreshes the page waiting for the background celery workers to have done their job of
 * escalating the alert group
 */
const incidentTimelineContainsStep = async (page: Page, triggeredStepText: string, retryNum = 0): Promise<boolean> => {
  if (retryNum > MAX_RETRIES) {
    return Promise.resolve(false);
  }

  if (!page.getByTestId('incident-timeline-list').getByText(triggeredStepText)) {
    await page.reload({ waitUntil: 'networkidle' });
    return incidentTimelineContainsStep(page, triggeredStepText, (retryNum += 1));
  }
  return true;
};

export const verifyThatAlertGroupIsTriggered = async (
  page: Page,
  integrationName: string,
  triggeredStepText: string
): Promise<void> => {
  await goToOnCallPage(page, 'incidents');

  // filter by integration
  const selectElement = await selectDropdownValue({
    page,
    selectType: 'grafanaSelect',
    placeholderText: 'Search or filter results...',
    value: 'Integration',
  });
  await selectElement.type(integrationName);
  await selectValuePickerValue(page, integrationName, false);

  /**
   * wait for the alert groups to be filtered then
   * click on the alert group and go to the individual alert group page
   */
  await (await page.waitForSelector('table > tbody > tr > td:nth-child(4) a')).click();

  expect(await incidentTimelineContainsStep(page, triggeredStepText)).toBe(true);
};
