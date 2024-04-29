import React, { FC, SyntheticEvent, useRef, useState } from 'react';

import { cx } from '@emotion/css';
import { Icon, LoadingPlaceholder, useStyles2 } from '@grafana/ui';
import { getUtilStyles } from 'styles/utils.styles';

import { Tag, TagColor } from 'components/Tag/Tag';
import { Text } from 'components/Text/Text';
import { WithContextMenu } from 'components/WithContextMenu/WithContextMenu';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { AlertAction, IncidentStatus } from 'models/alertgroup/alertgroup.types';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { UserActions } from 'utils/authorization/authorization';

import { getIncidentDropdownStyles } from './IncidentDropdown.styles';
import { SilenceSelect } from './SilenceSelect';

const getIncidentTagColor = (alert: ApiSchemas['AlertGroup']) => {
  if (alert.status === IncidentStatus.Resolved) {
    return TagColor.SUCCESS;
  }
  if (alert.status === IncidentStatus.Firing) {
    return TagColor.ERROR;
  }
  if (alert.status === IncidentStatus.Acknowledged) {
    return TagColor.WARNING;
  }
  return TagColor.SECONDARY;
};

function IncidentStatusTag({
  alert,
  openMenu,
}: {
  alert: ApiSchemas['AlertGroup'];
  openMenu: React.MouseEventHandler<HTMLElement>;
}) {
  const styles = useStyles2(getIncidentDropdownStyles);
  const forwardedRef = useRef<HTMLSpanElement>();

  return (
    <Tag
      forwardedRef={forwardedRef}
      className={cx(styles.incidentTag)}
      color={getIncidentTagColor(alert)}
      onClick={() => {
        const boundingRect = forwardedRef.current.getBoundingClientRect();
        const LEFT_MARGIN = 8;
        openMenu({ pageX: boundingRect.left + LEFT_MARGIN, pageY: boundingRect.top + boundingRect.height } as any);
      }}
    >
      <Text size="small">{IncidentStatus[alert.status]}</Text>
      <Icon className={cx(styles.incidentIcon)} name="angle-down" size="sm" />
    </Tag>
  );
}

