import { Page } from '@playwright/test';
import { GRAFANA_USERNAME } from './constants';
import { clickButton, fillInInput, selectDropdownValue, selectValuePickerValue } from './forms';
import { goToOnCallPageByClickingOnTab } from './navigation';

export const createOnCallSchedule = async (page: Page, scheduleName: string): Promise<void> => {
  // go to the escalation chains page
  await goToOnCallPageByClickingOnTab(page, 'Schedules');

  // create an oncall-rotation schedule
  await clickButton({ page, buttonText: 'New Schedule' });
  (await page.waitForSelector('button >> text=Create >> nth=0')).click();

  // fill in the name input
  await fillInInput(page, 'div[class*="ScheduleForm"] input[name="name"]', scheduleName);

  // Add a new layer w/ the current user to it
  await clickButton({ page, buttonText: 'Create Schedule' });

  await clickButton({ page, buttonText: 'Add rotation' });
  await selectValuePickerValue(page, 'New Layer');

  await selectDropdownValue({
    page,
    selectType: 'grafanaSelect',
    placeholderText: 'Add user',
    value: GRAFANA_USERNAME,
  });

  await clickButton({ page, buttonText: 'Create' });
};
