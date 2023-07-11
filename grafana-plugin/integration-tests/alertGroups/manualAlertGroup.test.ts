import { test } from '../fixtures';
import { generateRandomValue } from '../utils/forms';
import { goToOnCallPage } from '../utils/navigation';

test.only('we can create a manual alert group', async ({ adminRolePage }) => {
  const { page, userName } = adminRolePage;
  const alertGroupName = generateRandomValue();
  const alertGroupDescription = generateRandomValue();

  await goToOnCallPage(page, 'incidents');

  // open the manual alert group drawer
  await page.getByTestId('new-manual-alert-group-button').click();

  // // add a responder by clicking the button and waiting for the popup to show up
  // await page.getByTestId('assign-responders-button').click();
  // const escalationVariantsPopup = page.getByTestId('escalation-variants-popup');
  // await escalationVariantsPopup.waitFor({ state: 'visible' });

  // // select the Users radio button, type in our user's username, then select them from the list
  // await escalationVariantsPopup.locator(`label >> text=Users`).click();
  // await escalationVariantsPopup.getByTestId('escalation-variants-user-input').type(userName);
  // await escalationVariantsPopup
  //   .getByTestId('escalation-variants-user-table')
  //   .locator(`table >> text=${userName}`)
  //   .click();

  // // confirm to add the responder
  // await page.getByTestId('user-warning-confirm-button').click();

  // fill out the form
  const manualAlertGroupForm = page.getByTestId('manual-alert-group-form');

  await manualAlertGroupForm.locator('input[name="title"]').type(alertGroupName);
  await manualAlertGroupForm.locator('textarea[name="message"]').type(alertGroupDescription);
  await manualAlertGroupForm.locator('button >> text=Create').click();

  // await verifyThatAlertGroupIsTriggered(page, integrationName, `Notify on-call from Schedule '${onCallScheduleName}'`);
});
