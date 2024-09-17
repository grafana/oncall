import React from 'react';

import { css } from '@emotion/css';
import { GrafanaTheme2 } from '@grafana/data';
import { Button, Checkbox, Icon, Stack, Themeable2, withTheme2 } from '@grafana/ui';
import { UserActions, isUserActionAllowed } from 'helpers/authorization/authorization';
import { Lambda, observe } from 'mobx';
import { observer } from 'mobx-react';

import { GTable } from 'components/GTable/GTable';
import { Text } from 'components/Text/Text';
import { WithConfirm } from 'components/WithConfirm/WithConfirm';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { GlobalSetting } from 'models/global_setting/global_setting.types';
import { WithStoreProps } from 'state/types';
import { withMobXProviderContext } from 'state/withStore';

import { PLACEHOLDER } from './LiveSettings.config';
import { normalizeValue, prepareForUpdate } from './LiveSettings.helpers';

interface LiveSettingsProps extends WithStoreProps, Themeable2 {}

interface LiveSettingsState {
  hideValues: boolean;
}

@observer
class _LiveSettings extends React.Component<LiveSettingsProps, LiveSettingsState> {
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
        width: '20%',
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
        width: '10%',
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
    const styles = getStyles(this.props.theme);

    return (
      <div>
        <GTable
          tableLayout="fixed"
          emptyText={data ? 'No variables found' : 'Loading...'}
          title={() => (
            <div className={styles.header}>
              <Stack>
                <Text.Title level={3}>Env Variables</Text.Title>
              </Stack>
              <Stack justifyContent="flex-end">
                <WithPermissionControlTooltip userAction={UserActions.OtherSettingsWrite}>
                  <Button
                    variant="primary"
                    icon={hideValues ? 'eye' : 'eye-slash'}
                    onClick={this.handleToggleSecretsClick}
                  >
                    {hideValues ? 'Show values' : 'Hide values'}
                  </Button>
                </WithPermissionControlTooltip>
              </Stack>
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
      <div className={breakwordStyles}>
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
        <div className={breakwordStyles}>
          <Text type="warning">{item.error}</Text>
        </div>
      );
    }

    const styles = getStyles(this.props.theme);

    return (
      <div className={breakwordStyles}>
        <Text>
          <Icon className={styles.checkIcon} name="check" />
        </Text>
      </div>
    );
  };

  renderDescription = (item: GlobalSetting) => {
    const styles = getStyles(this.props.theme);

    return (
      <div
        dangerouslySetInnerHTML={{
          __html: item.description,
        }}
        className={styles.descriptionStyle}
      />
    );
  };

  renderDefault = (item: GlobalSetting) => {
    const { hideValues } = this.state;

    return (
      <div className={breakwordStyles}>
        <Text>{hideValues && item.is_secret ? PLACEHOLDER : normalizeValue(item.default_value)}</Text>
      </div>
    );
  };

  getEditValueChangeHandler = ({ id, name }: GlobalSetting) => {
    const { store } = this.props;
    const { globalSettingStore } = store;

    return async (value: string | boolean) => {
      await globalSettingStore.update(id, { name, value: prepareForUpdate(value) });
      this.update();
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

    return async () => {
      await globalSettingStore.delete(item.id);
      this.update();
    };
  };
}

const breakwordStyles = css`
  word-wrap: break-word;
  word-break: break-word;
  white-space: normal;
`;

const getStyles = (theme: GrafanaTheme2) => {
  return {
    alignTop: css`
      vertical-align: top;
    `,

    header: css`
      display: flex;
      justify-content: space-between;
    `,

    checkIcon: css`
      color: green;
    `,

    descriptionStyle: css`
      word-wrap: break-word;
      word-break: break-word;
      white-space: normal;

      a {
        color: ${theme.colors.primary.text};
      }
    `,
  };
};

export const LiveSettings = withMobXProviderContext(withTheme2(_LiveSettings));
