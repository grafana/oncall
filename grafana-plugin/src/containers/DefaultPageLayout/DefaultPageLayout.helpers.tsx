import React from 'react';

import { PluginLink } from 'components/PluginLink/PluginLink';
import { RenderConditionally } from 'components/RenderConditionally/RenderConditionally';
import { Organization } from 'models/organization/organization.types';

import { SlackError } from './DefaultPageLayout.types';

export function getSlackMessage(slackError: SlackError, organization: Organization, hasLiveSettingsFeature: boolean) {
  if (slackError === SlackError.WRONG_WORKSPACE) {
    return (
      <>
        Couldn't connect Slack.
        <RenderConditionally
          shouldRender={Boolean(organization?.slack_team_identity)}
          render={() => (
            <>
              {' '}
              Select <b>{organization.slack_team_identity.cached_name}</b> workspace when connecting please
            </>
          )}
        />
      </>
    );
  }

  if (slackError === SlackError.USER_ALREADY_CONNECTED) {
    return (
      <>Couldn't connect to Slack. This Slack account has already been connected to another user in this organization</>
    );
  }

  if (slackError === SlackError.AUTH_FAILED) {
    return (
      <>
        An error has occurred with Slack authentication.{' '}
        {hasLiveSettingsFeature && (
          <>
            <PluginLink query={{ page: 'live-settings' }}>Check ENV variables</PluginLink> related to Slack and try
            again please.
          </>
        )}
      </>
    );
  }

  if (slackError === SlackError.REGION_ERROR) {
    return (
      <>Couldn't connect to Slack. Slack workspace has already been connected to OnCall instance in another region.</>
    );
  }

  return <>Couldn't connect Slack.</>;
}
