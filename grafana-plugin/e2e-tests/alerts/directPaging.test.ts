import { test, expect } from '../fixtures';
import { clickButton, fillInInput } from '../utils/forms';
import { goToOnCallPage } from '../utils/navigation';

/**
 * TODO: test that we can also direct page a team. This is a bit more involved because we need to
 * create a team via the Grafana API then go and configure the team's direct paging integration so that
 * it will show up in the dropdown (ie. create an escalation chain and assign it to the integration)
 */

test.only('we can directly page a user', async ({ adminRolePage }) => {
  const message = 'Help me please!';
  const { page } = adminRolePage;

  await goToOnCallPage(page, 'alert-groups');
  await clickButton({ page, buttonText: 'Escalation' });

  await fillInInput(page, 'textarea[name="message"]', message);
  await clickButton({ page, buttonText: 'Invite' });

  const addRespondersPopup = page.getByTestId('add-responders-popup');

  await addRespondersPopup.getByText('Users').click();
  await addRespondersPopup.getByText(adminRolePage.userName).click();

  await clickButton({ page, buttonText: 'Create' });

  // Check we are redirected to the alert group page
  await page.waitForURL('**/alert-groups/I*'); // Alert group IDs always start with "I"
  await expect(page.getByTestId('incident-message')).toContainText(message);
});
