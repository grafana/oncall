import express from 'express';
import ngrok from 'ngrok';

import { expect, test } from '../fixtures';
import { clickButton, generateRandomValue } from '../utils/forms';
import { goToOnCallPage } from '../utils/navigation';
import { checkWebhookPresenceInTable } from '../utils/outgoingWebhooks';
import { EscalationStep, createEscalationChain } from '../utils/escalationChain';
import { createIntegrationAndSendDemoAlert } from '../utils/integrations';

const createWebhook = async ({ page, webhookName, webhookUrl }) => {
  await goToOnCallPage(page, 'outgoing_webhooks');

  await clickButton({ page, buttonText: 'New Outgoing Webhook' });

  await page.getByText('Simple').first().click();

  await page.waitForTimeout(2000);

  await page.keyboard.insertText(webhookUrl);
  await page.locator('[name=name]').fill(webhookName);
  await page.getByLabel('New Outgoing Webhook').getByRole('img').nth(1).click(); // Open team dropdown
  await page.getByLabel('Select options menu').getByText('No team').click();
  await clickButton({ page, buttonText: 'Create' });
};

test.describe('simple webhook', () => {
  test('Create and check it is displayed on the list correctly', async ({ adminRolePage: { page } }) => {
    const webhookName = generateRandomValue();
    await createWebhook({ page, webhookName, webhookUrl: 'https://example.com' });
    await checkWebhookPresenceInTable({ page, webhookName, expectedTriggerType: 'Escalation step' });
  });

  test('Create and check that our webhook actually receives the payload', async ({ adminRolePage: { page } }) => {
    const escalationChainName = generateRandomValue();
    const integrationName = generateRandomValue();
    const PORT = 5050;

    /**
     * This is a simple express server that listens for outgoing webhook requests
     * ngrok is used to expose this server to the internet, to make it easier for the backend to be able to send
     * requests to it
     */
    let resolveRequest: (value: unknown) => void;
    const requestPromise = new Promise<any>((resolve) => {
      resolveRequest = resolve;
    });

    const app = express();
    app.use(express.json());
    app.post('/', (req, res) => {
      resolveRequest(req.body); // Resolve the promise with the request body
      res.send('ok');
    });
    app.listen(PORT);

    const webhookUrl = await ngrok.connect(PORT);
    const webhookName = generateRandomValue();

    await createWebhook({ page, webhookName, webhookUrl });

    await createEscalationChain(page, escalationChainName, EscalationStep.TriggerWebhook, webhookName);
    await createIntegrationAndSendDemoAlert(page, integrationName, escalationChainName);

    /**
     * Wait for the request to be received on our express server's endpoint handler
     * when the request is received, the promise will be resolved w/ the request body
     */
    const payload = await requestPromise;

    expect(payload.alert_group.state).toEqual('firing');
    expect(payload.alert_payload.message).toEqual('This alert was sent by user for demonstration purposes');
    expect(payload.integration.name).toEqual(`${integrationName} - Webhook`);
    expect(payload.integration.type).toEqual('webhook');
  });
});
