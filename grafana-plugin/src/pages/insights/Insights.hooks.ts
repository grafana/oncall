import { useEffect, useState } from 'react';

import { useStore } from 'state/useStore';

export const useAlertGroupsCounterChecker = () => {
  const {
    alertGroupStore: { getAllIncidentsCount, allIncidentsCount },
  } = useStore();
  const [isFirstAlertCountCheckDone, setIsFirstAlertCountCheckDone] = useState(false);

  const isAlertCreated = allIncidentsCount >= 1;

  useEffect(() => {
    const fetch = async () => {
      if (!isAlertCreated) {
        await getAllIncidentsCount();
      }
      setIsFirstAlertCountCheckDone(true);
    };
    fetch();
    const interval = setInterval(() => {
      fetch();
    }, 5_000);
    return () => clearInterval(interval);
  }, [isAlertCreated]);

  return { isAlertCreated, isFirstAlertCountCheckDone };
};
