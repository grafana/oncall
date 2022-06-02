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
} = require('@cucumber/cucumber');
const seleniumWebdriver = require('selenium-webdriver');
const { Builder, By, until } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

function CustomWorld({ attach, parameters }) {
  this.attach = attach;
  this.parameters = parameters;

  var options = new chrome.Options();

  options.addArguments('headless');
  options.addArguments('window-size=1440,900');

  this.driver = new Builder().forBrowser('chrome').build();

  this.driver.manage().window().maximize();

  this.driver.manage().setTimeouts({ implicit: 4000 });

  // Returns a promise that resolves to the element
  this.waitForElement = function (locator) {
    const condition = seleniumWebdriver.until.elementLocated(locator);
    return this.driver.wait(condition);
  };
}

setDefaultTimeout(20 * 1000);

setWorldConstructor(CustomWorld);
