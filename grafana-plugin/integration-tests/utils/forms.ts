import type { Locator, Page } from '@playwright/test';

const fillInInput = (page: Page, selector: string, value: string) => page.fill(selector, value);

export const fillInInputByPlaceholderValue = (page: Page, placeholderValue: string, value: string) =>
  fillInInput(page, `input[placeholder="${placeholderValue}"]`, value);

export const getInputByName = (page: Page, name: string): Locator => page.locator(`input[name="${name}"]`);

export const clickButton = (page: Page, buttonText: string) => page.locator('button', { hasText: buttonText }).click();
