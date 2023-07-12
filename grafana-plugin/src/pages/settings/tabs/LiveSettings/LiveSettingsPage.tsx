import React from 'react';

import { Button, Checkbox, HorizontalGroup, Icon } from '@grafana/ui';
import cn from 'classnames/bind';
import { observe } from 'mobx';
import { observer } from 'mobx-react';
import { Lambda } from 'mobx/lib/internal';

import GTable from 'components/GTable/GTable';
import Text from 'components/Text/Text';
import WithConfirm from 'components/WithConfirm/WithConfirm';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { GlobalSetting } from 'models/global_setting/global_setting.types';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';
import { isUserActionAllowed, UserActions } from 'utils/authorization';

import { PLACEHOLDER } from './LiveSettings.config';
import { normalizeValue, prepareForUpdate } from './LiveSettings.helpers';

import styles from './LiveSettings.module.css';

const cx = cn.bind(styles);

interface LiveSettingsProps extends WithStoreProps {}

interface LiveSettingsState {
  hideValues: boolean;
}

@observer
class LiveSettings extends React.Component<LiveSettingsProps, LiveSettingsState> {
  state: LiveSettingsState = {
    hideValues: true,
  };

  disposer: Lambda;

  constructor(props: LiveSettingsProps) {
    super(props);

    const { store } = props;

    this.disposer = observe(store.userStore, (change) => {
      if (change.name === 'currentUserPk') {
        this.update();
      }
    });
  }

  componentWillUnmount() {
    this.disposer();
  }
  componentDidMount() {
    this.update();
  }

  update = () => {
    const { store } = this.props;

    store.globalSettingStore.updateItems();
  };

  render() {
    const { store } = this.props;
    const { globalSettingStore } = store;
    const { hideValues } = this.state;

    const columns = [
      {
        width: '15%',
        title: 'Name',
        dataIndex: 'name',
        key: 'name',
      },
      {
        width: '25%',
        title: 'Description',
        render: this.renderDescription,
        key: 'description',
      },
      {
        width: '15%',
        render: this.renderError,
        title: 'Status',
        key: 'error',
        align: 'center',
      },
      {
        width: '20%',
        title: 'Value',
        render: (item: GlobalSetting) => this.renderValue(item), // to avoid caching previous render result
        key: 'value',
      },
      {
        width: '20%',
        title: 'ENV or default',
        render: (item: GlobalSetting) => this.renderDefault(item), // to avoid caching previous render result
        key: 'default',
      },
      {
        width: '5%',
        render: this.renderButtons,
        key: 'buttons',
        align: 'center',
      },
    ];

    const data: any = globalSettingStore.getSearchResult();

    return (
      <div className={cx('root')}>
        <GTable
          rowClassName={cx('row')}
          emptyText={data ? 'No variables found' : 'Loading...'}
          title={() => (
            <div className={cx('header')}>
              <HorizontalGroup>
                <Text.Title level={3}>Env Variables</Text.Title>
              </HorizontalGroup>
              <HorizontalGroup justify="flex-end">
                <WithPermissionControlTooltip userAction={UserActions.OtherSettingsWrite}>
                  <Button
                    variant="primary"
                    icon={hideValues ? 'eye' : 'eye-slash'}
                    onClick={this.handleToggleSecretsClick}
                  >
                    {hideValues ? 'Show values' : 'Hide values'}
                  </Button>
                </WithPermissionControlTooltip>
              </HorizontalGroup>
            </div>
          )}
          rowKey="id"
          // @ts-ignore // how to import AlignType?
          columns={columns}
          data={data}
        />
      </div>
    );
  }

  handleToggleSecretsClick = () => {
    this.setState({ hideValues: !this.state.hideValues });
  };

  renderValue = (item: GlobalSetting) => {
    const { hideValues } = this.state;

    if (item.value === true || item.value === false) {
      return (
        <Checkbox
          value={item.value}
          label={''}
          onChange={(event) => {
            this.getEditValueChangeHandler(item)(event.currentTarget.checked);
          }}
        />
      );
    }

    return (
      <div style={{ wordWrap: 'break-word', wordBreak: 'break-word' }}>
        <Text
          copyable={!item.is_secret && Boolean(item.value)}
          onTextChange={this.getEditValueChangeHandler(item)}
          editable={isUserActionAllowed(UserActions.OtherSettingsWrite)}
          clearBeforeEdit={item.is_secret}
          hidden={hideValues && item.is_secret}
        >
          {normalizeValue(item.value)}
        </Text>
      </div>
    );
  };

  renderError = (item: GlobalSetting) => {
    if (item.error) {
      return (
        <div style={{ wordWrap: 'break-word', wordBreak: 'break-word' }}>
          <Text type="warning">{item.error}</Text>
        </div>
      );
    }

    return (
      <div style={{ wordWrap: 'break-word', wordBreak: 'break-word' }}>
        <Text>
          <Icon className={cx('check-icon')} name="check" />
        </Text>
      </div>
    );
  };

  renderDescription = (item: GlobalSetting) => {
    return (
      <div
        dangerouslySetInnerHTML={{
          __html: item.description,
        }}
        className={cx('description-style')}
      />
    );
  };

  renderDefault = (item: GlobalSetting) => {
    const { hideValues } = this.state;

    return (
      <div style={{ wordWrap: 'break-word', wordBreak: 'break-word' }}>
        <Text>{hideValues && item.is_secret ? PLACEHOLDER : normalizeValue(item.default_value)}</Text>
      </div>
    );
  };

  getEditValueChangeHandler = ({ id, name }: GlobalSetting) => {
    const { store } = this.props;
    const { globalSettingStore } = store;

    return (value: string | boolean) => {
      globalSettingStore.update(id, { name, value: prepareForUpdate(value) }).then(this.update);
    };
  };

  renderButtons = (item: GlobalSetting) => {
    if (item.value === item.default_value) {
      return null;
    }

    return (
      <WithConfirm title="Are you sure to reset to default?" confirmText="Reset">
        <Button fill="text" variant="destructive" onClick={this.getResetGlobalSettingClickHandler(item)}>
          Reset to default
        </Button>
      </WithConfirm>
    );
  };

  getResetGlobalSettingClickHandler = (item: GlobalSetting) => {
    const { store } = this.props;
    const { globalSettingStore } = store;

    return () => {
      globalSettingStore.delete(item.id).then(this.update);
    };
  };
}

export default withMobXProviderContext(LiveSettings);
