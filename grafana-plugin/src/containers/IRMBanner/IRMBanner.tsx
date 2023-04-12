import React from 'react';

import { Alert, AlertVariant, Button, HorizontalGroup } from '@grafana/ui';
import Text from 'components/Text/Text';
import { IRMPlanStatus } from 'models/alertgroup/alertgroup.types';
import { useStore } from 'state/useStore';

const IRMBanner: React.FC = () => {
  const store = useStore();
  const {
    alertGroupStore: { irmPlan },
  } = store;

  if (store.isOpenSource()) {
    return null;
  }
  if (irmPlan.limits.isIrmPro || irmPlan.limits.status === IRMPlanStatus.WithinLimits) {
    return null;
  }

  const statusSeverity: { [key: string]: AlertVariant } = {
    [IRMPlanStatus.WithinLimits]: 'success',
    [IRMPlanStatus.NearLimit]: 'warning',
    [IRMPlanStatus.AtLimit]: 'error',
  };

  return (
    <Alert
      title={
        (
          <HorizontalGroup justify={'space-between'}>
            <Text type={'secondary'}>
              <div dangerouslySetInnerHTML={{ __html: irmPlan.limits.reasonHTML }} />
            </Text>
            <Button variant={'secondary'} onClick={() => window.open(irmPlan.limits.upgradeURL, '_blank')}>
              Upgrade to Pro
            </Button>
          </HorizontalGroup>
        ) as any
      }
      severity={statusSeverity[irmPlan.limits.status]}
      buttonContent={undefined}
    />
  );
};

export default IRMBanner;
