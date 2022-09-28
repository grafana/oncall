import React, { useCallback, useState, FC } from 'react';
import { SlackNewIcon } from '../../icons';
import { Button, VerticalGroup, Icon, Field, Input } from '@grafana/ui';
import { observer } from 'mobx-react';
import cn from 'classnames/bind';

import Text from 'components/Text/Text';
import Block from 'components/GBlock/Block';

import styles from './SlackInstructions.module.css';

const cx = cn.bind(styles);

interface SlackInstructionsProps {}

const SlackInstructions: FC<SlackInstructionsProps> = observer((props) => {
  return (
    <div>
      <SlackNewIcon />
      {/* <VerticalGroup spacing="lg">
        <Text.Title level={2}>Setup Slack workspace</Text.Title>
        <Block bordered withBackground className={cx('slack-infoblock')}>
          <VerticalGroup align="center" spacing="lg">
            <Text>You can manage incidents in your Slack workspace. </Text>
            <Text>Before start you need to connect your Slack bot to Grafana OnCall.</Text>
            <Text type="secondary">
              For bot creating instructions and additional information please read{' '}
              <a href="https://grafana.com/docs/grafana-cloud/oncall/open-source/#slack-setup">
                <Text type="link">our documentation</Text>
              </a>
            </Text>{' '}
          </VerticalGroup>
        </Block>
        <Text>Setup environment</Text>
        <Text>
          Create OnCall Slack bot using{' '}
          <a href="https://grafana.com/docs/grafana-cloud/oncall/open-source/#slack-setup">
            <Text type="link">our instructions</Text>
          </a>{' '}
          and fill out app credentials below.
        </Text>
        <div className={cx('slack-infoblock')}>
          <Field label="App ID">
            <Input id="appId" onChange={() => {}} defaultValue={'appId'} />
          </Field>
          <Field label="Client secret">
            <Input id="clientsecret" onChange={() => {}} defaultValue={'clientsecret'} />
          </Field>
          <Field label="Signing secret">
            <Input id="signingsecret" onChange={() => {}} defaultValue={'signingsecret'} />
          </Field>
          <Field label="Redirect host">
            <Input id="host" onChange={() => {}} defaultValue={'https://'} />
          </Field>
        </div>
        <Block bordered withBackground className={cx('slack-infoblock')}>
          <Text type="secondary">
            <Icon name="info-circle" /> Your host to Slack must start with “https://” and be publicly available (meaning
            that it can be reached by Slack servers). If your host is private or local, you can use redirecting services
            like Ngrok.
          </Text>
        </Block>
        <Button onClick={() => {}}>Save environment</Button>
      </VerticalGroup> */}
    </div>
  );
});

export default SlackInstructions;
