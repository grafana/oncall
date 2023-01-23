import React, { useRef } from 'react';

import { Icon, WithContextMenu } from '@grafana/ui';
import { Alert, IncidentStatus } from 'models/alertgroup/alertgroup.types';

import cn from 'classnames/bind';

import styles from 'pages/incidents/parts/IncidentDropdown.module.scss';

import Tag from 'components/Tag/Tag';
import Text from 'components/Text/Text';

const cx = cn.bind(styles);

const getIncidentTagColor = (alert: Alert) => {
  if (alert.status === IncidentStatus.Resolved) return '#299C46';
  if (alert.status === IncidentStatus.Firing) return '#E02F44';
  if (alert.status === IncidentStatus.Acknowledged) return '#C69B06';
  return '#464C54';
};

function ListMenu({ alert, openMenu }: { alert: Alert; openMenu: React.MouseEventHandler<HTMLElement> }) {
  const forwardedRef = useRef<HTMLSpanElement>();

  return (
    <Tag
      forwardedRef={forwardedRef}
      className={cx('incident__tag')}
      color={getIncidentTagColor(alert)}
      onClick={() => {
        const boundingRect = forwardedRef.current.getBoundingClientRect();
        openMenu({ pageX: boundingRect.left, pageY: boundingRect.top + boundingRect.height } as any);
      }}
    >
      <Text strong size="small">
        {IncidentStatus[alert.status]}
      </Text>
      <Icon className={cx('incident__icon')} name="angle-down" size="sm" />
    </Tag>
  );
}

export function getIncidentContextMenu(alert: Alert) {
  if (alert.status === IncidentStatus.Resolved) {
    return (
      <WithContextMenu
        renderMenuItems={() => (
          <div className={cx('incident__options')}>
            <div className={cx('incident__option-item', 'incident__option-item--firing')}>Firing</div>
          </div>
        )}
      >
        {({ openMenu }) => <ListMenu alert={alert} openMenu={openMenu} />}
      </WithContextMenu>
    );
  }

  if (alert.status === IncidentStatus.Acknowledged) {
    return (
      <WithContextMenu
        renderMenuItems={() => (
          <div className={cx('incident__options')}>
            <div className={cx('incident__option-item', 'incident__option-item--unacknowledge')}>Unacknowledge</div>
            <div className={cx('incident__option-item', 'incident__option-item--resolve')}>Resolve</div>
          </div>
        )}
      >
        {({ openMenu }) => <ListMenu alert={alert} openMenu={openMenu} />}
      </WithContextMenu>
    );
  }

  if (alert.status === IncidentStatus.Firing) {
    return (
      <WithContextMenu
        renderMenuItems={() => (
          <>
            <div className={cx('incident__option-item')}>Silence</div>
            <div className={cx('incident__option-item', 'incident__option-item--acknowledge')}>Acknowledge</div>
            <div className={cx('incident__option-item', 'incident__option-item--resolve')}>Resolve</div>
          </>
        )}
      >
        {({ openMenu }) => <ListMenu alert={alert} openMenu={openMenu} />}
      </WithContextMenu>
    );
  }

  // Silenced Alerts
  return (
    <WithContextMenu
      renderMenuItems={() => (
        <div className={cx('incident_options')}>
          <div className={cx('incident__option-item')}>Unsilence</div>
          <div className={cx('incident__option-item', 'incident__option-item--acknowledge')}>Acknowledge</div>
          <div className={cx('incident__option-item', 'incident__option-item--firing')}>Acknowledge</div>
        </div>
      )}
    >
      {({ openMenu }) => <ListMenu alert={alert} openMenu={openMenu} />}
    </WithContextMenu>
  );
}
