import type { Locator, Page } from '@playwright/test';
import { randomUUID } from 'crypto';

type SelectorType = 'gSelect' | 'grafanaSelect';
type SelectDropdownValueArgs = {
  page: Page;
  value: string;
  // if set, search for a dropdown that contains this text as its placeholder
  placeholderText?: string;
  // specifies which type of select dropdown we are dealing with (since we currently mix-and-match 3 different components...)
  selectType?: SelectorType;
  // if provided, use this Locator as the root of our search for the dropdown
  startingLocator?: Locator;
  // if true, when selecting the dropdown option, use an exact match, otherwise use a substring contains match
  optionExactMatch?: boolean;
};

type ClickButtonArgs = {
  page: Page;
  buttonText: string;
  // if provided, use this Locator as the root of our search for the button
  startingLocator?: Locator;
};

export const fillInInput = (page: Page, selector: string, value: string) => page.fill(selector, value);

export const fillInInputByPlaceholderValue = (page: Page, placeholderValue: string, value: string) =>
  fillInInput(page, `input[placeholder*="${placeholderValue}"]`, value);

export const getInputByName = (page: Page, name: string): Locator => page.locator(`input[name="${name}"]`);

export const clickButton = async ({ page, buttonText, startingLocator }: ClickButtonArgs): Promise<void> => {
  const button = (startingLocator || page).locator(`button >> text=${buttonText}`);
  await button.waitFor({ state: 'visible' });
  await button.click();
};

/**
 * at a minimum must specify selectType OR placeholderText
 * if both are specified selectType takes precedence
 */
const openSelect = async ({
  page,
  placeholderText,
  selectType,
  startingLocator,
}: SelectDropdownValueArgs): Promise<void> => {
  /**
   * we currently mix three different dropdown components in the UI..
   * so we need to support all of them :(
   */
  const dropdownSelectors: Record<SelectorType, string> = {
    gSelect: 'div[class*="GSelect"]',
    grafanaSelect: `div[class*="grafana-select-value-container"] ${
      placeholderText ? `>> text=${placeholderText} ` : ''
    }>> ..`,
  };

  const dropdownSelector = dropdownSelectors[selectType];
  const placeholderSelector = `text=${placeholderText}`;
  const selector = dropdownSelector || placeholderSelector;

  const selectElement: Locator = (startingLocator || page).locator(selector);
  await selectElement.waitFor({ state: 'visible' });
  await selectElement.click();
};

const chooseDropdownValue = async ({
  page,
  value,
  optionExactMatch = true,
}: SelectDropdownValueArgs): Promise<void> => {
  // notice the difference in double quotes - https://playwright.dev/docs/selectors#text-selector
  const textMatchSelector = optionExactMatch ? `text="${value}"` : `text=${value}`;
  await page.locator(`div[id^="react-select-"][id$="-listbox"] >> ${textMatchSelector}`).click();
};

export const selectDropdownValue = async (args: SelectDropdownValueArgs): Promise<void> => {
  await openSelect(args);
  await chooseDropdownValue(args);
};

export const generateRandomValue = (): string => randomUUID();
