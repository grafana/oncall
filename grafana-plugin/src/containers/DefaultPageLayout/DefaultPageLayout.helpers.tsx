import React from 'react';

import PluginLink from 'components/PluginLink/PluginLink';
import { Team } from 'models/team/team.types';
import { RootStore } from 'state';
import { AppFeature } from 'state/features';

import { SlackError } from './DefaultPageLayout.types';

export function getSlackMessage(slackError: SlackError, team: Team, store: RootStore) {
  if (slackError === SlackError.WRONG_WORKSPACE) {
    return (
      <>
        Couldn't connect Slack.
        {Boolean(team?.slack_team_identity) && (
          <>
            {' '}
            Select <b>{team.slack_team_identity.cached_name}</b> workspace when connecting please
          </>
        )}
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
        {store.hasFeature(AppFeature.LiveSettings) && (
          <>
            <PluginLink query={{ page: 'live-settings' }}>Check ENV variables</PluginLink> related to Slack and try
            again please.
          </>
        )}
      </>
    );
  }

  return <>Couldn't connect Slack.</>;
}
