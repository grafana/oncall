import { useEffect, useState } from 'react';

import { AlertReceiveChannelHelper } from 'models/alert_receive_channel/alert_receive_channel.helpers';

import { useCurrentIntegration } from './OutgoingTab/OutgoingTab.hooks';

export const useIntegrationTokenCheck = () => {
  const [tokenExists, setTokenExists] = useState(true);

  const { id } = useCurrentIntegration();

  useEffect(() => {
    const checkToken = async () => {
      const tokenExists = await AlertReceiveChannelHelper.checkIfTokenExists(id);
      setTokenExists(tokenExists);
    };
    checkToken();
  }, [id]);

  return tokenExists;
};
