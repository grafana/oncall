import React, { FC } from 'react';

import { Button, VerticalGroup } from '@grafana/ui';

import { Text } from 'components/Text/Text';

type Props = {
  baseUrl: string;
  token: string;
};

export const LinkLoginButton: FC<Props> = (props: Props) => {
  const { baseUrl, token } = props;
  const mobileDeepLink = `grafana://mobile/login/link-login?oncall_api_url=${baseUrl}&token=${token}`;

  return (
    <VerticalGroup spacing="lg">
      <Text type="primary" strong>
        Sign in via deeplink
      </Text>
      <Text type="primary">Make sure to have the app installed</Text>
      <Button
        variant="primary"
        onClick={() => {
          window.open(mobileDeepLink, '_blank');
        }}
      >
        Connect Mobile App
      </Button>
    </VerticalGroup>
  );
};
