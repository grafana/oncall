import { Page } from '@playwright/test';
import { GRAFANA_USERNAME } from './constants';
import { clickButton, fillInInput, selectDropdownValue, selectValuePickerValue } from './forms';
import { goToOnCallPage } from './navigation';
import dayjs from 'dayjs';

export const createOnCallSchedule = async (page: Page, scheduleName: string): Promise<void> => {
  // go to the schedules page
  await goToOnCallPage(page, 'schedules');

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

export interface OverrideFormDateInputs {
  start: dayjs.Dayjs;
  end: dayjs.Dayjs;
}

export const getOverrideFormDateInputs = async (page: Page): Promise<OverrideFormDateInputs> => {
  const getInputValue = async (inputNumber: number): Promise<string> => {
    const element = await page.waitForSelector(`div[data-testid=\"override-inputs\"] >> input >> nth=${inputNumber}`);
    return await element.inputValue();
  };

  const startDate = await getInputValue(0);
  const startTime = await getInputValue(1);

  const endDate = await getInputValue(2);
  const endTime = await getInputValue(3);

  const startDateTime = dayjs(`${startDate} ${startTime}`, 'MM/DD/YYYY HH:mm');
  const endDateTime = dayjs(`${endDate} ${endTime}`, 'MM/DD/YYYY HH:mm');

  return {
    start: startDateTime,
    end: endDateTime,
  };
};
