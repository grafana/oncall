import React, { FC, SyntheticEvent, useRef, useState } from 'react';

import { Icon } from '@grafana/ui';
import cn from 'classnames/bind';

import Tag from 'components/Tag/Tag';
import Text from 'components/Text/Text';
import { WithContextMenu } from 'components/WithContextMenu/WithContextMenu';
import { Alert, AlertAction, IncidentStatus } from 'models/alertgroup/alertgroup.types';
import styles from 'pages/incidents/parts/IncidentDropdown.module.scss';

import SilenceCascadingSelect from './SilenceCascadingSelect';

const cx = cn.bind(styles);

const getIncidentTagColor = (alert: Alert) => {
  if (alert.status === IncidentStatus.Resolved) {
    return '#299C46';
  }
  if (alert.status === IncidentStatus.Firing) {
    return '#E02F44';
  }
  if (alert.status === IncidentStatus.Acknowledged) {
    return '#C69B06';
  }
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
        const LEFT_MARGIN = 8;
        openMenu({ pageX: boundingRect.left + LEFT_MARGIN, pageY: boundingRect.top + boundingRect.height } as any);
      }}
    >
      <Text strong size="small">
        {IncidentStatus[alert.status]}
      </Text>
      <Icon className={cx('incident__icon')} name="angle-down" size="sm" />
    </Tag>
  );
}

export const IncidentDropdown: FC<{
  alert: Alert;
  onResolve: (e: SyntheticEvent) => Promise<void>;
  onUnacknowledge: (e: SyntheticEvent) => Promise<void>;
  onUnresolve: (e: SyntheticEvent) => Promise<void>;
  onAcknowledge: (e: SyntheticEvent) => Promise<void>;
  onSilence: (value: number) => Promise<void>;
  onUnsilence: (event: any) => Promise<void>;
}> = ({ alert, onResolve, onUnacknowledge, onUnresolve, onAcknowledge, onSilence, onUnsilence }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [isResolvedOpen, setIsResolvedOpen] = useState(false);
  const [isAcknowledgedOpen, setIsAcknowledgedOpen] = useState(false);
  const [isFiringOpen, setIsFiringOpen] = useState(false);
  const [isSilencedOpen, setIsSilencedOpen] = useState(false);

  const onClickFn = (
    ev: React.SyntheticEvent<HTMLDivElement>,
    status: string,
    action: (value: SyntheticEvent | number) => Promise<void>
  ) => {
    setIsLoading(true);

    // set them to forcedOpen so that they do not close
    if (status === AlertAction.Resolve) {
      setIsResolvedOpen(true);
    } else if (status === AlertAction.Acknowledge) {
      setIsAcknowledgedOpen(true);
    } else if (status === AlertAction.Silence) {
      setIsSilencedOpen(true);
    } else if (status === AlertAction.unResolve) {
      setIsFiringOpen(true);
    }

    action(ev)
      .then(() => {
        // network request is done and succesful, close them
        if (status === AlertAction.Resolve) {
          setIsResolvedOpen(false);
        } else if (status === AlertAction.Acknowledge) {
          setIsAcknowledgedOpen(false);
        } else if (status === AlertAction.Silence) {
          setIsSilencedOpen(false);
        } else if (status === AlertAction.unResolve) {
          setIsFiringOpen(false);
        }
      })
      .finally(() => {
        // hide loading/disabled state
        setIsLoading(false);
      });
  };

  if (alert.status === IncidentStatus.Resolved) {
    return (
      <WithContextMenu
        forceIsOpen={isResolvedOpen}
        renderMenuItems={() => (
          <div className={cx('incident__options', { 'u-disabled': isLoading })}>
            <div
              className={cx('incident__option-item', 'incident__option-item--firing')}
              onClick={(e) => onClickFn(e, AlertAction.Resolve, onUnresolve)}
            >
              Firing
            </div>
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
        forceIsOpen={isAcknowledgedOpen}
        renderMenuItems={() => (
          <div className={cx('incident__options', { 'u-disabled': isLoading })}>
            <div
              className={cx('incident__option-item', 'incident__option-item--unacknowledge')}
              onClick={(e) => onClickFn(e, AlertAction.Acknowledge, onUnacknowledge)}
            >
              Unacknowledge
            </div>
            <div
              className={cx('incident__option-item', 'incident__option-item--resolve')}
              onClick={(e) => onClickFn(e, AlertAction.Acknowledge, onResolve)}
            >
              Resolve
            </div>
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
        forceIsOpen={isFiringOpen}
        renderMenuItems={() => (
          <div className={cx('incident__options', { 'u-disabled': isLoading })}>
            <div
              className={cx('incident__option-item', 'incident__option-item--acknowledge')}
              onClick={(e) => onClickFn(e, AlertAction.unResolve, onAcknowledge)}
            >
              Acknowledge
            </div>
            <div
              className={cx('incident__option-item', 'incident__option-item--resolve')}
              onClick={(e) => onClickFn(e, AlertAction.unResolve, onResolve)}
            >
              Resolve
            </div>
            <div
              className={cx('incident__option-item')}
              onClick={(e) => onClickFn(e, AlertAction.unResolve, onSilence)}
            >
              <SilenceCascadingSelect isCascading={false} onSelect={onSilence} />
            </div>
          </div>
        )}
      >
        {({ openMenu }) => <ListMenu alert={alert} openMenu={openMenu} />}
      </WithContextMenu>
    );
  }

  // Silenced Alerts
  return (
    <WithContextMenu
      forceIsOpen={isSilencedOpen}
      renderMenuItems={() => (
        <div className={cx('incident_options', { 'u-disabled': isLoading })}>
          <div className={cx('incident__option-item')} onClick={(e) => onClickFn(e, AlertAction.Silence, onUnsilence)}>
            Unsilence
          </div>
          <div
            className={cx('incident__option-item', 'incident__option-item--acknowledge')}
            onClick={(e) => onClickFn(e, AlertAction.Silence, onAcknowledge)}
          >
            Acknowledge
          </div>
          <div
            className={cx('incident__option-item', 'incident__option-item--firing')}
            onClick={(e) => onClickFn(e, AlertAction.Silence, onAcknowledge)}
          >
            Acknowledge
          </div>
        </div>
      )}
    >
      {({ openMenu }) => <ListMenu alert={alert} openMenu={openMenu} />}
    </WithContextMenu>
  );
};
