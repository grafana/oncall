const { When, Given, Before, AfterAll, Then, After, setDefaultTimeout } = require('@cucumber/cucumber');
const { Builder, By, until } = require('selenium-webdriver');

const { takeScreenshot } = require('../../utils/takeScreenshot');

const { setup, checkTitle } = require('./common');

const assert = require('assert');

When('Open settings page', async function () {
  const menuItem = await this.driver.findElement(By.className('TEST-settings-menu-item'));

  menuItem.click();
});

Then('We see settings page', async function () {
  this.driver.wait(until.elementLocated(By.className('TEST-alert-rules')));
});

When('Click Add new Escalation chain', async function () {
  const button = await this.driver.findElement(By.className('TEST-add-new-chain-button'));

  button.click();
});

Then('We see new Escalation chain popup', async function () {
  await this.driver.wait(until.elementLocated(By.className('TEST-channel-filter-form')));

  await this.driver.sleep(3000);
});

When('We input Filtering Term', async function () {
  await this.driver
    .findElement(By.className('TEST-filtering-term-input'))
    .sendKeys('CUCUMBER ' + Math.random().toFixed(2) * 100);

  await this.driver.sleep(3000);
});

When('Click Create', async function () {
  const button = await this.driver.findElement(By.className('TEST-create-channel-filter-form-button'));

  button.click();

  await this.driver.sleep(8000);
});
