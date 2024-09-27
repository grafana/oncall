import React, { Component } from 'react';

import { css, cx } from '@emotion/css';
import {
  Alert,
  LoadingPlaceholder,
  Icon,
  Button,
  InlineField,
  Input,
  Legend,
  ConfirmModal,
  Stack,
  Themeable2,
  withTheme2,
} from '@grafana/ui';
import { UserActions } from 'helpers/authorization/authorization';
import { StackSize, DOCS_SLACK_SETUP, getPluginId } from 'helpers/consts';
import { showApiError } from 'helpers/helpers';
import { useConfirmModal } from 'helpers/hooks';
import { observer } from 'mobx-react';

import { Block } from 'components/GBlock/Block';
import { PluginBridge, SupportedPlugin } from 'components/PluginBridge/PluginBridge';
import { PluginLink } from 'components/PluginLink/PluginLink';
import { Text } from 'components/Text/Text';
import { WithConfirm } from 'components/WithConfirm/WithConfirm';
import { GSelect } from 'containers/GSelect/GSelect';
import { RemoteSelect } from 'containers/RemoteSelect/RemoteSelect';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { SlackNewIcon } from 'icons/Icons';
import { PRIVATE_CHANNEL_NAME } from 'models/slack_channel/slack_channel.config';
import { SlackChannel } from 'models/slack_channel/slack_channel.types';
import { AppFeature } from 'state/features';
import { WithStoreProps } from 'state/types';
import { useStore } from 'state/useStore';
import { withMobXProviderContext } from 'state/withStore';

import { getSlackSettingsStyles } from './SlackSettings.styles';

interface SlackProps extends WithStoreProps, Themeable2 {}

interface SlackState {
  showENVVariablesButton: boolean;
}

@observer
class _SlackSettings extends Component<SlackProps, SlackState> {
  state: SlackState = {
    showENVVariablesButton: false,
  };

  componentDidMount() {
    this.onDidMount();
  }

  onDidMount = async () => {
    const { store } = this.props;
    if (store.hasFeature(AppFeature.LiveSettings)) {
      await this.getSlackLiveSettings();
    }
    this.update();
  };

  handleOpenSlackInstructions = async () => {
    const { store } = this.props;
    try {
      await store.slackStore.installSlackIntegration();
    } catch (err) {
      showApiError(err);
    }
  };

  update = () => {
    const { store } = this.props;

    store.slackChannelStore.updateItems();
    store.slackStore.updateSlackSettings();
  };

  getSlackLiveSettings = async () => {
    const { store } = this.props;
    const results = await store.globalSettingStore.getAll();

    const slackClientOAUTH = results.find((element: { name: string }) => element.name === 'SLACK_CLIENT_OAUTH_ID');
    const slackClientOAUTHSecret = results.find(
      (element: { name: string }) => element.name === 'SLACK_CLIENT_OAUTH_SECRET'
    );
    const slackRedirectHost = results.find((element: { name: string }) => element.name === 'SLACK_CLIENT_OAUTH_ID');
    const slackSigningSecret = results.find((element: { name: string }) => element.name === 'SLACK_SIGNING_SECRET');

    if (
      slackClientOAUTH?.error ||
      slackClientOAUTHSecret?.error ||
      slackRedirectHost?.error ||
      slackSigningSecret?.error
    ) {
      this.setState({ showENVVariablesButton: true });
    }
  };

  render() {
    const { currentOrganization } = this.props.store.organizationStore;

    if (!currentOrganization) {
      return <LoadingPlaceholder text="Loading..." />;
    }

    return currentOrganization?.slack_team_identity ? this.renderSlackIntegration() : this.renderSlackStub();
  }

