import { test } from '../../fixtures';
import { verifyThatAlertGroupIsRoutedCorrectlyButNotEscalated } from '../../utils/alertGroup';
import { sendDemoAlert } from '../../utils/integrations';

import {
  createIntegrationAndEscalationChainAndEnableMaintenanceMode,
  createRoutedText,
  disableMaintenanceMode,
} from './';

test('debug mode', async ({ adminRolePage: { page, userName } }) => {
  const { escalationChainName, integrationName } = await createIntegrationAndEscalationChainAndEnableMaintenanceMode(
    page,
    userName,
    'Debug'
  );
  await sendDemoAlert(page);
  await verifyThatAlertGroupIsRoutedCorrectlyButNotEscalated(
    page,
    integrationName,
    createRoutedText(escalationChainName)
  );

  await disableMaintenanceMode(page, integrationName);
});
