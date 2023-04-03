import React, { FC } from 'react';

import cn from 'classnames/bind';

import Block from 'components/GBlock/Block';
import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';

import { TutorialStep } from './Tutorial.types';
import bellIcon from './icons/bell-icon.svg';
import scheduleIcon from './icons/calendar-icon.svg';
import chatIcon from './icons/chat-icon.svg';
import escalationIcon from './icons/escalation-icon.svg';
import integrationsIcon from './icons/integration-icon.svg';

import styles from './Tutorial.module.css';

interface TutorialProps {
  title: React.ReactNode;
  step: TutorialStep;
}

const cx = cn.bind(styles);

const Tutorial: FC<TutorialProps> = (props) => {
  const { title, step } = props;

  return (
    <Block className={cx('root')} bordered>
      <div className={cx('title')}>{title}</div>
      <div className={cx('steps')}>
        <div className={cx('step')}>
          <PluginLink query={{ page: 'integrations' }}>
            <div className={cx('icon', { icon_active: step === TutorialStep.Integrations })}>
              <img src={integrationsIcon} />
            </div>
          </PluginLink>
          <Text type="secondary">Add integration with a monitoring system</Text>
        </div>
        <Arrow />
        <div className={cx('step')}>
          <PluginLink query={{ page: 'escalations' }}>
            <div className={cx('icon', { icon_active: step === TutorialStep.Escalations })}>
              <img src={escalationIcon} />
            </div>
          </PluginLink>
          <Text type="secondary">Setup escalation chain to handle notifications</Text>
        </div>
        <Arrow />
        <div className={cx('step')}>
          <PluginLink query={{ page: 'chat-ops' }}>
            <div className={cx('icon', { icon_active: step === TutorialStep.Slack })}>
              <img src={chatIcon} />
            </div>
          </PluginLink>
          <Text type="secondary">Connect to your chat workspace</Text>
        </div>
        <Arrow />
        <div className={cx('step')}>
          <PluginLink query={{ page: 'schedules' }}>
            <div className={cx('icon', { icon_active: step === TutorialStep.Schedules })}>
              <img src={scheduleIcon} />
            </div>
          </PluginLink>
          <Text type="secondary">Add your team calendar to define an on-call rotation.</Text>
        </div>
        <Arrow />
        <div className={cx('step')}>
          <PluginLink query={{ page: 'alert-groups' }}>
            <div className={cx('icon', { icon_active: step === TutorialStep.Incidents })}>
              <img src={bellIcon} />
            </div>
          </PluginLink>
          <Text type="secondary">OnCall manages your alerts</Text>
        </div>
      </div>
    </Block>
  );
};

const Arrow = () => (
  <div className={cx('arrow')}>
    <svg width="41" height="16" viewBox="0 0 41 16" xmlns="http://www.w3.org/2000/svg">
      <path d="M40.7071 8.70711C41.0976 8.31658 41.0976 7.68342 40.7071 7.29289L34.3431 0.928932C33.9526 0.538408 33.3195 0.538408 32.9289 0.928932C32.5384 1.31946 32.5384 1.95262 32.9289 2.34315L38.5858 8L32.9289 13.6569C32.5384 14.0474 32.5384 14.6805 32.9289 15.0711C33.3195 15.4616 33.9526 15.4616 34.3431 15.0711L40.7071 8.70711ZM0 9H40V7H0V9Z" />
    </svg>
  </div>
);

export default Tutorial;
