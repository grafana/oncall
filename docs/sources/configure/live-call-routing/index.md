---
title: Configure SMS & call routing with Grafana OnCall
menuTitle: Configure SMS & call routing
description: A step-by-step guide on how to configure SMS & call routing with Grafana OnCall and Twilio.
weight: 300
keywords:
  - OnCall
  - Live call routing
  - Twilio
  - SMS routing
  - Phone call routing
  - Webhook integration
canonical: https://grafana.com/docs/oncall/latest/configure/live-call-routing/
aliases:
  - /docs/grafana-cloud/alerting-and-irm/oncall/configure/escalation-chains-and-routes/
  - ../live-call-routing/ # /docs/oncall/<ONCALL_VERSION>/escalation-chains-and-routes/
---

# Configure SMS & call routing with Grafana OnCall

This guide walks you through configuring a system that enables you to page on-call personnel via phone call and SMS message using Grafana OnCall and Twilio.

## Before you begin

Before you begin, ensure you have the following:

- Grafana Cloud account: If you haven't already, [sign up for Grafana Cloud](https://grafana.com/auth/sign-up/create-user).
Grafana OnCall user with administrator privileges.
Twilio account: [Sign up for Twilio](https://www.twilio.com/try-twilio).

## Basic setup

In the basic setup, you'll create an integration in OnCall and configure a phone number in Twilio.
This setup allows you to receive alerts from SMS messages or phone calls made to your Twilio phone number.
We’ll expand this setup as we go.

<!--- [Visual diagram to represent the OnCall/Twilio flow] --->

### Grafana OnCall setup

To complete the Grafana OnCall portion of the configuration, ensure you have:

- Grafana OnCall user account with administrator privileges.
- Configured notification settings for your user to test functionality along the way.

If you need to set these up first, refer to the Grafana OnCall documentation.

#### Setup webhook integration

Create a new integration to establish an endpoint for receiving alerts and connecting them to routes and escalation chains.
The [generic webhook integration](/docs/grafana-cloud/alerting-and-irm/oncall/integrations/webhook/)
accepts any payload and allows for customization of how the payload is handled in OnCall.

To create the integration:

1. In Grafana Cloud, navigate to **Alerts & IRM** -> **OnCall** -> **Integrations**.
1. Click **+ New Integration**.
1. Choose **Webhook (Generic)** as the integration type.
1. Provide a name, description, and optionally assign it to a team.
1. Note the integration URL for future use in Twilio.

#### Add an Escalation Chain

An escalation chain defines a sequence of notifications and other actions once an alert has been received in OnCall.

Create a simple escalation chain to directly notify your user for testing during the setup process:

1. Go to **Alerts & IRM** -> **OnCall** -> **Escalation chains**.
2. Click **+ New Escalation chain**.
3. Provide a name and click **Create Escalation Chain**.
4. For step 1, choose **Notify users** and select your user.

Later, you can customize the escalation chain as needed.

#### Connect and test the Escalation Chain

Connect the escalation chain to the newly created integration and then test that the setup is working correctly.

1. Return to the Webhook integration.
1. In the integration details, under Routes, assign the new escalation chain as the Default route using the dropdown.
1. Click **Send demo alert** and verify that you receive a notification as expected.
1. Resolve the demo alert.

Next, switch to Twilio to set up the other side of the integration.

### Twilio setup

A Twilio account is required to complete the steps in this section. (Sign-up).

In this section, you’ll set up the following:

- A Twilio phone number
- Twilio Studio Flows to send information as an alert to Grafana OnCall.

#### Set up Studio Flow

Utilize Twilio's Studio Flow to capture alert information from SMS messages and phone calls to send it to Grafana OnCall:

1. In Twilio, navigate to **Develop** -> **Studio** -> **Flows**.
If Studio isn’t visible, select **Explore Products** and navigate to Studio under the **Developer Tools** section.
1. Select **Create new Flow**, enter a Flow name, and click **Next**.
1. Select **Import from JSON** and click **Next**.
1. Import the provided JSON, replacing `<YOUR_INTEGRATION_URL>` (Lines 54 and 156) with the webhook integration URL from Grafana OnCall.
1. After adding your webhook URL, click **Next**.
1. Review the flow and click **Publish** to make the flow available for use.

#### Understand your flow

The flow you created has the following two paths:

- SMS Path: Accepts incoming messages and forwards their contents to Grafana OnCall via the Webhook URL, including the sender's phone number.
- Voice Path: Converts voice calls to text and sends them to the Webhook integration in Grafana OnCall.

<!--- Screenshot of Twilio flow --->

#### Buy a Twilio phone number

Purchase a phone number in Twilio to receive calls and messages:

1. Go to **Develop** -> **# Phone Numbers** -> **Manage** -> **Buy a number**.
If you don’t see Phone Numbers, select **Explore Products** -> **Super Network** -> **Phone Numbers**.
1. Search for a number in your desired country code, select one, and buy it.
1. Once purchased, the number will be available in **Active Numbers**.

{{< admonition type="note" >}}
Some countries and regions may require additional information to purchase a phone number such as address, contact person, etc.
{{< /admonition >}}

#### Configure the phone number

Configure your Twilio phone number to use the Studio Flow created earlier.

1. In **Develop** -> **Phone Numbers** -> **Manage** -> **Active Numbers**, select the purchased number.
1. Configure Voice: Set the dropdown `A call comes in` to `Studio Flow`. Then select the flow we created.
1. Configure Messaging: Set the dropdown `A message comes in` to `Studio Flow`. Then select the flow we created.
1. Save the configuration.

#### Test and troubleshoot

Test configuration via SMS:

- Send an SMS message to the purchased number and verify that you receive an “Alert sent” success notification.
- Shortly after that, verify that you received a notification from Grafana OnCall using your configured method.

Test configuration via phone call:

- Call the purchased number, follow the instructions to describe your alert, and verify that you hear a message that the alert was sent successfully.
- Confirm that you receive a notification from Grafana OnCall using your configured method.

If you encounter issues:

- Ensure the correct integration URL is configured.
- Check the configuration of your Twilio Studio Flow.
Confirm that “A message comes in” and “A call comes in” are configured correctly for the Phone number.
- Review execution logs in Twilio Studio.
In Studio -> Flows, select the flow you created and view Execution Log.
- Review Grafana OnCall escalation log.
Verify if an alert group was created in OnCall. If not, the alert didn’t make it to the URL. If there is an alert group, view the escalation log to review what happened.

### Basic setup complete

You've completed the basic setup to receive alerts via SMS and phone calls in Grafana OnCall.

Explore the advanced configuration section to learn how to further enhance your setup by routing alerts to different escalation chains.
