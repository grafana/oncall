import React from 'react';

import { Button, Icon, LoadingPlaceholder, Tag, TextArea } from '@grafana/ui';
import { sentenceCase } from 'change-case';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';
import Emoji from 'react-emoji-render';

import PluginLink from 'components/PluginLink/PluginLink';
import Text from 'components/Text/Text';
import GSelect from 'containers/GSelect/GSelect';
import { PRIVATE_CHANNEL_NAME } from 'models/slack_channel/slack_channel.config';
import { makeRequest } from 'network';
import { withMobXProviderContext } from 'state/withStore';
import { showApiError } from 'utils';

import apiTokensImg from './img/api-tokens.png';

import styles from './MigrationTool.module.css';
import { PluginPage } from 'PluginPage';
import { pages } from 'pages';

const cx = cn.bind(styles);

interface MigrationToolProps {}

interface MigrationToolState {
  migrationStatus?: MIGRATION_STATUS;
  migrationInitiated?: boolean;
  migrationPlan?: any;
  apiKey: string;
  endpointsList?: string[];
}

enum MIGRATION_STATUS {
  NOT_STARTED = 'not_started',
  IN_PROGRESS = 'in_progress',
  FINISHED = 'finished',
}

function scrollIntoView(node: HTMLDivElement | null) {
  if (node) {
    node.scrollIntoView({ behavior: 'smooth' });
  }
}

@observer
class MigrationToolPage extends React.Component<MigrationToolProps, MigrationToolState> {
  state: MigrationToolState = {
    migrationStatus: undefined,
    migrationInitiated: false,
    migrationPlan: undefined,
    apiKey: '',
  };

  statusTimer: ReturnType<typeof setTimeout>;

  async componentDidMount() {
    this.checkStatus();
  }

