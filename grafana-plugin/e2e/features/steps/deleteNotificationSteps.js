const { When, Given, Before, Then, After, setDefaultTimeout } = require('@cucumber/cucumber');
const { Builder, By, until } = require('selenium-webdriver');

const { takeScreenshot } = require('../../utils/takeScreenshot');

const { setup, checkTitle } = require('./common');

const assert = require('assert');

When('Go to my settings page', async function () {
  var menuItem = await this.driver.findElement(By.className('TEST-users-menu-item'));

  menuItem.click();

  this.driver.sleep(3000);
});

Then('We see my settings page', async function f() {
  await this.driver.wait(until.elementLocated(By.className('TEST-users-page')));
});

When('Click edit button', async function () {
  const editButton = await this.driver.findElement(By.className('TEST-edit-my-own-settings-button'));

  editButton.click();
});

Then('We see settings popup', async function () {
  await this.driver.findElement(By.className('TEST-user-settings-modal'));

  this.driver.sleep(3000);
});

When('Delete all notification policies', async function () {
  const deleteNotificationButtons = await this.driver.findElements(
    By.className('TEST-delete-notification-policy-button')
  );

  await (async function () {
    for (const item of deleteNotificationButtons) {
      await (async function () {
        return new Promise((resolve) =>
          setTimeout(() => {
            item.click();
            resolve();
          }, 1500)
        );
      })();
    }
  })();
});
