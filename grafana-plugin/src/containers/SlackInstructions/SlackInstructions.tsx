import React, { FC } from 'react';

import { Button, VerticalGroup, Icon, Field, Input } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import Block from 'components/GBlock/Block';
import Text from 'components/Text/Text';
import { SlackNewIcon } from 'icons';
import { DOCS_SLACK_SETUP } from 'utils/consts';

import styles from './SlackInstructions.module.css';

const cx = cn.bind(styles);

interface SlackInstructionsProps {}
/* This component will be used when we will work on moving ENV variables to chat-ops, but we need to do work on backend side first */
const SlackInstructions: FC<SlackInstructionsProps> = observer(() => {
  return (
    <div>
      <VerticalGroup spacing="lg">
        <Text.Title level={2}>Connect Slack workspace</Text.Title>

        <Block bordered withBackground className={cx('slack-infoblock')}>
          <VerticalGroup align="center" spacing="lg">
            <SlackNewIcon />
            <Text>You can manage alert groups in your Slack workspace. </Text>
            <Text>Before start you need to connect your Slack bot to Grafana OnCall.</Text>
            <Text type="secondary">
              For bot creating instructions and additional information please read{' '}
              <a href={DOCS_SLACK_SETUP} target="_blank" rel="noreferrer">
                <Text type="link">our documentation</Text>
              </a>
            </Text>{' '}
          </VerticalGroup>
        </Block>
        <Text>Setup environment</Text>
        <Text>
          Create OnCall Slack bot using{' '}
          <a href={DOCS_SLACK_SETUP} target="_blank" rel="noreferrer">
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
      </VerticalGroup>
    </div>
  );
});

export default SlackInstructions;
