import { useEffect, useState } from 'react';

import { useStore } from 'state/useStore';

const TWENTY_SECS = 20_000;
const FIVE_SECS = 5_000;

export const useAlertCreationChecker = () => {
  const {
    alertGroupStore: { fetchAlertGroups, alerts },
  } = useStore();
  const [isFirstAlertCheckDone, setIsFirstAlertCheckDone] = useState(false);

  const isAnyAlertCreatedMoreThan20SecsAgo = Array.from(alerts).some(([_key, alert]) => {
    const alertTime = new Date(alert.started_at).getTime();
    const nowTime = new Date().getTime();
    return nowTime - alertTime > TWENTY_SECS;
  });

  useEffect(() => {
    const fetch = async () => {
      if (!isAnyAlertCreatedMoreThan20SecsAgo) {
        await fetchAlertGroups();
      }
      setIsFirstAlertCheckDone(true);
    };
    fetch();
    const interval = setInterval(() => {
      fetch();
    }, FIVE_SECS);
    return () => clearInterval(interval);
  }, [isAnyAlertCreatedMoreThan20SecsAgo]);

  return { isAnyAlertCreatedMoreThan20SecsAgo, isFirstAlertCheckDone };
};
