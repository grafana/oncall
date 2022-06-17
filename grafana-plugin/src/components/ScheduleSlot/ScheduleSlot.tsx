import React, { FC } from 'react';

import { HorizontalGroup, VerticalGroup, Icon, Tooltip, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';

import Line from 'components/ScheduleUserDetails/img/line.svg';
import Text from 'components/Text/Text';

import styles from './ScheduleSlot.module.css';

interface ScheduleSlotProps {
  color: string;
  user: string;
  label: string;
}

const cx = cn.bind(styles);

const ScheduleSlot: FC<ScheduleSlotProps> = (props) => {
  const { color, user, inactive, label } = props;

  const left = Math.random() * 50;
  const right = 100 - (left + 20 + Math.random() * 30);

  const width = Math.random() * 150 + 100;

  let title = user;
  if (width < 150) {
    title = title
      .split(' ')
      .map((word) => word.charAt(0).toUpperCase())
      .join('');
  }

  return (
    <Tooltip content={<ScheduleSlotDetails user={user} />}>
      <div
        className={cx('root', { root__inactive: inactive })}
        style={{
          backgroundColor: color,
          width: `${width}px`,
        }}
      >
        <div style={{ left: `${left}%`, right: `${right}%` }} className={cx('striped')} />
        {label && (
          <div className={cx('label')} style={{ color }}>
            {label}
          </div>
        )}
        <div className={cx('title')}>{title}</div>
      </div>
    </Tooltip>
  );
};

export default ScheduleSlot;

interface ScheduleSlotDetailsProps {}

const ScheduleSlotDetails = (props) => {
  const { user, currentUser } = props;

  const userStatus = 'success';

  return (
    <div className={cx('details')}>
      <HorizontalGroup>
        <VerticalGroup spacing="sm">
          <HorizontalGroup spacing="md">
            <div
              className={cx('details-user-status', {
                [`details-user-status__type_${userStatus}`]: true,
              })}
            />
            <Text type="secondary">{user}</Text>
          </HorizontalGroup>
          <HorizontalGroup>
            <VerticalGroup spacing="none">
              <HorizontalGroup spacing="sm">
                <Icon name="clock-nine" size="xs" />
                <Text type="secondary">30 apr, 7:54 </Text>
              </HorizontalGroup>
              <HorizontalGroup spacing="sm">
                <img src={Line} />
                <VerticalGroup spacing="none">
                  <Text type="secondary">30 apr, 00:00</Text>
                  <Text type="secondary">30 apr, 23:59</Text>
                </VerticalGroup>
              </HorizontalGroup>
            </VerticalGroup>
          </HorizontalGroup>
        </VerticalGroup>
        <VerticalGroup spacing="sm">
          <Text type="primary">Maxim Mordasov</Text>
          <VerticalGroup spacing="none">
            <Text type="primary">30 apr, 12:54 </Text>
            <Text type="primary">29 apr, 20:00 </Text>
            <Text type="primary">30 apr, 20:00 </Text>
          </VerticalGroup>
        </VerticalGroup>
      </HorizontalGroup>
    </div>
  );
};
