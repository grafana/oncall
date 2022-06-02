const {
  setWorldConstructor,
  When,
  Given,
  Before,
  Then,
  After,
  setDefaultTimeout,
  AfterAll,
  BeforeAll,
  BeforeStep,
} = require('@cucumber/cucumber');
const { Builder, By, until } = require('selenium-webdriver');
const seleniumWebdriver = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

const assert = require('assert');

const AMIXR_DOMAIN = process.env.AMIXR_DOMAIN || 'develop.amixr.io';

Before({ tags: '@main' }, login);
After(clear);

async function login() {
  await this.driver.get(`https://${AMIXR_DOMAIN}/app/auth/login`);

  await this.driver.wait(until.elementLocated(By.className('TEST-login-email')));

  await this.driver.findElement(By.className('TEST-login-email')).sendKeys(process.env.USER_EMAIL);

  await this.driver.findElement(By.className('TEST-login-password')).sendKeys(process.env.PASSWORD);

  await this.driver.findElement(By.className('TEST-login-button')).click();

  await this.driver.sleep(8000);
}

async function setup() {
  await this.driver.get(`https://${AMIXR_DOMAIN}`);

  await this.driver.manage().addCookie({
    name: 'jwt',
    value: process.env.JWT,
    path: '/',
    domain: AMIXR_DOMAIN,
    secure: true,
    httpOnly: true,
  });

  await this.driver.navigate().to(`https://${AMIXR_DOMAIN}/app/`);
}

async function clear() {
  await this.driver.close();
}

async function checkTitle() {
  /* var productElements = await this.driver.findElements(
        By.className('product')
    );*/

  const title = await this.driver.getTitle();

  assert.strictEqual(title, 'Alert Mixer (Amixr)');

  /*var expectations = dataTable.hashes();
    for (let i = 0; i < expectations.length; i++) {
        const productName = await productElements[i]
            .findElement(By.tagName('h3'))
            .getText();
        assert.equal(productName, expectations[i].name);

        const description = await productElements[i]
            .findElement(By.tagName('p'))
            .getText();
        assert.equal(
            description,
            `Description: ${expectations[i].description}`
        );
    }*/
}
module.exports = {
  setup,
  checkTitle,
};
