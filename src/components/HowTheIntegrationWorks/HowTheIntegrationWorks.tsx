import React from 'react';

import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { useStyles2 } from '@grafana/ui';

import { Collapse } from 'components/Collapse/Collapse';
import { Text } from 'components/Text/Text';
import { ApiSchemas } from 'network/oncall-api/api.types';

export const HowTheIntegrationWorks: React.FC<{
  selectedOption: ApiSchemas['AlertReceiveChannelIntegrationOptions'];
}> = ({ selectedOption }) => {
  const styles = useStyles2(getStyles);

  if (!selectedOption) {
    return null;
  }

  return (
    <Collapse
      headerWithBackground
      className={styles.collapse}
      isOpen={false}
      label={<Text type="link">How the integration works</Text>}
      contentClassName={styles.collapsableContent}
    >
      <Text type="secondary">
        The integration will generate the following:
        <ul className={styles.integrationInfoList}>
          <li className={styles.integrationInfoItem}>Unique URL endpoint for receiving alerts </li>
          <li className={styles.integrationInfoItem}>
            Templates to interpret alerts, tailored for {selectedOption.display_name}{' '}
          </li>
          <li className={styles.integrationInfoItem}>{selectedOption.display_name} contact point </li>
          <li className={styles.integrationInfoItem}>{selectedOption.display_name} notification</li>
        </ul>
        What you'll need to do next:
        <ul className={styles.integrationInfoList}>
          <li className={styles.integrationInfoItem}>
            Finish connecting Monitoring system using Unique URL that will be provided on the next step{' '}
          </li>
          <li className={styles.integrationInfoItem}>
            Set up routes that are based on alert content, such as severity, region, and service{' '}
          </li>
          <li className={styles.integrationInfoItem}>Connect escalation chains to the routes</li>
          <li className={styles.integrationInfoItem}>
            Review templates and personalize according to your requirements
          </li>
        </ul>
      </Text>
    </Collapse>
  );
};

const getStyles = (theme: GrafanaTheme2) => {
  return {
    collapse: css({
      width: '100%',
      marginBottom: '24px',
      ' svg': {
        color: theme.colors.primary.text,
      },
    }),
    integrationInfoList: css({
      listStylePosition: 'inside',
      margin: '16px 0',
    }),
    integrationInfoItem: css({
      marginLeft: '16px',
    }),
    collapsableContent: css({
      width: '100%',
      backgroundColor: theme.colors.background.secondary,
      fontSize: 'small',
    }),
  };
};
