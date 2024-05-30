import React, { Component } from 'react';

import { cx } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { Button, HorizontalGroup, Tooltip, withTheme2 } from '@grafana/ui';
import dayjs from 'dayjs';
import { observer } from 'mobx-react';
import { CSSTransition, TransitionGroup } from 'react-transition-group';

import { ScheduleFiltersType } from 'components/ScheduleFilters/ScheduleFilters.types';
import { Tag } from 'components/Tag/Tag';
import { Text } from 'components/Text/Text';
import { Rotation } from 'containers/Rotation/Rotation';
import { ScheduleOverrideForm } from 'containers/RotationForm/ScheduleOverrideForm';
import { TimelineMarks } from 'containers/TimelineMarks/TimelineMarks';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import {
  getOverrideColor,
  getOverridesFromStore,
  getShiftSwapsFromStore,
  scheduleViewToDaysInOneRow,
  SHIFT_SWAP_COLOR,
} from 'models/schedule/schedule.helpers';
import { Schedule, Shift, ShiftEvents, ShiftSwap } from 'models/schedule/schedule.types';
import { getCurrentTimeX } from 'pages/schedule/Schedule.helpers';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import { HTML_ID } from 'utils/DOM';
import { UserActions } from 'utils/authorization/authorization';

import { DEFAULT_TRANSITION_TIMEOUT } from './Rotations.config';
import { findColor } from './Rotations.helpers';
import { getRotationsStyles } from './Rotations.styles';

import animationStyles from './Rotations.module.css';

interface ScheduleOverridesProps extends WithStoreProps {
  shiftStartToShowOverrideForm: dayjs.Dayjs;
  shiftEndToShowOverrideForm: dayjs.Dayjs;
  scheduleId: Schedule['id'];
  shiftIdToShowRotationForm?: Shift['id'] | 'new';
  onShowRotationForm: (shiftId: Shift['id'] | 'new') => void;
  onShowShiftSwapForm: (id: ShiftSwap['id'] | 'new') => void;
  onCreate: () => void;
  onUpdate: () => void;
  onDelete: () => void;
  disabled: boolean;
  disableShiftSwaps: boolean;
  filters: ScheduleFiltersType;
  theme: GrafanaTheme2;
}

interface ScheduleOverridesState {
  shiftStartToShowOverrideForm?: dayjs.Dayjs;
  shiftEndToShowOverrideForm?: dayjs.Dayjs;
}

@observer
class _ScheduleOverrides extends Component<ScheduleOverridesProps, ScheduleOverridesState> {
  state: ScheduleOverridesState = {
    shiftStartToShowOverrideForm: undefined,
    shiftEndToShowOverrideForm: undefined,
  };

