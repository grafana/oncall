import React, { useCallback } from 'react';

import { Button, VerticalGroup, Icon } from '@grafana/ui';
import cn from 'classnames/bind';

import Block from 'components/GBlock/Block';
import Text from 'components/Text/Text';
import { WithPermissionControlDisplay } from 'containers/WithPermissionControl/WithPermissionControlDisplay';
import { SlackNewIcon } from 'icons';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization';
import { DOCS_SLACK_SETUP } from 'utils/consts';

import styles from './SlackTab.module.css';

const cx = cn.bind(styles);

export const SlackTab = () => {
  const { slackStore } = useStore();

  const handleClickConnectSlackAccount = useCallback(() => {
    slackStore.slackLogin();
  }, [slackStore]);

  return (
    <WithPermissionControlDisplay userAction={UserActions.UserSettingsWrite}>
      <VerticalGroup spacing="lg">
        <Block bordered withBackground className={cx('slack-infoblock', 'personal-slack-infoblock')}>
          <VerticalGroup align="center" spacing="lg">
            <SlackNewIcon />
            <Text>
              Personal Slack connection will allow you to manage alert groups in your connected team's Internal Slack
              workspace.
            </Text>
            <Text>To setup personal Slack click the button below, choose workspace and click Allow.</Text>

            <Text type="secondary">
              More details in{' '}
              <a href={DOCS_SLACK_SETUP} target="_blank" rel="noreferrer">
                <Text type="link">our documentation</Text>
              </a>
            </Text>

            <img
              style={{ height: '350px', display: 'block', margin: '0 auto' }}
              src="public/plugins/grafana-oncall-app/assets/img/slack_instructions.png"
            />
          </VerticalGroup>
        </Block>
        <Button onClick={handleClickConnectSlackAccount}>
          <Icon name="external-link-alt" className={cx('external-link-style')} /> Open Slack connection page
        </Button>
      </VerticalGroup>
    </WithPermissionControlDisplay>
  );
};
