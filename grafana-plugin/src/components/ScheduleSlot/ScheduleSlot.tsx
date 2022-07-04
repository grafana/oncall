import React, { FC } from 'react';

import { HorizontalGroup, VerticalGroup, Icon, Tooltip, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import Line from 'components/ScheduleUserDetails/img/line.svg';
import Text from 'components/Text/Text';
import { User } from 'models/user/user.types';
import { useStore } from 'state/useStore';

import styles from './ScheduleSlot.module.css';

interface ScheduleSlotProps {
  color: string;
  userPk: User['pk'];
  label: string;
  inactive: boolean;
  width: number;
}

const cx = cn.bind(styles);

const ScheduleSlot: FC<ScheduleSlotProps> = observer((props) => {
  const { color, userPk, inactive, label } = props;

  const left = Math.random() * 50;
  const right = 100 - (left + 20 + Math.random() * 30);

  const store = useStore();

  const storeUser = store.userStore.items[userPk];

  let title = storeUser
    ? storeUser.username
        .split(' ')
        .map((word) => word.charAt(0).toUpperCase())
        .join('')
    : null;

  return (
    <Tooltip content={<ScheduleSlotDetails user={storeUser} />}>
      <div
        className={cx('root', { root__inactive: inactive })}
        style={{
          backgroundColor: color,
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
});

export default ScheduleSlot;

interface ScheduleSlotDetailsProps {}

const ScheduleSlotDetails = (props: ScheduleSlotDetailsProps) => {
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
            <Text type="secondary">{user?.username}</Text>
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

interface ScheduleGapProps {}

export const ScheduleGap = (props: ScheduleGapProps) => {
  return <div className={cx('root', 'root__type_gap')} style={{}} />;
};
