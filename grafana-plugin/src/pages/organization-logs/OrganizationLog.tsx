import React from 'react';

import { Button, HorizontalGroup, Tag, Tooltip } from '@grafana/ui';
import cn from 'classnames/bind';
import { debounce } from 'lodash-es';
import { observer } from 'mobx-react';
import moment, { Moment } from 'moment-timezone';
import { RouteComponentProps } from 'react-router-dom';

import Avatar from 'components/Avatar/Avatar';
import GTable from 'components/GTable/GTable';
import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import OrganizationLogFilters from 'containers/OrganizationLogFilters/OrganizationLogFilters';
import logo from 'img/logo.svg';
import { OrganizationLog } from 'models/organization_log/organization_log.types';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import sanitize from 'utils/sanitize';

import styles from './OrganizationLog.module.css';

const cx = cn.bind(styles);

interface OrganizationLogProps extends WithStoreProps, RouteComponentProps {}

interface OrganizationLogState {
  filters: { [key: string]: any };
  page: number;
  expandedLogsKeys: string[];
}

const INITIAL_FILTERS = {};

const ITEMS_PER_PAGE = 50;

@observer
class OrganizationLogPage extends React.Component<OrganizationLogProps, OrganizationLogState> {
  state: OrganizationLogState = { filters: { ...INITIAL_FILTERS }, page: 1, expandedLogsKeys: [] };

  componentDidMount() {
    this.refresh();
  }

  refresh = () => {
    const { store } = this.props;

    const { filters, page } = this.state;
    store.OrganizationLogStore.updateItems('', page, {
      ...filters,
      created_at: filters.created_at
        ? filters.created_at.map((m: Moment) => m.utc().format('YYYY-MM-DDTHH:mm:ss')).join('/')
        : undefined,
    });
  };

  debouncedRefresh = debounce(this.refresh, 500);

  render() {
    const { filters, expandedLogsKeys } = this.state;
    const { store } = this.props;
    const { OrganizationLogStore } = store;

    const columns = [
      {
        width: '40%',
        title: 'Action',
        render: this.renderShortDescription,
        key: 'action',
      },
      {
        width: '10%',
        title: 'User',
        render: this.renderUser,
        key: 'user',
      },
      {
        width: '30%',
        title: 'Labels',
        render: this.renderLabels,
        key: 'labels',
      },
      {
        width: '20%',
        title: 'Time',
        render: this.renderCreatedAt,
        key: 'created_at',
      },
    ];

    const searchResult: any = OrganizationLogStore.getSearchResult() || {};

    const { total, page, results } = searchResult;

    const loading = !results;

    return (
      <div className={cx('root')}>
        <OrganizationLogFilters value={filters} onChange={this.handleChangeOrganizationLogFilters} />
        <GTable
          rowKey="id"
          title={() => (
            <div className={cx('header')}>
              <Text.Title className={cx('users-title')} level={3}>
                Organization Logs
              </Text.Title>
              <Button onClick={this.refresh} icon={loading ? 'fa fa-spinner' : 'sync'}>
                Refresh
              </Button>
            </div>
          )}
          showHeader={true}
          data={results}
          loading={loading}
          emptyText={results ? 'No logs found' : 'Loading...'}
          columns={columns}
          pagination={{
            page,
            total: Math.ceil((total || 0) / ITEMS_PER_PAGE),
            onChange: this.handleChangePage,
          }}
          rowClassName={cx('align-top')}
          expandable={{
            expandedRowRender: this.renderFullDescription,
            expandRowByClick: true,
            expandedRowKeys: expandedLogsKeys,
            onExpandedRowsChange: this.handleExpandedRowsChange,
          }}
        />
      </div>
    );
  }

  handleExpandedRowsChange = (expandedRows: string[]) => {
    this.setState({ expandedLogsKeys: expandedRows });
  };

  handleChangePage = (page: number) => {
    this.setState({ page }, this.refresh);
  };

  handleChangeOrganizationLogFilters = (filters: any) => {
    this.setState({ filters, page: 1 }, this.debouncedRefresh);
  };

  renderShortDescription = (item: OrganizationLog) => {
    return <div className={cx('short-description')}>{item.description}</div>;
  };

  renderFullDescription = (item: OrganizationLog) => {
    return (
      <div
        dangerouslySetInnerHTML={{
          __html: sanitize(item.description),
        }}
      />
    );
  };

  renderUser = (item: OrganizationLog) => {
    if (!item.author) {
      return (
        <Tooltip content="System event">
          <Avatar size="large" className={cx('no-background')} src={logo} />
        </Tooltip>
      );
    }

    return (
      <PluginLink query={{ page: 'users', id: item.author.pk }}>
        <Tooltip placement="top" key={item.author.pk} content={item.author.username}>
          <span>
            <Avatar size="large" src={item.author.avatar} />
          </span>
        </Tooltip>
      </PluginLink>
    );
  };

  renderLabels = (item: OrganizationLog) => {
    if (!item.labels) {
      return null;
    }

    return (
      <HorizontalGroup wrap>
        {item.labels.map((label) => (
          <Tag key={label} name={label} />
        ))}
      </HorizontalGroup>
    );
  };

  renderCreatedAt = (item: OrganizationLog) => {
    return moment(item.created_at).toString();
  };
}

export default withMobXProviderContext(OrganizationLogPage);
