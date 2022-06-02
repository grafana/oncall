let fs = require('fs');

async function takeScreenshot(driver) {
  const encodedString = await driver.takeScreenshot();
  await fs.writeFileSync('./image.png', encodedString, 'base64');
}

module.exports = {
  takeScreenshot,
};
