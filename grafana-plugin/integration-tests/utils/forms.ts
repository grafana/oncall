import type { Locator, Page } from '@playwright/test';
import { randomUUID } from 'crypto';

type SelectorType = 'gSelect' | 'reactSelect' | 'grafanaSelect';
type SelectDropdownValueArgs = {
  page: Page;
  value: string;
  // if set, search for a dropdown that contains this text as its placeholder
  placeholderText?: string;
  // specifies which type of select dropdown we are dealing with (since we currently mix-and-match 3 different components...)
  selectType?: SelectorType;
  // if provided, use this Locator as the root of our search for the dropdown
  startingLocator?: Locator;
};

export const fillInInput = (page: Page, selector: string, value: string) => page.fill(selector, value);

export const fillInInputByPlaceholderValue = (page: Page, placeholderValue: string, value: string) =>
  fillInInput(page, `input[placeholder*="${placeholderValue}"]`, value);

export const getInputByName = (page: Page, name: string): Locator => page.locator(`input[name="${name}"]`);

export const clickButton = async (page: Page, buttonText: string): Promise<void> => {
  const button = page.locator(`button >> text=${buttonText}`);
  await button.waitFor({ state: 'visible' });
  await button.click();
};

const openSelect = async ({
  page,
  placeholderText,
  selectType = 'gSelect',
  startingLocator,
}: SelectDropdownValueArgs): Promise<void> => {
  /**
   * we currently mix three different dropdown components in the UI..
   * so we need to support all of them :(
   */
  const dropdownSelectors: Record<SelectorType, string> = {
    gSelect: 'div[class*="GSelect"]',
    reactSelect: `div[id^="react-select-"][id$="-placeholder"] ${
      placeholderText ? `>> text=${placeholderText} ` : ''
    }>> ../..`,
    grafanaSelect: 'div[class*="grafana-select-value-container"] >> ..',
  };

  const selectElement: Locator = (startingLocator || page).locator(dropdownSelectors[selectType]);
  await selectElement.waitFor({ state: 'visible' });
  await selectElement.click();
};

const chooseDropdownValue = ({ page, value }: SelectDropdownValueArgs): Promise<void> =>
  page.locator(`div[id^="react-select-"][id$="-listbox"] >> text=${value}`).click();

export const selectDropdownValue = async (args: SelectDropdownValueArgs): Promise<void> => {
  await openSelect(args);
  await chooseDropdownValue(args);
};

export const generateRandomValue = (): string => randomUUID();
