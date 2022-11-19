import React, { FC, useCallback, useState } from 'react';

import { Button, Field, Form, Input } from '@grafana/ui';
import cn from 'classnames/bind';
import { isEmpty } from 'lodash-es';
import { SubmitHandler } from 'react-hook-form';

import Block from 'components/GBlock/Block';
import Text from 'components/Text/Text';
import PluginState from 'state/plugin';

import styles from './ConfigurationForm.module.css';

const cx = cn.bind(styles);

type Props = {
  onSuccessfulSetup: () => void;
  defaultOnCallApiUrl: string;
};

type FormProps = {
  onCallApiUrl: string;
};

/**
 * https://stackoverflow.com/a/43467144
 */
const isValidUrl = (url: string): boolean => {
  try {
    new URL(url);
    return true;
  } catch (_) {
    return false;
  }
};

const FormErrorMessage: FC<{ errorMsg: string }> = ({ errorMsg }) => (
  <>
    <pre>
      <Text type="link">{errorMsg}</Text>
    </pre>
    <Block withBackground className={cx('info-block')}>
      <Text type="secondary">
        Need help?
        <br />- Reach out to the OnCall team in the{' '}
        <a href="https://grafana.slack.com/archives/C02LSUUSE2G" target="_blank" rel="noreferrer">
          <Text type="link">#grafana-oncall</Text>
        </a>{' '}
        community Slack channel
        <br />- Ask questions on our GitHub Discussions page{' '}
        <a href="https://github.com/grafana/oncall/discussions/categories/q-a" target="_blank" rel="noreferrer">
          <Text type="link">here</Text>
        </a>{' '}
        <br />- Or file bugs on our GitHub Issues page{' '}
        <a href="https://github.com/grafana/oncall/issues" target="_blank" rel="noreferrer">
          <Text type="link">here</Text>
        </a>
      </Text>
    </Block>
  </>
);

const ConfigurationForm: FC<Props> = ({ onSuccessfulSetup, defaultOnCallApiUrl }) => {
  const [setupErrorMsg, setSetupErrorMsg] = useState<string>(null);
  const [formLoading, setFormLoading] = useState<boolean>(false);

  const setupPlugin: SubmitHandler<FormProps> = useCallback(async ({ onCallApiUrl }) => {
    setFormLoading(true);

    const errorMsg = await PluginState.selfHostedInstallPlugin(onCallApiUrl, false);

    if (!errorMsg) {
      onSuccessfulSetup();
    } else {
      setSetupErrorMsg(errorMsg);
      setFormLoading(false);
    }
  }, []);

  return (
    <Form<FormProps>
      defaultValues={{ onCallApiUrl: defaultOnCallApiUrl }}
      onSubmit={setupPlugin}
      data-testid="plugin-configuration-form"
    >
      {({ register, errors }) => (
        <>
          <div className={cx('info-block')}>
            <p>1. Launch the OnCall backend</p>
            <Text type="secondary">
              Run hobby, dev or production backend. See{' '}
              <a href="https://github.com/grafana/oncall#getting-started" target="_blank" rel="noreferrer">
                <Text type="link">here</Text>
              </a>{' '}
              on how to get started.
            </Text>
          </div>

          <div className={cx('info-block')}>
            <p>2. Let us know the base URL of your OnCall API</p>
            <Text type="secondary">
              The OnCall backend must be reachable from your Grafana installation. Some examples are:
              <br />
              - http://host.docker.internal:8080
              <br />- http://localhost:8080
            </Text>
          </div>

          <Field label="OnCall backend URL" invalid={!!errors.onCallApiUrl} error="Must be a valid URL">
            <Input
              data-testid="onCallApiUrl"
              {...register('onCallApiUrl', {
                required: true,
                validate: isValidUrl,
              })}
            />
          </Field>

          {setupErrorMsg && <FormErrorMessage errorMsg={setupErrorMsg} />}

          <Button type="submit" size="md" disabled={formLoading || !isEmpty(errors)}>
            Connect
          </Button>
        </>
      )}
    </Form>
  );
};

export default ConfigurationForm;