  renderSlackIntegration = () => {
    const { store } = this.props;
    const {
      organizationStore: { currentOrganization },
      slackStore,
      slackChannelStore,
      // dereferencing items is needed to rerender GSelect
      slackChannelStore: { items: slackChannelItems },
    } = store;

    const isUnifiedSlackInstalled = !currentOrganization.slack_team_identity.needs_reinstall;
    const styles = getSlackSettingsStyles();

    const uninstallSlackButton = (
      <WithPermissionControlTooltip userAction={UserActions.ChatOpsUpdateSettings}>
        {isUnifiedSlackInstalled ? (
          <WithConfirm
            title="Uninstall IRM Slack integration"
            modalClass={styles.confirmUninstallModal}
            description={
              <div>
                <Alert severity="error" title="">
                  Are you sure you want to remove this integration from OnCall and Incident?
                </Alert>
                <p>
                  This action will uninstall the IRM Slack integration from OnCall and Incident. The following IRM data
                  will be permanently deleted:
                </p>
                <ul style={{ marginLeft: '20px' }}>
                  <li>OnCall default Slack channel</li>
                  <li>Slack channels for OnCall escalation policies</li>
                  <li>Slack channels and user groups for OnCall schedules</li>
                  <li>Linked Slack profiles for OnCall users</li>
                  <li>Incident announcement and automatic Slack channel creation</li>
                </ul>
                <br />
              </div>
            }
            confirmationText="UNINSTALL"
            confirmText="Uninstall"
          >
            <Button variant="destructive" fill="outline" onClick={() => this.removeSlackIntegration()}>
              Uninstall
            </Button>
          </WithConfirm>
        ) : (
          <WithConfirm
            title="Remove Slack Integration for all of OnCall"
            description={
              <Alert severity="error" title="WARNING">
                <p>Are you sure to delete this Slack Integration?</p>
                <p>Removing the integration will also irreverisbly remove the following data for your OnCall plugin:</p>
                <ul style={{ marginLeft: '20px' }}>
                  <li>default organization Slack channel</li>
                  <li>default Slack channels for OnCall Integrations</li>
                  <li>Slack channels & Slack user groups for OnCall Schedules</li>
                  <li>linked Slack usernames for OnCall Users</li>
                </ul>
                <br />
                <p>
                  If you would like to instead remove your linked Slack username, please head{' '}
                  <PluginLink query={{ page: 'users/me' }}>here</PluginLink>.
                </p>
              </Alert>
            }
            confirmationText="DELETE"
          >
            <Button variant="destructive" fill="outline" onClick={() => this.removeSlackIntegration()}>
              Uninstall
            </Button>
          </WithConfirm>
        )}
      </WithPermissionControlTooltip>
    );

    return (
      <div className={styles.root}>
        <Stack>
          <Legend>Slack OnCall settings</Legend>
          {uninstallSlackButton}
        </Stack>
        {currentOrganization.slack_team_identity.needs_reinstall && <UpgradeToUnifiedSlackBanner />}
        <InlineField label="Slack Workspace" grow disabled>
          <Input value={currentOrganization?.slack_team_identity?.cached_name} />
        </InlineField>
        <InlineField
          label="Default channel for Slack notifications"
          tooltip="The selected channel will be used as a fallback in the event that a schedule or integration does not have a configured channel"
        >
          <WithPermissionControlTooltip userAction={UserActions.ChatOpsUpdateSettings}>
            <GSelect<SlackChannel>
              items={slackChannelItems}
              fetchItemsFn={slackChannelStore.updateItems}
              fetchItemFn={slackChannelStore.updateItem}
              getSearchResult={slackChannelStore.getSearchResult}
              displayField="display_name"
              valueField="id"
              placeholder="Select Slack Channel"
              value={currentOrganization?.slack_channel?.id}
              onChange={this.handleSlackChannelChange}
              nullItemName={PRIVATE_CHANNEL_NAME}
            />
          </WithPermissionControlTooltip>
        </InlineField>
        <Alert
          severity="info"
          title="Tip: Create a separate channel for OnCall Slack App notifications (catch-all). Avoid using #general, etc."
        />
        <Legend>Additional settings</Legend>
        <InlineField
          label="Timeout for acknowledged alerts"
          tooltip="Slack app will send reminders into alert group slack thread and unacknowledge alert group if no confirmation is received."
        >
          <Stack gap={StackSize.xs}>
            <WithPermissionControlTooltip userAction={UserActions.ChatOpsWrite}>
              <RemoteSelect
                showSearch={false}
                href={'/slack_settings/acknowledge_remind_options/'}
                value={slackStore.slackSettings?.acknowledge_remind_timeout}
                onChange={this.getSlackSettingsChangeHandler('acknowledge_remind_timeout')}
              />
            </WithPermissionControlTooltip>
            <WithPermissionControlTooltip userAction={UserActions.ChatOpsWrite}>
              <RemoteSelect
                disabled={slackStore.slackSettings?.acknowledge_remind_timeout === 0}
                showSearch={false}
                href={'/slack_settings/unacknowledge_timeout_options/'}
                value={slackStore.slackSettings?.unacknowledge_timeout}
                onChange={this.getSlackSettingsChangeHandler('unacknowledge_timeout')}
              />
            </WithPermissionControlTooltip>
          </Stack>
        </InlineField>
        {isUnifiedSlackInstalled && (
          <div className={styles.linkToIncidentWrapper}>
            <PluginBridge plugin={SupportedPlugin.Incident}>
              <Text type="secondary">
                <a
                  href={`/a/${SupportedPlugin.Incident}/integrations/grate.irm.slack`}
                  target="_blank"
                  rel="noreferrer"
                >
                  <Text type="link">Open Slack Incident settings</Text>
                </a>
              </Text>
            </PluginBridge>
          </div>
        )}
      </div>
    );
  };

  removeSlackIntegration = async () => {
    const { store } = this.props;
    try {
      await store.slackStore.removeSlackIntegration();
      store.organizationStore.loadCurrentOrganization();
    } catch (err) {
      showApiError(err);
    }
  };

  getSlackSettingsChangeHandler = (field: string) => {
    const { store } = this.props;
    const { slackStore } = store;

    return (value: number | boolean) => {
      slackStore.saveSlackSettings({ [field]: value });
    };
  };

