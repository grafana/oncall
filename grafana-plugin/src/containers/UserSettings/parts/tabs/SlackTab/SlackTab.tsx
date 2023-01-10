import React, { useCallback } from 'react';

import { Button, VerticalGroup, Icon } from '@grafana/ui';
import cn from 'classnames/bind';

import Block from 'components/GBlock/Block';
import Text from 'components/Text/Text';
import { SlackNewIcon } from 'icons';
import { useStore } from 'state/useStore';

import styles from './SlackTab.module.css';

const cx = cn.bind(styles);

export const SlackTab = () => {
  const { slackStore } = useStore();

  const handleClickConnectSlackAccount = useCallback(() => {
    slackStore.slackLogin();
  }, [slackStore]);

  return (
    <VerticalGroup spacing="lg">
      <Block bordered withBackground className={cx('slack-infoblock', 'personal-slack-infoblock')}>
        <VerticalGroup align="center" spacing="lg">
          <SlackNewIcon />
          <Text>
            Personal Slack connection will allow you to manage alert groups in your connected team Internal Slack
            workspace.
          </Text>
          <Text>To setup personal Slack click the button below, choose workspace and click Allow.</Text>

          <Text type="secondary">
            More details in{' '}
            <a href="https://grafana.com/docs/grafana-cloud/oncall/open-source/#slack-setup">
              <Text type="link">our documentation</Text>
            </a>
          </Text>

          <img
            style={{ height: '350px', display: 'block', margin: '0 auto' }}
            src="public/plugins/grafana-oncall-app/img/slack_instructions.png"
          />
        </VerticalGroup>
      </Block>
      <Button onClick={handleClickConnectSlackAccount}>
        <Icon name="external-link-alt" className={cx('external-link-style')} /> Open Slack connection page
      </Button>
    </VerticalGroup>
  );
};
