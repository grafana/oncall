import React, { FC } from 'react';

import { css, cx } from '@emotion/css';
import { useStyles2 } from '@grafana/ui';

import ElasticAlertIcon from 'assets/img/ElastAlert.svg';
import HeartbeatMonitoringIcon from 'assets/img/HeartBeatMonitoring.png';
import PagerDutyIcon from 'assets/img/PagerDuty.png';
import ServiceNowIcon from 'assets/img/ServiceNow.png';
import GrafanaLegacyAlertingIcon from 'assets/img/grafana-legacy-alerting-icon.svg';
import GrafanaIcon from 'assets/img/grafana_icon.svg';
import InboundEmailIcon from 'assets/img/inbound-email.png';
import IntegrationLogos from 'assets/img/integration-logos.png';
import { logoColors } from 'components/IntegrationLogo/IntegrationLogo.config';
import { SelectOption } from 'state/types';

export interface IntegrationLogoProps {
  integration: SelectOption;
  scale: number;
}

const SPRITESHEET_WIDTH = 3000;
const LOGO_WIDTH = 200;

export const IntegrationLogo: FC<IntegrationLogoProps> = (props) => {
  const { integration, scale } = props;
  const styles = useStyles2(getStyles);

  if (!integration) {
    return null;
  }

  const coors = logoColors[integration.value] || { x: 2, y: 14 };

  const bgStyle = {
    backgroundPosition: `-${coors?.x * LOGO_WIDTH * scale}px -${coors?.y * LOGO_WIDTH * scale}px`,
    width: LOGO_WIDTH * scale,
    height: LOGO_WIDTH * scale,
    backgroundSize: `${SPRITESHEET_WIDTH * scale}px ${SPRITESHEET_WIDTH * scale}px`,
  };

  return (
    <div
      className={cx(styles.bg, {
        [styles[`${integration.display_name.replace(new RegExp(' ', 'g'), '')}`]]: true,
      })}
      style={bgStyle}
    />
  );
};

const getStyles = () => {
  return {
    bg: css`
      background: url(${IntegrationLogos});
      background-repeat: no-repeat;
    `,

    bgServiceNow: css`
      background: url(${ServiceNowIcon})
      background-size: 100% !important;
    `,

    bgPagerDuty: css`
      background: url(${PagerDutyIcon});
      background-size: 100% !important;
    `,

    bgElastAlert: css`
      background: url(${ElasticAlertIcon});
      background-size: 100% !important;
    `,

    bgHeartBeatMonitoring: css`
      background: url(${HeartbeatMonitoringIcon});
      background-size: 100% !important;
    `,

    bgGrafanaLegacyAlerting: css`
      background: url(${GrafanaLegacyAlertingIcon});
      background-size: 100% !important;
    `,

    bgGrafanaAlerting: css`
      background: url(${GrafanaIcon});
      background-size: 100% !important;
    `,

    bgInboundEmail: css`
      background: url(${InboundEmailIcon});
      background-size: 100% !important;
    `,
  };
};
