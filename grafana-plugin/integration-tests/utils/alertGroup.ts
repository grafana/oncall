import { Locator, Page, expect } from '@playwright/test';
import { selectDropdownValue, selectValuePickerValue } from './forms';
import { goToOnCallPage } from './navigation';

const MAX_RETRIES = 5;
const ALERT_GROUP_REGISTERED_TEXT = 'alert group registered';

const getIncidentTimelineList = async (page: Page): Promise<Locator> => {
  const incidentTimelineList = page.getByTestId('incident-timeline-list');
  await incidentTimelineList.waitFor({ state: 'visible' });
  return incidentTimelineList;
};

/**
 * recursively refreshes the page waiting for the background celery workers to have done their job of
 * escalating the alert group
 */
const incidentTimelineContainsStep = async (page: Page, triggeredStepText: string, retryNum = 0): Promise<boolean> => {
  if (retryNum > MAX_RETRIES) {
    return Promise.resolve(false);
  }

  const incidentTimelineList = await getIncidentTimelineList(page);

  if (!incidentTimelineList.getByText(triggeredStepText)) {
    await page.reload({ waitUntil: 'networkidle' });
    return incidentTimelineContainsStep(page, triggeredStepText, (retryNum += 1));
  }
  return true;
};

export const filterAlertGroupsTableByIntegrationAndGoToDetailPage = async (
  page: Page,
  integrationName: string
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
};

export const verifyThatAlertGroupIsRoutedCorrectlyButNotEscalated = async (
  page: Page,
  integrationName: string,
  routedText: string
): Promise<void> => {
  await filterAlertGroupsTableByIntegrationAndGoToDetailPage(page, integrationName);

  /**
   * incidentTimelineContainsStep recursively reloads the alert group page until the engine
   * background workers have processed/escalated the alert group
   */
  expect(await incidentTimelineContainsStep(page, ALERT_GROUP_REGISTERED_TEXT)).toBe(true);

  const incidentTimelineList = await getIncidentTimelineList(page);
  expect(incidentTimelineList).toContainText(routedText);
  expect(incidentTimelineList).not.toContainText('triggered step');
};

export const verifyThatAlertGroupIsTriggered = async (
  page: Page,
  integrationName: string,
  triggeredStepText: string
): Promise<void> => {
  await filterAlertGroupsTableByIntegrationAndGoToDetailPage(page, integrationName);

  expect(await incidentTimelineContainsStep(page, triggeredStepText)).toBe(true);
};