  handleSlackChannelChange = async (value: SlackChannel['id']) => {
    const { store } = this.props;
    const { slackStore } = store;

    await slackStore.setGeneralLogChannelId(value);

    store.organizationStore.loadCurrentOrganization();
  };

  renderSlackStub = () => {
    const { store } = this.props;
    const { showENVVariablesButton } = this.state;
    const isLiveSettingAvailable = store.hasFeature(AppFeature.LiveSettings) && showENVVariablesButton;
    const isUnifiedSlackEnabled = store.hasFeature(AppFeature.UnifiedSlack);
    const styles = getSlackSettingsStyles();

    return (
      <Stack gap={4} direction="column">
        <Stack justifyContent={'space-between'}>
          <Text.Title level={2}>Slack</Text.Title>
          {isLiveSettingAvailable ? (
            <PluginLink query={{ page: 'live-settings' }}>
              <Button variant="primary">Setup ENV Variables</Button>
            </PluginLink>
          ) : (
            <Stack grow={0}>
              <Button onClick={this.handleOpenSlackInstructions}>Install integration</Button>
              {store.hasFeature(AppFeature.LiveSettings) && (
                <PluginLink query={{ page: 'live-settings' }}>
                  <Button variant="secondary">See ENV Variables</Button>
                </PluginLink>
              )}
            </Stack>
          )}
        </Stack>
        <Block bordered withBackground className={styles.slackInfoblock}>
          <Stack direction="column" alignItems="center" gap={0}>
            <div className={styles.marginTop}>
              <SlackNewIcon />
            </div>
            <Text className={cx([styles.infoblockText, styles.marginTop])}>
              {isUnifiedSlackEnabled
                ? 'Connecting Slack App will allow you to manage alert groups and incidents in your team Slack workspace.'
                : 'Connecting Slack App will allow you to manage alert groups in your team Slack workspace.'}
            </Text>
            <Text className={cx(styles.infoblockText)}>
              Once the workspace is connected, team members need to link their Slack accounts to their IRM users to
              start using the app.
            </Text>
            {isLiveSettingAvailable && (
              <Text type="secondary" className={cx(styles.infoblockText, styles.marginTop)}>
                For bot creating instructions and additional information please read{' '}
                <a href={DOCS_SLACK_SETUP} target="_blank" rel="noreferrer">
                  <Text type="link">our documentation</Text>
                </a>
              </Text>
            )}
            <img
              style={{ height: '350px', display: 'block', margin: '0 auto' }}
              src={`public/plugins/${getPluginId()}/assets/img/slack_instructions.png`}
            />
          </Stack>
        </Block>
      </Stack>
    );
  };
}

const UpgradeToUnifiedSlackBanner = observer(() => {
  const {
    slackStore: { installSlackIntegration },
  } = useStore();
  const { modalProps, openModal } = useConfirmModal();
  const styles = getSlackSettingsStyles();

  const SLACK_MIGRATION_DOCS =
    'https://grafana.com/docs/grafana-cloud/alerting-and-irm/oncall/configure/integrations/references/slack/#migrate-to-the-grafana-irm-slack-integration';
  return (
    <div>
      <ConfirmModal {...modalProps} />
      <Alert severity="warning" title="This integration is outdated" buttonContent="Migrate">
        <div className={styles.upgradeSlackAlertText}>
          The OnCall Slack app is now a Grafana IRM app with new incident management features. Migrate now to access the
          enhanced capabilities.{' '}
          <a href={`${SLACK_MIGRATION_DOCS}`} target="_blank" rel="noreferrer">
            Learn more
          </a>
        </div>
        <Button
          className={styles.upgradeSlackBtn}
          variant="secondary"
          onClick={() =>
            openModal({
              confirmText: 'Migrate',
              onConfirm: installSlackIntegration,
              confirmButtonVariant: 'primary',
              title: `Migrate to Grafana IRM Slack integration`,
              description: (
                <div>
                  <p>
                    You will be redirected to Slack to approve additional permissions for the Grafana IRM Slack app. New
                    permissions are necessary for incident management features.
                  </p>
                  <p>After the migration, you can use OnCall and Incident features in a single app:</p>
                  <p>
                    <ul style={{ marginLeft: '20px' }}>
                      <li>The OnCall Slack configuration will remain intact.</li>
                      <li>
                        The Incident Slack integration will be upgraded to Grafana IRM Slack. Announcement and Create
                        Slack Channel hooks will be migrated, active incident can still be managed.
                      </li>
                    </ul>
                  </p>
                  <a href={`${SLACK_MIGRATION_DOCS}`} target="_blank" rel="noreferrer" className={styles.marginTop}>
                    <Text type="link">
                      <span>Learn more in the docs</span>
                      <Icon
                        name="external-link-alt"
                        className={css`
                          margin-left: 4px;
                          margin-bottom: 2px;
                        `}
                      />
                    </Text>
                  </a>
                </div>
              ),
              confirmVariant: 'secondary',
            })
          }
        >
          Migrate
        </Button>
      </Alert>
    </div>
  );
});

export const SlackSettings = withMobXProviderContext(withTheme2(_SlackSettings));
