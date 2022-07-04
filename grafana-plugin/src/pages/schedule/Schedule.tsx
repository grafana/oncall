import React, { useMemo } from 'react';

import { AppRootProps } from '@grafana/data';
import { Button, HorizontalGroup, VerticalGroup, RadioButtonGroup, IconButton, ToolbarButton } from '@grafana/ui';
import cn from 'classnames/bind';
import * as dayjs from 'dayjs';
import { observer } from 'mobx-react';
import Draggable from 'react-draggable';

// import Rotations from 'components/Rotations/Rotations';
import PluginLink from 'components/PluginLink/PluginLink';
import Rotations from 'components/Rotations/Rotations';
import ScheduleCounter from 'components/ScheduleCounter/ScheduleCounter';
import ScheduleQuality from 'components/ScheduleQuality/ScheduleQuality';
import Text from 'components/Text/Text';
// import UsersTimezones from 'components/UsersTimezones/UsersTimezones';
import UserTimezoneSelect from 'components/UserTimezoneSelect/UserTimezoneSelect';
import UsersTimezones from 'components/UsersTimezones/UsersTimezones';
import { Timezone } from 'models/timezone/timezone.types';
import { User } from 'models/user/user.types';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';

import { getRandomUsers } from './Schedule.helpers';

import styles from './Schedule.module.css';

const cx = cn.bind(styles);

interface SchedulePageProps extends AppRootProps, WithStoreProps {}

interface SchedulePageState {
  startMoment: dayjs.Dayjs;
  schedulePeriodType: string;
  renderType: string;
  users: User[];
  tz: Timezone;
}

@observer
class SchedulePage extends React.Component<SchedulePageProps, SchedulePageState> {
  state: SchedulePageState = {
    startMoment: dayjs().utc().startOf('week'),
    schedulePeriodType: 'week',
    renderType: 'timeline',
    users: getRandomUsers(),
    tz: 'Europe/Moscow',
  };

  async componentDidMount() {
    const { store } = this.props;

    store.userStore.updateItems();
  }

  componentDidUpdate() {}

  render() {
    const { startMoment, schedulePeriodType, renderType, users, tz } = this.state;
    const { query } = this.props;

    return (
      <div className={cx('root')}>
        <VerticalGroup spacing="lg">
          <HorizontalGroup justify="space-between">
            <HorizontalGroup>
              <PluginLink query={{ page: 'schedules' }}>
                <IconButton style={{ marginTop: '5px' }} name="arrow-left" size="xxl" />
              </PluginLink>
              <Text.Title level={3}>Schedule Team {query.id}</Text.Title>
              <ScheduleCounter
                type="link"
                count={5}
                tooltipTitle="Used in escalations"
                tooltipContent={
                  <>
                    <PluginLink query={{ page: 'integrations', id: 'CXBEG63MBJMDL' }}>Grafana 1</PluginLink>
                    <br />
                    <PluginLink query={{ page: 'integrations', id: 'CXBEG63MBJMDL' }}>Grafana 2</PluginLink>
                    <br />
                    <PluginLink query={{ page: 'integrations', id: 'CXBEG63MBJMDL' }}>Grafana 3</PluginLink>
                  </>
                }
              />
              <ScheduleCounter
                type="warning"
                count={2}
                tooltipTitle="Warnings"
                tooltipContent="Schedule has unassigned time periods during next 7 days"
              />
            </HorizontalGroup>
            <HorizontalGroup>
              <UserTimezoneSelect value={tz} users={users} onChange={this.handleTimezoneChange} />
              <ScheduleQuality quality={0.89} />
              <ToolbarButton icon="copy" tooltip="Copy" />
              <ToolbarButton icon="brackets-curly" tooltip="Code" />
              <ToolbarButton icon="share-alt" tooltip="Share" />
              <ToolbarButton icon="cog" tooltip="Settings" />
              <ToolbarButton icon="trash-alt" tooltip="Delete" />
            </HorizontalGroup>
          </HorizontalGroup>
          <Text className={cx('desc')} size="small" type="secondary">
            On-call Schedules. Use this to distribute notifications among team members you specified in the "Notify
            Users from on-call schedule" step in escalation chains.
          </Text>
          <div className={cx('users-timezones')}>
            <UsersTimezones users={users} tz={tz} onTzChange={this.handleTimezoneChange} />
          </div>
          <div className={cx('controls')}>
            <HorizontalGroup justify="space-between">
              <HorizontalGroup>
                <Button variant="secondary" onClick={this.handleTodayClick}>
                  Today
                </Button>
                <Button variant="secondary" onClick={this.handleLeftClick}>
                  &larr;
                </Button>
                <Button variant="secondary" onClick={this.handleRightClick}>
                  &rarr;
                </Button>
                <div>
                  {startMoment.format('DD MMM')} - {startMoment.add(6, 'day').format('DD MMM')}
                </div>
              </HorizontalGroup>
              <HorizontalGroup width="auto">
                <RadioButtonGroup
                  options={[
                    { label: 'Day', value: 'day' },
                    {
                      label: 'Week',
                      value: 'week',
                    },
                    { label: 'Month', value: 'month' },
                    { label: 'Custom', value: 'custom' },
                  ]}
                  value={schedulePeriodType}
                  onChange={this.handleShedulePeriodTypeChange}
                />
                <RadioButtonGroup
                  options={[
                    { label: 'Timeline', value: 'timeline' },
                    {
                      label: 'Grid',
                      value: 'grid',
                    },
                  ]}
                  value={renderType}
                  onChange={this.handleRenderTypeChange}
                />
              </HorizontalGroup>
            </HorizontalGroup>
          </div>
          {/* <div className={'current-time'} />*/}
          <div className={cx('rotations')}>
            {/*<Rotations startMoment={startMoment} title="Final schedule" />*/}
            <Rotations startMoment={startMoment} title="Rotations" />
            {/* <Rotations startMoment={startMoment} title="Overrides" />*/}
          </div>
        </VerticalGroup>
      </div>
    );
  }

  handleTimezoneChange = (value: Timezone) => {
    this.setState({ tz: value });
  };

  handleShedulePeriodTypeChange = (value: string) => {
    this.setState({ schedulePeriodType: value });
  };

  handleRenderTypeChange = (value: string) => {
    this.setState({ renderType: value });
  };

  handleTodayClick = () => {
    const { startMoment } = this.state;

    this.setState({ startMoment: dayjs().utc().startOf('week') });
  };

  handleLeftClick = () => {
    const { startMoment } = this.state;

    this.setState({ startMoment: startMoment.add(-7, 'day') });
  };

  handleRightClick = () => {
    const { startMoment } = this.state;

    this.setState({ startMoment: startMoment.add(7, 'day') });
  };
}

export default withMobXProviderContext(SchedulePage);