  render() {
    const {
      scheduleId,
      onCreate,
      onUpdate,
      onDelete,
      store,
      shiftIdToShowRotationForm,
      disabled,
      disableShiftSwaps,
      shiftStartToShowOverrideForm: propsShiftStartToShowOverrideForm,
      shiftEndToShowOverrideForm: propsShiftEndToShowOverrideForm,
      onShowShiftSwapForm,
      filters,
      theme,
    } = this.props;
    const { shiftStartToShowOverrideForm, shiftEndToShowOverrideForm } = this.state;

    const shifts = getOverridesFromStore(store, scheduleId, store.timezoneStore.calendarStartDate) as ShiftEvents[];

    const shiftSwaps = getShiftSwapsFromStore(store, scheduleId, store.timezoneStore.calendarStartDate);

    const currentTimeX = getCurrentTimeX(
      store.timezoneStore.currentDateInSelectedTimezone,
      store.timezoneStore.calendarStartDate,
      scheduleViewToDaysInOneRow[store.scheduleStore.scheduleView] * 24 * 60
    );

    const currentTimeHidden = currentTimeX < 0 || currentTimeX > 1;

    const schedule = store.scheduleStore.items[scheduleId];

    const isTypeReadOnly = !schedule?.enable_web_overrides;

    const styles = getRotationsStyles(theme);

    return (
      <>
        <div id={HTML_ID.SCHEDULE_OVERRIDES_AND_SWAPS} className={styles.root}>
          <div className={styles.header}>
            <HorizontalGroup justify="space-between">
              <Text.Title level={5} type="primary">
                Overrides and swaps
              </Text.Title>
              <HorizontalGroup>
                <Button
                  variant="secondary"
                  disabled={disableShiftSwaps}
                  onClick={() => {
                    onShowShiftSwapForm('new');
                  }}
                >
                  Request shift swap
                </Button>
                {isTypeReadOnly ? (
                  <Tooltip content="You can set an override using the override calendar" placement="top">
                    <div>
                      <Button variant="primary" icon="plus" disabled>
                        Add override
                      </Button>
                    </div>
                  </Tooltip>
                ) : (
                  <WithPermissionControlTooltip userAction={UserActions.SchedulesWrite}>
                    <Button disabled={disabled} icon="plus" onClick={this.handleAddOverride} variant="secondary">
                      Add override
                    </Button>
                  </WithPermissionControlTooltip>
                )}
              </HorizontalGroup>
            </HorizontalGroup>
          </div>
          <div className="u-position-relative">
            {!currentTimeHidden && <div className={styles.currentTime} style={{ left: `${currentTimeX * 100}%` }} />}
            <TimelineMarks />
            {shiftSwaps && shiftSwaps.length ? (
              <TransitionGroup className={cx(styles.layer, styles.layerFirst)}>
                <Tag className={styles.layerTitle}>
                  <Text type="primary" size="small">
                    Swaps
                  </Text>
                </Tag>
                {shiftSwaps.map(({ isPreview, events }, index) => (
                  <CSSTransition key={index} timeout={DEFAULT_TRANSITION_TIMEOUT} classNames={{ ...animationStyles }}>
                    <Rotation
                      events={events}
                      color={SHIFT_SWAP_COLOR}
                      onSlotClick={(event) => {
                        if (event.is_gap) {
                          return;
                        }
                        onShowShiftSwapForm(event.shiftSwapId);
                      }}
                      transparent={isPreview}
                      filters={filters}
                    />
                  </CSSTransition>
                ))}
              </TransitionGroup>
            ) : null}
            <TransitionGroup className={cx(styles.layer, { [styles.layerFirst]: !shiftSwaps || !shiftSwaps.length })}>
              {shifts && shifts.length ? (
                <CSSTransition key={-1} timeout={DEFAULT_TRANSITION_TIMEOUT} classNames={{ ...animationStyles }}>
                  <Tag className={styles.layerTitle}>
                    <Text type="primary" size="small">
                      Overrides
                    </Text>
                  </Tag>
                </CSSTransition>
              ) : null}
              {shifts && shifts.length ? (
                shifts.map(({ shiftId, isPreview, events }, index) => (
                  <CSSTransition key={index} timeout={DEFAULT_TRANSITION_TIMEOUT} classNames={{ ...animationStyles }}>
                    <Rotation
                      events={events}
                      color={getOverrideColor(index)}
                      onClick={(shiftStart, shiftEnd) => {
                        this.onRotationClick(shiftId, shiftStart, shiftEnd);
                      }}
                      transparent={isPreview}
                      filters={filters}
                    />
                  </CSSTransition>
                ))
              ) : (
                <CSSTransition key={0} timeout={DEFAULT_TRANSITION_TIMEOUT} classNames={{ ...animationStyles }}>
                  <Rotation
                    key={0}
                    events={[]}
                    onClick={(shiftStart, shiftEnd) => {
                      this.onRotationClick('new', shiftStart, shiftEnd);
                    }}
                  />
                </CSSTransition>
              )}
            </TransitionGroup>
          </div>
        </div>
        {shiftIdToShowRotationForm && (
          <ScheduleOverrideForm
            shiftId={shiftIdToShowRotationForm}
            shiftColor={findColor(shiftIdToShowRotationForm, undefined, shifts)}
            scheduleId={scheduleId}
            shiftStart={propsShiftStartToShowOverrideForm || shiftStartToShowOverrideForm}
            shiftEnd={propsShiftEndToShowOverrideForm || shiftEndToShowOverrideForm}
            onHide={() => {
              this.handleHide();

              store.scheduleStore.clearPreview();
            }}
            onUpdate={() => {
              this.handleHide();

              onUpdate();
            }}
            onCreate={() => {
              this.handleHide();

              onCreate();
            }}
            onDelete={() => {
              this.handleHide();

              onDelete();
            }}
          />
        )}
      </>
    );
  }

  onRotationClick = (shiftId: Shift['id'], shiftStart: dayjs.Dayjs, shiftEnd: dayjs.Dayjs) => {
    const { disabled } = this.props;

    if (disabled) {
      return;
    }

    this.setState({ shiftStartToShowOverrideForm: shiftStart, shiftEndToShowOverrideForm: shiftEnd }, () => {
      this.onShowRotationForm(shiftId);
    });
  };

  handleAddOverride = () => {
    const { store, disabled } = this.props;

    if (disabled) {
      return;
    }

    // use start of current day as default start time for override
    this.setState(
      { shiftStartToShowOverrideForm: store.timezoneStore.currentDateInSelectedTimezone.startOf('day') },
      () => {
        this.onShowRotationForm('new');
      }
    );
  };

  handleHide = () => {
    this.setState({ shiftStartToShowOverrideForm: undefined, shiftEndToShowOverrideForm: undefined }, () => {
      this.onShowRotationForm(undefined);
    });
  };

  onShowRotationForm = (shiftId: Shift['id']) => {
    const { onShowRotationForm } = this.props;

    onShowRotationForm(shiftId);
  };
}

export const ScheduleOverrides = withMobXProviderContext(withTheme2(_ScheduleOverrides));
