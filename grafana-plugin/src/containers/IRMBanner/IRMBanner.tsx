import React, { useEffect } from 'react';

import { Alert, AlertVariant, Button, HorizontalGroup } from '@grafana/ui';
import { observer } from 'mobx-react';

import Text from 'components/Text/Text';
import { IRMPlanStatus } from 'models/alertgroup/alertgroup.types';
import { useStore } from 'state/useStore';

const IRMBanner: React.FC = observer(() => {
  const store = useStore();
  const {
    alertGroupStore,
    alertGroupStore: { irmPlan },
  } = store;

  useEffect(() => {
    alertGroupStore.fetchIRMPlan();
  }, []);

  if (store.isOpenSource() || !irmPlan?.limits) {
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
              Upgrade
            </Button>
          </HorizontalGroup>
        ) as any
      }
      severity={statusSeverity[irmPlan.limits.status]}
      buttonContent={undefined}
    />
  );
});

export default IRMBanner;
