import React, { FC, SyntheticEvent, useRef, useState } from 'react';

import { Icon, LoadingPlaceholder } from '@grafana/ui';
import cn from 'classnames/bind';

import Tag from 'components/Tag/Tag';
import Text from 'components/Text/Text';
import { WithContextMenu } from 'components/WithContextMenu/WithContextMenu';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { Alert, AlertAction, IncidentStatus } from 'models/alertgroup/alertgroup.types';
import styles from 'pages/incidents/parts/IncidentDropdown.module.scss';
import { getVar } from 'utils/DOM';
import { UserActions } from 'utils/authorization';

import { SilenceSelect } from './SilenceSelect';

const cx = cn.bind(styles);

const getIncidentTagColor = (alert: Alert) => {
  if (alert.status === IncidentStatus.Resolved) {
    return getVar('--tag-primary');
  }
  if (alert.status === IncidentStatus.Firing) {
    return getVar('--tag-danger');
  }
  if (alert.status === IncidentStatus.Acknowledged) {
    return getVar('--tag-warning');
  }
  return getVar('--tag-secondary');
};

function IncidentStatusTag({ alert, openMenu }: { alert: Alert; openMenu: React.MouseEventHandler<HTMLElement> }) {
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
  onUnsilence: (event: React.SyntheticEvent) => Promise<void>;
}> = ({ alert, onResolve, onUnacknowledge, onUnresolve, onAcknowledge, onSilence, onUnsilence }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [currentLoadingAction, setCurrentActionLoading] = useState<IncidentStatus>(undefined);
  const [forcedOpenAction, setForcedOpenAction] = useState<string>(undefined);

  const onClickFn = (
    ev: React.SyntheticEvent<HTMLDivElement>,
    actionName: string,
    action: (value: SyntheticEvent | number) => Promise<void>,
    status: IncidentStatus
  ) => {
    setIsLoading(true);
    setCurrentActionLoading(status);

    // set them to forcedOpen so that they do not close
    setForcedOpenAction(actionName);

    action(ev)
      .then(() => {
        // network request is done and succesful, close them
        setForcedOpenAction(undefined);
      })
      .finally(() => {
        // hide loading/disabled state
        setIsLoading(false);
      });
  };

  if (alert.status === IncidentStatus.Resolved) {
    return (
      <WithContextMenu
        forceIsOpen={forcedOpenAction === AlertAction.Resolve}
        renderMenuItems={() => (
          <div className={cx('incident__options', { 'u-disabled': isLoading })}>
            <WithPermissionControlTooltip userAction={UserActions.AlertGroupsWrite}>
              <div
                className={cx('incident__option-item', 'incident__option-item--firing')}
                onClick={(e) => onClickFn(e, AlertAction.Resolve, onUnresolve, IncidentStatus.Firing)}
              >
                Firing{' '}
                {currentLoadingAction === IncidentStatus.Firing && isLoading && (
                  <span className={cx('incident__option-span')}>
                    <LoadingPlaceholder text="" />
                  </span>
                )}
              </div>
            </WithPermissionControlTooltip>
          </div>
        )}
      >
        {({ openMenu }) => <IncidentStatusTag alert={alert} openMenu={openMenu} />}
      </WithContextMenu>
    );
  }

  if (alert.status === IncidentStatus.Acknowledged) {
    return (
      <WithContextMenu
        forceIsOpen={forcedOpenAction === AlertAction.Acknowledge}
        renderMenuItems={() => (
          <div className={cx('incident__options', { 'u-disabled': isLoading })}>
            <WithPermissionControlTooltip userAction={UserActions.AlertGroupsWrite}>
              <div
                className={cx('incident__option-item', 'incident__option-item--unacknowledge')}
                onClick={(e) => onClickFn(e, AlertAction.Acknowledge, onUnacknowledge, IncidentStatus.Firing)}
              >
                Unacknowledge{' '}
                {currentLoadingAction === IncidentStatus.Firing && isLoading && (
                  <span className={cx('incident__option-span')}>
                    <LoadingPlaceholder text="" />
                  </span>
                )}
              </div>
            </WithPermissionControlTooltip>
            <WithPermissionControlTooltip userAction={UserActions.AlertGroupsWrite}>
              <div
                className={cx('incident__option-item', 'incident__option-item--resolve')}
                onClick={(e) => onClickFn(e, AlertAction.Acknowledge, onResolve, IncidentStatus.Resolved)}
              >
                Resolve{' '}
                {currentLoadingAction === IncidentStatus.Resolved && isLoading && (
                  <span className={cx('incident__option-span')}>
                    <LoadingPlaceholder text="" />
                  </span>
                )}
              </div>
            </WithPermissionControlTooltip>
          </div>
        )}
      >
        {({ openMenu }) => <IncidentStatusTag alert={alert} openMenu={openMenu} />}
      </WithContextMenu>
    );
  }

  if (alert.status === IncidentStatus.Firing) {
    return (
      <WithContextMenu
        forceIsOpen={forcedOpenAction === AlertAction.unResolve}
        renderMenuItems={() => (
          <div className={cx('incident__options', { 'u-disabled': isLoading })}>
            <WithPermissionControlTooltip userAction={UserActions.AlertGroupsWrite}>
              <div
                className={cx('incident__option-item', 'incident__option-item--acknowledge')}
                onClick={(e) => onClickFn(e, AlertAction.unResolve, onAcknowledge, IncidentStatus.Acknowledged)}
              >
                Acknowledge{' '}
                {currentLoadingAction === IncidentStatus.Acknowledged && isLoading && (
                  <span className={cx('incident__option-span')}>
                    <LoadingPlaceholder text="" />
                  </span>
                )}
              </div>
            </WithPermissionControlTooltip>
            <WithPermissionControlTooltip userAction={UserActions.AlertGroupsWrite}>
              <div
                className={cx('incident__option-item', 'incident__option-item--resolve')}
                onClick={(e) => onClickFn(e, AlertAction.unResolve, onResolve, IncidentStatus.Resolved)}
              >
                Resolve{' '}
                {currentLoadingAction === IncidentStatus.Resolved && isLoading && (
                  <span className={cx('incident__option-span')}>
                    <LoadingPlaceholder text="" />
                  </span>
                )}
              </div>
            </WithPermissionControlTooltip>

            <div className={cx('incident__option-item')}>
              <SilenceSelect
                placeholder={
                  currentLoadingAction === IncidentStatus.Silenced && isLoading ? 'Loading...' : 'Silence for'
                }
                onSelect={(value) => {
                  setIsLoading(true);
                  setForcedOpenAction(AlertAction.unResolve);
                  setCurrentActionLoading(IncidentStatus.Silenced);
                  onSilence(value).finally(() => {
                    setIsLoading(false);
                    setForcedOpenAction(undefined);
                    setCurrentActionLoading(undefined);
                  });
                }}
              />
            </div>
          </div>
        )}
      >
        {({ openMenu }) => <IncidentStatusTag alert={alert} openMenu={openMenu} />}
      </WithContextMenu>
    );
  }

  // Silenced Alerts
  return (
    <WithContextMenu
      forceIsOpen={forcedOpenAction === AlertAction.Silence}
      renderMenuItems={() => (
        <div className={cx('incident_options', { 'u-disabled': isLoading })}>
          <WithPermissionControlTooltip userAction={UserActions.AlertGroupsWrite}>
            <div
              className={cx('incident__option-item')}
              onClick={(e) => onClickFn(e, AlertAction.Silence, onUnsilence, IncidentStatus.Firing)}
            >
              Unsilence{' '}
              {currentLoadingAction === IncidentStatus.Firing && isLoading && (
                <span className={cx('incident__option-span')}>
                  <LoadingPlaceholder text="" />
                </span>
              )}
            </div>
          </WithPermissionControlTooltip>
          <WithPermissionControlTooltip userAction={UserActions.AlertGroupsWrite}>
            <div
              className={cx('incident__option-item', 'incident__option-item--acknowledge')}
              onClick={(e) => onClickFn(e, AlertAction.Silence, onAcknowledge, IncidentStatus.Acknowledged)}
            >
              Acknowledge{' '}
              {currentLoadingAction === IncidentStatus.Acknowledged && isLoading && (
                <span className={cx('incident__option-span')}>
                  <LoadingPlaceholder text="" />
                </span>
              )}
            </div>
          </WithPermissionControlTooltip>
          <WithPermissionControlTooltip userAction={UserActions.AlertGroupsWrite}>
            <div
              className={cx('incident__option-item', 'incident__option-item--resolve')}
              onClick={(e) => onClickFn(e, AlertAction.Silence, onAcknowledge, IncidentStatus.Resolved)}
            >
              Resolve{' '}
              {currentLoadingAction === IncidentStatus.Resolved && isLoading && (
                <span className={cx('incident__option-span')}>
                  <LoadingPlaceholder text="" />
                </span>
              )}
            </div>
          </WithPermissionControlTooltip>
        </div>
      )}
    >
      {({ openMenu }) => <IncidentStatusTag alert={alert} openMenu={openMenu} />}
    </WithContextMenu>
  );
};