  render() {
    const { migrationStatus, migrationInitiated, migrationPlan, apiKey, endpointsList } = this.state;

    return (
      <PluginPage pageNav={pages['migration-tool']}>
        <div className={cx('root')}>
          <p>
            <Text.Title level={3} className={cx('title')}>
              Migrate From Amixr.IO
            </Text.Title>
          </p>
          <div className={cx('desc')}>
            <p>Dear Amixr.IO customers!</p>
            <p>
              Amixr Inc. was acquired by Grafana Labs in 2021. Grafana OnCall is a very similar product, and most of you
              shouldn’t notice a lot of difference. We used the chance and made a few core improvements, which we hope
              will make your experience much better.
            </p>
            <p>
              We understand that it will put additional work on your shoulders. We did our best to prepare a migration
              tool to assist you with the migration process.
            </p>
            <p>
              Unfortunately, we no longer plan to support Amixr.IO and expect to shut down Amixr.IO to be able to focus
              on Grafana OnCall. The timeline is:
              <ul>
                <li>1 June 2022 - 31 June 2022 the migration tool will be available.</li>
                <li>30st of June Amixr.IO and all services located in this domain will be disabled.</li>
              </ul>
            </p>
            <p>
              How to prepare for the migration
              <ol>
                <li>
                  Ask all users from your Amixr.IO workspace to{' '}
                  <a href="https://grafana.com/auth/sign-up/create-user" target="_blank" rel="noreferrer">
                    sign up
                  </a>{' '}
                  in the Grafana Cloud.
                </li>
                <li>Request the migration plan.</li>
              </ol>
            </p>
            <p>
              For any technical assistance please reach out to our team in{' '}
              <a href="https://slack.grafana.com/" target="_blank" rel="noreferrer">
                Grafana Slack channel #grafana-oncall
              </a>
              . We’ll be happy to give you a hand and help you with migration on a call.
            </p>
            <p>For any questions related to pricing, or payments, please reach out to our sales:</p>
            <p>
              For any other questions:
              <ul>
                <li>
                  Matvey Kukuy (ex-CEO of Amixr):{' '}
                  <a href="mailto:matvey.kukuy@grafana.com" target="_blank" rel="noreferrer">
                    matvey.kukuy@grafana.com
                  </a>
                </li>
                <li>
                  Ildar Iskhakov (ex-CTO of Amixr):{' '}
                  <a href="mailto:ildar.iskhakov@grafana.com" target="_blank" rel="noreferrer">
                    ildar.iskhakov@grafana.com
                  </a>
                </li>
              </ul>
            </p>
          </div>
          {migrationStatus ? (
            <>
              {migrationStatus === MIGRATION_STATUS.NOT_STARTED && (
                <>
                  <hr />
                  <div className={cx('initiate-migration')}>
                    <p>
                      <Text.Title level={3}>Initiate migration to Grafana OnCall</Text.Title>
                    </p>
                    <p>Find API key in your Amixr.IO workspace -&gt; bottom of the “Settings” page:</p>
                    <p>
                      <img style={{ width: '600px' }} src={apiTokensImg} />
                    </p>
                    <p>Add Amixr.IO API Key to the field below:</p>
                    <p>
                      <TextArea
                        disabled={Boolean(migrationPlan)}
                        style={{ width: '600px' }}
                        rows={4}
                        onChange={(event) => {
                          this.setState({ apiKey: event.currentTarget.value });
                        }}
                      />
                    </p>
                    <p>
                      <Button
                        variant="secondary"
                        onClick={this.handleInitiateMigrationClick}
                        disabled={!apiKey.length || migrationInitiated}
                      >
                        Next Step: Build the migration plan
                      </Button>
                    </p>
                  </div>
                </>
              )}
              {migrationInitiated && (
                <>
                  <hr />
                  {migrationPlan ? (
                    <div className={cx('migration-plan')} ref={scrollIntoView}>
                      <p>
                        <Text.Title level={3}>Your migration plan</Text.Title>
                      </p>
                      {Object.keys(migrationPlan).map((key: string) => {
                        const item = migrationPlan[key];

                        return (
                          <p>
                            {key}:{' '}
                            {Array.isArray(item) && item.length ? (
                              <ul>
                                {item.map((subItem) => (
                                  <li>
                                    <Emoji text={subItem || ''} />
                                  </li>
                                ))}
                              </ul>
                            ) : Array.isArray(item) || !item ? (
                              '–'
                            ) : (
                              item
                            )}
                          </p>
                        );
                      })}
                      <p>
                        <Tag colorIndex={7} name="Attention" />{' '}
                        <Text>
                          Migration will be applied to the "General" team. Once you perform the migration there won’t be
                          possible to migrate data to the current Grafana OnCall workspace again. It’s a 1-time
                          operation.
                        </Text>
                      </p>
                      <p>
                        <Tag colorIndex={7} name="Attention" />{' '}
                        <Text>
                          Existing notification policies for migrated users will be replaced with policies from
                          Amixr.io. OnCall does not support notifications via email.
                        </Text>
                      </p>
                      <p>
                        <Tag colorIndex={7} name="Attention" />{' '}
                        <Text>
                          Only “ical” schedules will be migrated. User names in your calendars should not be prefixed
                          with '@', use bare usernames or emails.
                        </Text>
                      </p>
                      <p>
                        <Tag colorIndex={1} name="Info" />{' '}
                        <Text>
                          Unfortunately Grafana OnCall does not support Sentry OAuth-based integration. It won’t be
                          migrated. Please use Webhook integration instead and configure it after your migration will
                          finish. We’re sorry for the inconvenience.
                        </Text>
                      </p>
                      <p>
                        <Tag colorIndex={1} name="Info" />{' '}
                        <Text>
                          If you use terraform, please check our new terraform provider. We slightly changed it.
                        </Text>
                      </p>

                      <p>
                        <Button
                          variant="secondary"
                          onClick={this.handlePerformMigrationClick}
                          disabled={migrationStatus !== MIGRATION_STATUS.NOT_STARTED}
                        >
                          Next Step: Perform migration
                        </Button>
                      </p>
                    </div>
                  ) : (
                    <LoadingPlaceholder text="Loading Migration Plan..." />
                  )}
                </>
              )}
              {(migrationStatus === MIGRATION_STATUS.IN_PROGRESS || migrationStatus === MIGRATION_STATUS.FINISHED) && (
                <>
                  <hr />
                  <div className={cx('migration-status')} ref={scrollIntoView}>
                    <p>
                      {migrationStatus === MIGRATION_STATUS.FINISHED ? (
                        <Text.Title level={3} type="success">
                          Migration completed!
                        </Text.Title>
                      ) : (
                        <Text.Title level={3}>Migration started</Text.Title>
                      )}
                    </p>
                    <p>
                      {migrationStatus === MIGRATION_STATUS.IN_PROGRESS && <LoadingPlaceholder text="Migrating..." />}
                    </p>
                    <p>
                      {migrationStatus === MIGRATION_STATUS.IN_PROGRESS &&
                        "It may take a few hours (closing the tab won't stop the migration). "}
                      For now you need to do some actions to avoid collecting data in old Amixr.IO:
                      <ol>
                        <li>Update endpoints for alert sources:</li>
                        {endpointsList ? (
                          <ul>
                            {endpointsList.map((item) => (
                              <li>
                                <Emoji text={item || ''} />{' '}
                              </li>
                            ))}
                          </ul>
                        ) : null}
                        <li>Remove Slack & Telegram integrations in Amixr.IO.</li>
                        <li>Connect Slack & Telegram in Grafana OnCall.</li>
                        <li>Announce the start of migration to your colleagues!</li>
                      </ol>
                    </p>
                    <p>
                      <Tag colorIndex={1} name="Info" />{' '}
                      <Text type="secondary">
                        There is no way to re-migrate your Amixr.IO workspace to current OnCall workspace again. In case
                        you need to repeat the migration please use new Grafana Cloud workspace.
                      </Text>
                    </p>
                  </div>
                </>
              )}
            </>
          ) : (
            <LoadingPlaceholder text={'Loading migration status'} />
          )}
        </div>
      </PluginPage>
    );
  }

