import React, { FC } from 'react';

import { css, cx } from '@emotion/css';
import { useStyles2 } from '@grafana/ui';

import { SelectOption } from 'state/types';

import { logoCoors } from './IntegrationLogo.config';

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

  const coors = logoCoors[integration.value] || { x: 2, y: 14 };

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
      background: url(../../assets/img/integration-logos.png);
      background-repeat: no-repeat;
    `,

    bgServiceNow: css`
      background: url(../../assets/img/ServiceNow.png);
      background-size: 100% !important;
    `,

    bgPagerDuty: css`
      background: url(../../assets/img/PagerDuty.png);
      background-size: 100% !important;
    `,

    bgElastAlert: css`
      background: url(../../assets/img/ElastAlert.svg);
      background-size: 100% !important;
    `,

    bgHeartBeatMonitoring: css`
      background: url(../../assets/img/HeartBeatMonitoring.png);
      background-size: 100% !important;
    `,

    bgGrafanaLegacyAlerting: css`
      background: url(../../assets/img/grafana-legacy-alerting-icon.svg);
      background-size: 100% !important;
    `,

    bgGrafanaAlerting: css`
      background: url(../../assets/img/grafana_icon.svg);
      background-size: 100% !important;
    `,

    bgInboundEmail: css`
      background: url(../../assets/img/inbound-email.png);
      background-size: 100% !important;
    `,
  };
};
