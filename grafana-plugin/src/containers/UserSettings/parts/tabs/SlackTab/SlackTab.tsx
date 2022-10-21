import React, { useCallback } from 'react';

import { Button, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';

import Text from 'components/Text/Text';
import { useStore } from 'state/useStore';

import styles from './SlackTab.module.css';

const cx = cn.bind(styles);

export const SlackTab = () => {
  const { slackStore } = useStore();

  const handleClickConnectSlackAccount = useCallback(() => {
    slackStore.slackLogin();
  }, [slackStore]);

  return (
    <VerticalGroup>
      <Text>
        You can view your Slack Workspace at the top-right corner after you are redirected. It should be a Workspace
        with App Bot installed:
      </Text>
      <img
        style={{ height: '350px', display: 'block', margin: '0 auto' }}
        src="public/plugins/grafana-oncall-app/img/slack_workspace_choose_attention.png"
      />
      <div className={cx('footer')}>
        <Button key="back" onClick={handleClickConnectSlackAccount}>
          I'll check! Proceed to Slack...
        </Button>
      </div>
    </VerticalGroup>
  );
};
