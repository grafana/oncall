import Text from 'components/Text/Text';
import { observer } from 'mobx-react';
import React from 'react';
import { isUseProfileExtensionPointEnabled } from 'utils';

const MobileAppConnectionTab: React.FC<{ userPk: string }> = observer(() => {
  !isUseProfileExtensionPointEnabled();

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
