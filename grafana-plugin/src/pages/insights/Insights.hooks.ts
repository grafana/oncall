import { useEffect, useState } from 'react';

import { useStore } from 'state/useStore';

export const useAlertCreationChecker = () => {
  const {
    alertGroupStore: { updateAlertGroups, alerts },
  } = useStore();
  const [isFirstAlertCheckDone, setIsFirstAlertCheckDone] = useState(false);

  const isAnyAlertCreatedMoreThan20SecsAgo = Array.from(alerts).some(([_key, alert]) => {
    const alertTime = new Date(alert.started_at).getTime();
    const nowTime = new Date().getTime();
    return nowTime - alertTime > 20_000;
  });

  useEffect(() => {
    const fetch = async () => {
      if (!isAnyAlertCreatedMoreThan20SecsAgo) {
        await updateAlertGroups();
      }
      setIsFirstAlertCheckDone(true);
    };
    fetch();
    const interval = setInterval(() => {
      fetch();
    }, 5_000);
    return () => clearInterval(interval);
  }, [isAnyAlertCreatedMoreThan20SecsAgo]);

  return { isAnyAlertCreatedMoreThan20SecsAgo, isFirstAlertCheckDone };
};
