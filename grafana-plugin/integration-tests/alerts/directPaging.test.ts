import { test } from '../fixtures';
import { clickButton, fillInInput, selectDropdownValue } from '../utils/forms';
import { goToOnCallPage } from "../utils/navigation";
import { verifyAlertGroupTitleAndMessageContainText } from "../utils/alertGroup";

test('we can create an alert group for default team', async ({ adminRolePage }) => {
  const { page } = adminRolePage;

  await goToOnCallPage(page, 'alert-groups');
  await clickButton({ page, buttonText: 'New alert group' });

  await fillInInput(page, 'input[name="title"]', "Help me!");
  await fillInInput(page, 'textarea[name="message"]', "Help me please!");

  await selectDropdownValue({
    page,
    selectType: 'grafanaSelect',
    placeholderText: "Select team",
    value: "No team",
  });

  await clickButton({ page, buttonText: 'Create' });

  // Check we are redirected to the alert group page
  await page.waitForURL('**/alert-groups/I*');  // Alert group IDs always start with "I"
  await verifyAlertGroupTitleAndMessageContainText(page, "Help me!", "Help me please!")
});