export const IncidentDropdown: FC<{
  alert: ApiSchemas['AlertGroup'];
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

  const styles = useStyles2(getIncidentDropdownStyles);
  const utilStyles = useStyles2(getUtilStyles);

  const onClickFn = async (
    ev: React.SyntheticEvent<HTMLDivElement>,
    actionName: string,
    action: (value: SyntheticEvent | number) => Promise<void>,
    status: IncidentStatus
  ) => {
    setIsLoading(true);
    setCurrentActionLoading(status);

    // set them to forcedOpen so that they do not close
    setForcedOpenAction(actionName);

    await action(ev);

    // network request is done and succesful, close them
    setForcedOpenAction(undefined);
    // hide loading/disabled state
    setIsLoading(false);
  };

  if (alert.status === IncidentStatus.Resolved) {
    return (
      <WithContextMenu
        forceIsOpen={forcedOpenAction === AlertAction.Resolve}
        renderMenuItems={() => (
          <div className={cx(styles.incidentOptions, { [utilStyles.disabled]: isLoading })}>
            <WithPermissionControlTooltip userAction={UserActions.AlertGroupsWrite}>
              <div
                className={cx(styles.incidentOptionItem)}
                onClick={(e) => onClickFn(e, AlertAction.Resolve, onUnresolve, IncidentStatus.Firing)}
              >
                Firing{' '}
                {currentLoadingAction === IncidentStatus.Firing && isLoading && (
                  <span className={cx(styles.incidentOptionEl)}>
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
          <div className={cx(styles.incidentOptions, { [utilStyles.disabled]: isLoading })}>
            <WithPermissionControlTooltip userAction={UserActions.AlertGroupsWrite}>
              <div
                className={cx(styles.incidentOptionItem)}
                onClick={(e) => onClickFn(e, AlertAction.Acknowledge, onUnacknowledge, IncidentStatus.Firing)}
              >
                Unacknowledge{' '}
                {currentLoadingAction === IncidentStatus.Firing && isLoading && (
                  <span className={cx(styles.incidentOptionEl)}>
                    <LoadingPlaceholder text="" />
                  </span>
                )}
              </div>
            </WithPermissionControlTooltip>
            <WithPermissionControlTooltip userAction={UserActions.AlertGroupsWrite}>
              <div
                className={cx(styles.incidentOptionItem)}
                onClick={(e) => onClickFn(e, AlertAction.Acknowledge, onResolve, IncidentStatus.Resolved)}
              >
                Resolve{' '}
                {currentLoadingAction === IncidentStatus.Resolved && isLoading && (
                  <span className={cx(styles.incidentOptionEl)}>
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
          <div className={cx(styles.incidentOptions, { [utilStyles.disabled]: isLoading })}>
            <WithPermissionControlTooltip userAction={UserActions.AlertGroupsWrite}>
              <div
                className={cx(styles.incidentOptionItem)}
                onClick={(e) => onClickFn(e, AlertAction.unResolve, onAcknowledge, IncidentStatus.Acknowledged)}
              >
                Acknowledge{' '}
                {currentLoadingAction === IncidentStatus.Acknowledged && isLoading && (
                  <span className={cx(styles.incidentOptionEl)}>
                    <LoadingPlaceholder text="" />
                  </span>
                )}
              </div>
            </WithPermissionControlTooltip>
            <WithPermissionControlTooltip userAction={UserActions.AlertGroupsWrite}>
              <div
                className={cx(styles.incidentOptionItem)}
                onClick={(e) => onClickFn(e, AlertAction.unResolve, onResolve, IncidentStatus.Resolved)}
              >
                Resolve{' '}
                {currentLoadingAction === IncidentStatus.Resolved && isLoading && (
                  <span className={cx(styles.incidentOptionEl)}>
                    <LoadingPlaceholder text="" />
                  </span>
                )}
              </div>
            </WithPermissionControlTooltip>

            <div className={cx(styles.incidentOptionItem)}>
              <SilenceSelect
                placeholder={
                  currentLoadingAction === IncidentStatus.Silenced && isLoading ? 'Loading...' : 'Silence for'
                }
                onSelect={async (value) => {
                  setIsLoading(true);
                  setForcedOpenAction(AlertAction.unResolve);
                  setCurrentActionLoading(IncidentStatus.Silenced);

                  await onSilence(value);

                  setIsLoading(false);
                  setForcedOpenAction(undefined);
                  setCurrentActionLoading(undefined);
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
        <div className={cx(styles.incidentOptions, { [utilStyles.disabled]: isLoading })}>
          <WithPermissionControlTooltip userAction={UserActions.AlertGroupsWrite}>
            <div
              className={cx(styles.incidentOptionItem)}
              onClick={(e) => onClickFn(e, AlertAction.Silence, onUnsilence, IncidentStatus.Firing)}
            >
              Unsilence{' '}
              {currentLoadingAction === IncidentStatus.Firing && isLoading && (
                <span className={cx(styles.incidentOptionEl)}>
                  <LoadingPlaceholder text="" />
                </span>
              )}
            </div>
          </WithPermissionControlTooltip>
          <WithPermissionControlTooltip userAction={UserActions.AlertGroupsWrite}>
            <div
              className={cx(styles.incidentOptionItem)}
              onClick={(e) => onClickFn(e, AlertAction.Silence, onAcknowledge, IncidentStatus.Acknowledged)}
            >
              Acknowledge{' '}
              {currentLoadingAction === IncidentStatus.Acknowledged && isLoading && (
                <span className={cx(styles.incidentOptionEl)}>
                  <LoadingPlaceholder text="" />
                </span>
              )}
            </div>
          </WithPermissionControlTooltip>
          <WithPermissionControlTooltip userAction={UserActions.AlertGroupsWrite}>
            <div
              className={cx(styles.incidentOptionItem)}
              onClick={(e) => onClickFn(e, AlertAction.Silence, onAcknowledge, IncidentStatus.Resolved)}
            >
              Resolve{' '}
              {currentLoadingAction === IncidentStatus.Resolved && isLoading && (
                <span className={cx(styles.incidentOptionEl)}>
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
