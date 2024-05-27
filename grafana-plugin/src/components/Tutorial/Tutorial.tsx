import React, { FC } from 'react';

import { css, cx } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { useStyles2 } from '@grafana/ui';
import { bem } from 'styles/utils.styles';

import { Block } from 'components/GBlock/Block';
import { PluginLink } from 'components/PluginLink/PluginLink';
import { Text } from 'components/Text/Text';

import { TutorialStep } from './Tutorial.types';
import bellIcon from './icons/bell-icon.svg';
import scheduleIcon from './icons/calendar-icon.svg';
import chatIcon from './icons/chat-icon.svg';
import escalationIcon from './icons/escalation-icon.svg';
import integrationsIcon from './icons/integration-icon.svg';

interface TutorialProps {
  title: React.ReactNode;
  step: TutorialStep;
}

export const Tutorial: FC<TutorialProps> = (props) => {
  const { title, step } = props;
  const styles = useStyles2(getStyles);

  return (
    <Block className={styles.root} bordered>
      <div className={styles.title}>{title}</div>
      <div className={styles.steps}>
        <div className={styles.step}>
          <PluginLink query={{ page: 'integrations' }}>
            <div className={cx(styles.icon, { [bem(styles.icon, 'active')]: step === TutorialStep.Integrations })}>
              <img src={integrationsIcon} />
            </div>
          </PluginLink>
          <Text type="secondary">Add integration with a monitoring system</Text>
        </div>
        <Arrow />
        <div className={styles.step}>
          <PluginLink query={{ page: 'escalations' }}>
            <div className={cx(styles.icon, { [bem(styles.icon, 'active')]: step === TutorialStep.Escalations })}>
              <img src={escalationIcon} />
            </div>
          </PluginLink>
          <Text type="secondary">Setup escalation chain to handle notifications</Text>
        </div>
        <Arrow />
        <div className={styles.step}>
          <PluginLink query={{ page: 'chat-ops' }}>
            <div className={cx(styles.icon, { [bem(styles.icon, 'active')]: step === TutorialStep.Slack })}>
              <img src={chatIcon} />
            </div>
          </PluginLink>
          <Text type="secondary">Connect to your chat workspace</Text>
        </div>
        <Arrow />
        <div className={styles.step}>
          <PluginLink query={{ page: 'schedules' }}>
            <div className={cx(styles.icon, { [bem(styles.icon, 'active')]: step === TutorialStep.Schedules })}>
              <img src={scheduleIcon} />
            </div>
          </PluginLink>
          <Text type="secondary">Add your team calendar to define an on-call rotation.</Text>
        </div>
        <Arrow />
        <div className={styles.step}>
          <PluginLink query={{ page: 'alert-groups' }}>
            <div className={cx('icon', { [bem(styles.icon, 'active')]: step === TutorialStep.Incidents })}>
              <img src={bellIcon} />
            </div>
          </PluginLink>
          <Text type="secondary">OnCall manages your alerts</Text>
        </div>
      </div>
    </Block>
  );
};

const Arrow = () => {
  const styles = useStyles2(getStyles);
  return (
    <div className={styles.arrow}>
      <svg width="41" height="16" viewBox="0 0 41 16" xmlns="http://www.w3.org/2000/svg">
        <path d="M40.7071 8.70711C41.0976 8.31658 41.0976 7.68342 40.7071 7.29289L34.3431 0.928932C33.9526 0.538408 33.3195 0.538408 32.9289 0.928932C32.5384 1.31946 32.5384 1.95262 32.9289 2.34315L38.5858 8L32.9289 13.6569C32.5384 14.0474 32.5384 14.6805 32.9289 15.0711C33.3195 15.4616 33.9526 15.4616 34.3431 15.0711L40.7071 8.70711ZM0 9H40V7H0V9Z" />
      </svg>
    </div>
  );
};

const getStyles = (theme: GrafanaTheme2) => {
  return {
    root: css`
      display: flex;
      align-items: center;
      flex-direction: column;
    `,

    title: css`
      margin-top: 100px;
    `,

    steps: css`
      margin-top: 100px;
      display: flex;
      gap: 10px;
      margin-bottom: 100px;
      align-items: flex-start;
    `,

    step: css`
      display: flex;
      flex-direction: column;
      gap: 10px;
      align-items: center;
      width: 120px;
      text-align: center;

      @media (min-width: 1540px) {
        & {
          width: 170px;
        }
      }
    `,

    icon: css`
      width: 60px;
      height: 60px;
      background: ${theme.colors.background.secondary};
      border-radius: 50%;
      text-align: center;
      line-height: 55px;

      &--active {
        // this color doesn't seem to have any mapping
        border: 2px solid #ffb375;
      }
    `,

    arrow: css`
      margin-top: 20px;

      svg {
        fill: #ccccdc;
        ${theme.isDark ? 'fill-opacity: 0.15' : ''};
      }
    `,
  };
};
