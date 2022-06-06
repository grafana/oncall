import React, { useCallback, useEffect, useState } from 'react';

import { getLocationSrv, LocationUpdate } from '@grafana/runtime';
import { Field, Input, Button, Modal, HorizontalGroup, Alert, Icon, VerticalGroup, Table } from '@grafana/ui';
import cn from 'classnames/bind';

import Block from 'components/GBlock/Block';
import GTable from 'components/GTable/GTable';
import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import { User as UserType } from 'models/user/user.types';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';

import styles from './CloudPhoneSettings.module.css';

const cx = cn.bind(styles);

interface CloudPhoneSettingsProps extends WithStoreProps {}

const CloudPhoneSettings = (props: CloudPhoneSettingsProps) => {
  const [isAccountMatched, setIsAccountMatched] = useState<boolean>(true);
  const [isPhoneVerified, setIsPhoneVerified] = useState<boolean>(true);

  const signUpGrafanaCloud = () => {
    console.log('Sign UP');
  };
  const handleLinkClick = (link: string) => {
    getLocationSrv().update({ partial: false, path: link });
  };

  return (
    <VerticalGroup spacing="lg">
      <HorizontalGroup justify="space-between">
        <Text.Title level={3}>OnCall use Grafana Cloud for SMS and phone call notifications</Text.Title>
        <Button variant="secondary" icon="sync" onClick={() => handleLinkClick('fillmewithcorrectlink')}>
          Update
        </Button>
      </HorizontalGroup>
      {isAccountMatched ? (
        isPhoneVerified ? (
          <VerticalGroup spacing="lg">
            <Text>
              Your account successfully matched with the Grafana Cloud account. Please verify your phone number.{' '}
            </Text>
            <Button
              variant="secondary"
              icon="external-link-alt"
              onClick={() => handleLinkClick('fillmewithcorrectlink')}
            >
              Verify phone number in Grafana Cloud
            </Button>
          </VerticalGroup>
        ) : (
          <VerticalGroup spacing="lg">
            <Text>
              Your account successfully matched with the Grafana Cloud account. Your phone number is verified.
            </Text>
            <Button
              variant="secondary"
              icon="external-link-alt"
              onClick={() => handleLinkClick('fillmewithcorrectlink')}
            >
              Open account in Grafana Cloud
            </Button>
          </VerticalGroup>
        )
      ) : (
        <VerticalGroup spacing="lg">
          <Text>
            {'We can’t find a matching account in the connected Grafana Cloud instance (matching happens by e-mail). '}
          </Text>
          <Button variant="primary" onClick={signUpGrafanaCloud}>
            Sign up in Grafana Cloud
          </Button>
        </VerticalGroup>
      )}
    </VerticalGroup>
  );
};

export default withMobXProviderContext(CloudPhoneSettings);
