import React from 'react';

import { observer } from 'mobx-react';

import { Text } from 'components/Text/Text';

const MobileAppConnectionTab: React.FC<{ userPk?: string }> = observer(() => {
  return (
    <Text type="secondary">
      Mobile settings have been moved to{' '}
      <a href={`${window.location.origin}/profile?tab=irm`}>
        <Text type="link">user's profile</Text>
      </a>
    </Text>
  );
});

export { MobileAppConnectionTab };
