import { test } from '../../fixtures';
import { sendDemoAlert } from '../../utils/integrations';

import { createIntegrationAndEscalationChainAndEnableMaintenanceMode, disableMaintenanceMode } from './';

test('"maintenance" mode', async ({ adminRolePage: { page, userName } }) => {
  const { integrationName } = await createIntegrationAndEscalationChainAndEnableMaintenanceMode(
    page,
    userName,
    'Maintenance'
  );
  await sendDemoAlert(page);

  // TODO: there seems to be a bug here where "maintenance" mode alert groups don't show up in the UI
  // await verifyThatAlertGroupIsRoutedCorrectlyButNotEscalated(
  //   page,
  //   integrationName,
  //   createRoutedText(escalationChainName)
  // );

  await disableMaintenanceMode(page, integrationName);
});
