import React, { useCallback, useEffect, useState } from 'react';

import { Button, EmptySearchResult, LoadingPlaceholder } from '@grafana/ui';

import SourceCode from 'components/SourceCode/SourceCode';
import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { useStore } from 'state/useStore';

interface LiveLogsProps {
  alertReceiveChannelId: AlertReceiveChannel['id'];
}

const LiveLogs = ({ alertReceiveChannelId }: LiveLogsProps) => {
  const store = useStore();
  const { alertReceiveChannelStore } = store;

  const [logs, setLogs] = useState<string[]>();

  const updateLiveLogs = useCallback(() => {
    setLogs(undefined);
    alertReceiveChannelStore.getAccessLogs(alertReceiveChannelId).then(setLogs);
  }, [alertReceiveChannelId, alertReceiveChannelStore]);

  useEffect(updateLiveLogs, []);

  if (!logs) {
    return <LoadingPlaceholder text="Loading..." />;
  }

  return (
    <div>
      {logs.length ? (
        <SourceCode>{JSON.stringify(logs, null, 2)}</SourceCode>
      ) : (
        <EmptySearchResult>Could not find logs</EmptySearchResult>
      )}
      <Button variant="secondary" icon="sync" onClick={updateLiveLogs} key="back">
        Refresh
      </Button>
    </div>
  );
};

export default LiveLogs;