  handleInitiateMigrationClick = () => {
    const { apiKey } = this.state;

    this.setState({ migrationInitiated: true }, () => {
      makeRequest('/amixr_migration_plan/', { method: 'POST', data: { token: apiKey } })
        .then((data) => {
          this.setState({ migrationPlan: data });
        })
        .catch((error) => {
          this.setState({ migrationInitiated: false });

          throw error;
        })
        .catch(showApiError);
    });
  };

  handlePerformMigrationClick = () => {
    const { apiKey } = this.state;

    this.setState({ migrationStatus: MIGRATION_STATUS.IN_PROGRESS }, () => {
      makeRequest('/migrate_from_amixr/', { method: 'POST', data: { token: apiKey } })
        .then(this.startMigrationStatusPolling)
        .catch((error) => {
          this.setState({ migrationStatus: MIGRATION_STATUS.NOT_STARTED });

          throw error;
        })
        .catch(showApiError);
    });
  };

  startMigrationStatusPolling = () => {
    this.statusTimer = setInterval(this.checkStatus, 20000);
  };

  stopMigrationStatusPolling = () => {
    clearInterval(this.statusTimer);
  };

  checkStatus = () => {
    const { apiKey } = this.state;

    makeRequest('/amixr_migration_status/', { data: { token: apiKey } })
      .then(({ migration_status, endpoints_list }) => {
        this.setState({ migrationStatus: migration_status, endpointsList: endpoints_list });

        switch (migration_status) {
          case 'in_progress':
            if (!this.statusTimer) {
              this.startMigrationStatusPolling();
            }

            break;
        }
      })
      .catch((error) => {
        this.stopMigrationStatusPolling();

        throw error;
      })
      .catch(showApiError);
  };

  componentWillUnmount() {
    this.stopMigrationStatusPolling();
  }
}

export default withMobXProviderContext(MigrationToolPage);
