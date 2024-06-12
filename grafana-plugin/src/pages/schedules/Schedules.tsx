import React, { SyntheticEvent } from 'react';

import { cx } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { Button, HorizontalGroup, IconButton, LoadingPlaceholder, VerticalGroup, withTheme2 } from '@grafana/ui';
import { observer } from 'mobx-react';
import qs from 'query-string';
import { RouteComponentProps, withRouter } from 'react-router-dom';
import { getUtilStyles } from 'styles/utils.styles';

import { Avatar } from 'components/Avatar/Avatar';
import { NewScheduleSelector } from 'components/NewScheduleSelector/NewScheduleSelector';
import { PluginLink } from 'components/PluginLink/PluginLink';
import { GTable } from 'components/Table/Table';
import { Text } from 'components/Text/Text';
import { TextEllipsisTooltip } from 'components/TextEllipsisTooltip/TextEllipsisTooltip';
import { TooltipBadge } from 'components/TooltipBadge/TooltipBadge';
import { WithConfirm } from 'components/WithConfirm/WithConfirm';
import { RemoteFilters } from 'containers/RemoteFilters/RemoteFilters';
import { RemoteFiltersType } from 'containers/RemoteFilters/RemoteFilters.types';
import { ScheduleFinal } from 'containers/Rotations/ScheduleFinal';
import { SchedulePersonal } from 'containers/Rotations/SchedulePersonal';
import { ScheduleForm } from 'containers/ScheduleForm/ScheduleForm';
import { TeamName } from 'containers/TeamName/TeamName';
import { UserTimezoneSelect } from 'containers/UserTimezoneSelect/UserTimezoneSelect';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { Schedule, ScheduleView } from 'models/schedule/schedule.types';
import { getSlackChannelName } from 'models/slack_channel/slack_channel.helpers';
import { WithStoreProps, PageProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import { LocationHelper } from 'utils/LocationHelper';
import { UserActions } from 'utils/authorization/authorization';
import { PAGE, PLUGIN_ROOT, TEXT_ELLIPSIS_CLASS } from 'utils/consts';

import { getSchedulesStyles } from './Schedules.styles';

interface SchedulesPageProps extends WithStoreProps, RouteComponentProps, PageProps {
  theme: GrafanaTheme2;
}

interface SchedulesPageState {
  filters: RemoteFiltersType;
  showNewScheduleSelector: boolean;
  expandedRowKeys: Array<Schedule['id']>;
  scheduleIdToEdit?: Schedule['id'];
}

@observer
class _SchedulesPage extends React.Component<SchedulesPageProps, SchedulesPageState> {
  constructor(props: SchedulesPageProps) {
    super(props);

    this.state = {
      filters: { searchTerm: '', type: undefined, used: undefined, mine: undefined },
      showNewScheduleSelector: false,
      expandedRowKeys: [],
      scheduleIdToEdit: undefined,
    };
  }

  componentDidMount(): void {
    const {
      store: { userStore },
    } = this.props;

    userStore.fetchItems();
  }

  render() {
    const { store, query } = this.props;
    const { showNewScheduleSelector, expandedRowKeys, scheduleIdToEdit } = this.state;

    const { results, count, page_size } = store.scheduleStore.getSearchResult();

    const page = store.filtersStore.currentTablePageNum[PAGE.Schedules];
    const styles = getSchedulesStyles();

    return (
      <>
        <div>
          <div className={styles.title}>
            <HorizontalGroup justify="space-between">
              <Text.Title level={3}>Schedules</Text.Title>
              <div className={styles.schedulesActions}>
                <HorizontalGroup>
                  <Text type="secondary">View in timezone:</Text>
                  <UserTimezoneSelect onChange={this.refreshExpandedSchedules} />
                </HorizontalGroup>
                <WithPermissionControlTooltip userAction={UserActions.SchedulesWrite}>
                  <Button variant="primary" onClick={this.handleCreateScheduleClick}>
                    + New schedule
                  </Button>
                </WithPermissionControlTooltip>
              </div>
            </HorizontalGroup>
          </div>
          <div className={cx(styles.schedule, styles.schedulePersonal)}>
            <SchedulePersonal userPk={store.userStore.currentUserPk} />
          </div>
          <div className={styles.schedulesFiltersContainer}>
            <RemoteFilters
              query={query}
              page={PAGE.Schedules}
              grafanaTeamStore={store.grafanaTeamStore}
              onChange={this.handleSchedulesFiltersChange}
            />
          </div>
          <div data-testid="schedules-table">
            <GTable
              className={styles.table}
              columns={this.getTableColumns()}
              data={results}
              pagination={{
                page,
                total: results ? Math.ceil((count || 0) / page_size) : 0,
                onChange: this.handlePageChange,
              }}
              tableLayout="fixed"
              rowKey="id"
              expandable={{
                expandedRowKeys: expandedRowKeys,
                onExpand: this.handleExpandRow,
                expandedRowRender: this.renderSchedule,
                expandRowByClick: true,
              }}
              emptyText={results === undefined ? 'Loading...' : this.renderNotFound()}
            />
          </div>
        </div>

        {showNewScheduleSelector && (
          <NewScheduleSelector
            onCreate={this.handleCreateSchedule}
            onHide={() => {
              this.setState({ showNewScheduleSelector: false });
            }}
          />
        )}
        {scheduleIdToEdit && (
          <ScheduleForm
            id={scheduleIdToEdit}
            onSubmit={this.update}
            onHide={() => {
              this.setState({ scheduleIdToEdit: undefined });
            }}
          />
        )}
      </>
    );
  }

  renderNotFound() {
    return (
      <div>
        <Text type="secondary">Not found</Text>
      </div>
    );
  }

  handleCreateScheduleClick = () => {
    this.setState({ showNewScheduleSelector: true });
  };

  handleCreateSchedule = (data: Schedule) => {
    const { history, query } = this.props;

    history.push(`${PLUGIN_ROOT}/schedules/${data.id}?${qs.stringify(query)}`);
  };

  handleExpandRow = (expanded: boolean, data: Schedule) => {
    const { expandedRowKeys } = this.state;

    if (expanded && !expandedRowKeys.includes(data.id)) {
      this.setState({ expandedRowKeys: [...this.state.expandedRowKeys, data.id] }, () => {
        this.props.store.scheduleStore.refreshEvents(data.id, ScheduleView.OneWeek);
      });
    } else if (!expanded && expandedRowKeys.includes(data.id)) {
      const index = expandedRowKeys.indexOf(data.id);
      const newExpandedRowKeys = [...expandedRowKeys];
      newExpandedRowKeys.splice(index, 1);
      this.setState({ expandedRowKeys: newExpandedRowKeys });
    }
  };

  refreshExpandedSchedules = () => {
    const { expandedRowKeys } = this.state;
    expandedRowKeys.forEach((key: Schedule['id']) => {
      this.props.store.scheduleStore.refreshEvents(key, ScheduleView.OneWeek);
    });
  };

  renderSchedule = (data: Schedule) => {
    const styles = getSchedulesStyles();

    return (
      <div className={styles.schedule}>
        <ScheduleFinal
          scheduleView={ScheduleView.OneWeek}
          simplified
          scheduleId={data.id}
          onSlotClick={this.getScheduleClickHandler(data.id)}
        />
      </div>
    );
  };

  getScheduleClickHandler = (scheduleId: Schedule['id']) => {
    const { history, query } = this.props;

    return () => history.push(`${PLUGIN_ROOT}/schedules/${scheduleId}?${qs.stringify(query)}`);
  };

  renderType = (value: number) => {
    type tTypeToVerbal = {
      [key: number]: string;
    };
    const typeToVerbal: tTypeToVerbal = { 0: 'API/Terraform', 1: 'Ical', 2: 'Web' };
    return typeToVerbal[value];
  };

  renderStatus = (item: Schedule) => {
    const {
      store: { scheduleStore },
    } = this.props;

    const relatedEscalationChains = scheduleStore.relatedEscalationChains[item.id];
    return (
      <HorizontalGroup>
        {item.number_of_escalation_chains > 0 && (
          <TooltipBadge
            borderType="success"
            icon="link"
            text={item.number_of_escalation_chains}
            tooltipTitle="Used in escalations"
            tooltipContent={
              <VerticalGroup spacing="sm">
                {relatedEscalationChains ? (
                  relatedEscalationChains.length ? (
                    relatedEscalationChains.map((escalationChain) => (
                      <div key={escalationChain.pk}>
                        <PluginLink query={{ page: 'escalations', id: escalationChain.pk }} className="link">
                          <Text type="link">{escalationChain.name}</Text>
                        </PluginLink>
                      </div>
                    ))
                  ) : (
                    'Not used yet'
                  )
                ) : (
                  <LoadingPlaceholder text="Loading related escalation chains..." />
                )}
              </VerticalGroup>
            }
            onHover={this.getUpdateRelatedEscalationChainsHandler(item.id)}
          />
        )}

        {item.warnings?.length > 0 && (
          <TooltipBadge
            borderType="warning"
            icon="exclamation-triangle"
            text={item.warnings.length}
            tooltipTitle="Warnings"
            tooltipContent={
              <VerticalGroup spacing="none">
                {item.warnings.map((warning, index) => (
                  <Text type="primary" key={index}>
                    {warning}
                  </Text>
                ))}
              </VerticalGroup>
            }
          />
        )}
      </HorizontalGroup>
    );
  };

  renderName = (item: Schedule) => {
    const { query } = this.props;

    return <PluginLink query={{ page: 'schedules', id: item.id, ...query }}>{item.name}</PluginLink>;
  };

  renderOncallNow = (item: Schedule, _index: number) => {
    const { theme } = this.props;
    const utilsStyles = getUtilStyles(theme);

    if (item.on_call_now?.length > 0) {
      return (
        <div className="table__email-column">
          <VerticalGroup>
            {item.on_call_now.map((user) => {
              return (
                <PluginLink key={user.pk} query={{ page: 'users', id: user.pk }} className="table__email-content">
                  <HorizontalGroup>
                    <TextEllipsisTooltip placement="top" content={user.username}>
                      <Text type="secondary" className={cx(TEXT_ELLIPSIS_CLASS)}>
                        <Avatar size="small" src={user.avatar} />{' '}
                        <span className={cx(utilsStyles.wordBreakAll)}>{user.username}</span>
                      </Text>
                    </TextEllipsisTooltip>
                  </HorizontalGroup>
                </PluginLink>
              );
            })}
          </VerticalGroup>
        </div>
      );
    }
    return null;
  };

  renderChannelName = (value: Schedule) => {
    return getSlackChannelName(value.slack_channel) || '-';
  };

  renderUserGroup = (value: Schedule) => {
    return value.user_group?.handle || '-';
  };

  renderTeam(record: Schedule, teams: any) {
    return <TeamName team={teams[record.team]} />;
  }

  renderButtons = (item: Schedule) => {
    return (
      /* Wrapper div for onClick event to prevent expanding schedule view on delete/edit click */
      <div onClick={(event: SyntheticEvent) => event.stopPropagation()}>
        <HorizontalGroup>
          <WithPermissionControlTooltip key="edit" userAction={UserActions.SchedulesWrite}>
            <IconButton tooltip="Settings" name="cog" onClick={this.getEditScheduleClickHandler(item.id)} />
          </WithPermissionControlTooltip>
          <WithPermissionControlTooltip key="edit" userAction={UserActions.SchedulesWrite}>
            <WithConfirm>
              <IconButton tooltip="Delete" name="trash-alt" onClick={this.getDeleteScheduleClickHandler(item.id)} />
            </WithConfirm>
          </WithPermissionControlTooltip>
        </HorizontalGroup>
      </div>
    );
  };

  getEditScheduleClickHandler = (id: Schedule['id']) => {
    return () => {
      this.setState({ scheduleIdToEdit: id });
    };
  };

  getDeleteScheduleClickHandler = (id: Schedule['id']) => {
    const { store } = this.props;
    const { scheduleStore } = store;

    return async () => {
      await scheduleStore.delete(id);
      this.update();
    };
  };

  handleSchedulesFiltersChange = (filters: RemoteFiltersType, _isOnMount: boolean, invalidateFn: () => boolean) => {
    this.setState({ filters }, () => {
      this.applyFilters(invalidateFn);
    });
  };

  applyFilters = (invalidateFn?: () => boolean) => {
    const { scheduleStore, filtersStore } = this.props.store;
    const { filters } = this.state;
    const currentTablePage = filtersStore.currentTablePageNum[PAGE.Schedules];

    LocationHelper.update({ p: currentTablePage }, 'partial');
    scheduleStore.updateItems(filters, currentTablePage, invalidateFn);
  };

  handlePageChange = (page: number) => {
    const { store } = this.props;
    store.filtersStore.currentTablePageNum[PAGE.Schedules] = page;

    this.setState({ expandedRowKeys: [] }, this.applyFilters);
  };

  update = () => {
    const { store } = this.props;
    const page = store.filtersStore.currentTablePageNum[PAGE.Schedules];

    // For removal we need to check if count is 1, which means we should change the page to the previous one
    const { results } = store.scheduleStore.getSearchResult();
    const newPage = results.length === 1 ? Math.max(page - 1, 1) : page;

    store.scheduleStore.updatePersonalEvents(
      store.userStore.currentUserPk,
      store.timezoneStore.calendarStartDate,
      true
    );

    this.handlePageChange(newPage);
  };

  getUpdateRelatedEscalationChainsHandler = (scheduleId: Schedule['id']) => {
    const {
      store: { scheduleStore },
    } = this.props;

    return async () => {
      await scheduleStore.updateRelatedEscalationChains(scheduleId);
      this.forceUpdate();
    };
  };

  getTableColumns = () => {
    const { grafanaTeamStore } = this.props.store;
    const styles = getSchedulesStyles();

    return [
      {
        width: '10%',
        title: 'Type',
        dataIndex: 'type',
        render: this.renderType,
      },
      {
        width: '10%',
        title: 'Status',
        key: 'name',
        render: (item: Schedule) => this.renderStatus(item),
      },
      {
        width: '25%',
        title: 'Name',
        key: 'name',
        render: this.renderName,
      },
      {
        width: '25%',
        title: 'On-call now',
        key: 'users',
        render: this.renderOncallNow,
      },
      {
        width: '10%',
        title: 'Slack channel',
        render: this.renderChannelName,
      },
      {
        width: '10%',
        title: 'Slack user group',
        render: this.renderUserGroup,
      },
      {
        width: '20%',
        title: 'Team',
        render: (item: Schedule) => this.renderTeam(item, grafanaTeamStore.items),
      },
      {
        width: '50px',
        key: 'buttons',
        render: this.renderButtons,
        className: styles.buttons,
      },
    ];
  };
}

export const SchedulesPage = withRouter(withMobXProviderContext(withTheme2(_SchedulesPage)));
