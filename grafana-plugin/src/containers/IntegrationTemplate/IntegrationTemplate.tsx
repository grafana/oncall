import React, { useCallback, useEffect, useState } from 'react';

import { Button, HorizontalGroup, Tooltip, Icon, Drawer, VerticalGroup, IconButton } from '@grafana/ui';
import cn from 'classnames/bind';
import { debounce } from 'lodash-es';
import { observer } from 'mobx-react';
// import { useDebouncedCallback } from 'utils/hooks';

import { TemplateForEdit } from 'components/AlertTemplates/AlertTemplatesForm.config';
import CheatSheet from 'components/CheatSheet/CheatSheet';
import {
  groupingTemplateCheatSheet,
  slackMessageTemplateCheatSheet,
  webTitleTemplateCheatSheet,
} from 'components/CheatSheet/CheatSheet.config';
import MonacoJinja2Editor from 'components/MonacoJinja2Editor/MonacoJinja2Editor';
import SourceCode from 'components/SourceCode/SourceCode';
import Text from 'components/Text/Text';
import TemplatePreview from 'containers/TemplatePreview/TemplatePreview';
import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { Alert } from 'models/alertgroup/alertgroup.types';
import { useStore } from 'state/useStore';

import styles from './IntegrationTemplate.module.css';

const cx = cn.bind(styles);
// const PAYLOAD_CHANGE_DEBOUNCE_MS = 1000;

interface IntegrationTemplateProps {
  id: AlertReceiveChannel['id'];
  template: TemplateForEdit;
  onHide: () => void;
  onUpdateTemplates: (values: any) => void;
}

const IntegrationTemplate = observer((props: IntegrationTemplateProps) => {
  const { id, onHide, template, onUpdateTemplates } = props;

  const [isCheatSheetVisible, setIsCheatSheetVisible] = useState<boolean>(false);
  const [slackPermalink, setSlackPermalink] = useState<string>(undefined);
  const [alertGroupPayload, setAlertGroupPayload] = useState<JSON>(undefined);
  const [templateBody, setTemplateBody] = useState<string>(template.body);

  const onShowCheatSheet = useCallback(() => {
    setIsCheatSheetVisible(true);
  }, []);

  const onCloseCheatSheet = useCallback(() => {
    setIsCheatSheetVisible(false);
  }, []);

  const getChangeHandler = () => {
    return (value: string) => {
      setTemplateBody(value);
    };
  };

  const onEditPayload = (alertPayload: JSON) => {
    setAlertGroupPayload(alertPayload);
  };

  const onSelectAlertGroup = useCallback((alertGroup: Alert) => {
    setSlackPermalink(alertGroup?.slack_permalink);
  }, []);

  const handleSubmit = useCallback(() => {
    onUpdateTemplates({ [template.name]: templateBody });
    onHide();
  }, [onUpdateTemplates, templateBody]);

  const getCheatSheet = (templateName) => {
    switch (templateName) {
      case 'Grouping':
      case 'Autoresolve':
        return groupingTemplateCheatSheet;
      case 'Web titile':
      case 'Web message':
      case 'Web image':
        return webTitleTemplateCheatSheet;
      case 'Auto acknowledge':
      case 'Source link':
      case 'Phone call':
      case 'SMS':
      case 'Slack title':
      case 'Slack message':
      case 'Slack image':
      case 'Telegram title':
      case 'Telegram message':
      case 'Telegram image':
      case 'Email title':
      case 'Email message':
        return slackMessageTemplateCheatSheet;
      default:
        return webTitleTemplateCheatSheet;
    }
  };
  return (
    <>
      <Drawer
        title={
          <div className={cx('title-container')}>
            <HorizontalGroup justify="space-between">
              <VerticalGroup>
                <Text.Title level={3}>Edit {template.displayName} template</Text.Title>
                <Text type="secondary">
                  When monitoring systems return to normal, they can send "resolve" alerts. OnCall can use these signals
                  to resolve alert groups accordingly.
                </Text>
              </VerticalGroup>

              <HorizontalGroup>
                <Button variant="secondary" onClick={onHide}>
                  Cancel
                </Button>
                <Button variant="primary" onClick={handleSubmit}>
                  Save
                </Button>
              </HorizontalGroup>
            </HorizontalGroup>
          </div>
        }
        onClose={onHide}
        closeOnMaskClick={false}
        width={'95%'}
      >
        <div className={cx('container')}>
          <AlertGroupsList
            alertReceiveChannelId={id}
            onEditPayload={onEditPayload}
            onSelectAlertGroup={onSelectAlertGroup}
          />
          {isCheatSheetVisible ? (
            <CheatSheet cheatSheetData={getCheatSheet(template.displayName)} onClose={onCloseCheatSheet} />
          ) : (
            <>
              <div className={cx('template-block-codeeditor')}>
                <div className={cx('template-editor-block-title')}>
                  <HorizontalGroup justify="space-between">
                    <Text>Template editor</Text>

                    <Button variant="secondary" fill="outline" onClick={onShowCheatSheet} icon="book" size="sm">
                      Cheatsheat
                    </Button>
                  </HorizontalGroup>
                </div>

                <MonacoJinja2Editor
                  value={template.body}
                  data={undefined}
                  showLineNumbers={true}
                  height={'1000px'}
                  onChange={getChangeHandler()}
                />
              </div>
            </>
          )}
          {alertGroupPayload ? (
            <Result
              alertReceiveChannelId={id}
              templateName={template.name}
              templateBody={templateBody}
              alertGroup={undefined}
              slackPermalink={slackPermalink}
              payload={alertGroupPayload}
            />
          ) : (
            <div className={cx('template-block-result')}>
              <div className={cx('template-editor-block-title')}>
                <Text>Please select Alert group to see end result</Text>
              </div>
            </div>
          )}
        </div>
      </Drawer>
    </>
  );
});

interface AlertGroupsListProps {
  alertReceiveChannelId: AlertReceiveChannel['id'];
  onSelectAlertGroup?: (alertGroup: Alert) => void;
  onEditPayload?: (payload: JSON) => void;
}

const AlertGroupsList = (props: AlertGroupsListProps) => {
  const { alertReceiveChannelId, onEditPayload, onSelectAlertGroup } = props;
  const store = useStore();
  const [alertGroupsList, setAlertGroupsList] = useState(undefined);
  const [selectedAlertPayload, setSelectedAlertPayload] = useState<string>(undefined);
  const [isEditMode, setIsEditMode] = useState(false);

  useEffect(() => {
    store.alertGroupStore
      .getAlertGroupsForIntegration(alertReceiveChannelId)
      .then((result) => setAlertGroupsList(result));
  }, []);

  const getChangeHandler = () => {
    return debounce((value: string) => {
      onEditPayload(JSON.parse(value));
    }, 1000);
  };

  const getAlertGroupPayload = async (id) => {
    const groupedAlert = await store.alertGroupStore.getAlertsFromGroup(id);
    const currentIncidentRawResponse = await store.alertGroupStore.getPayloadForIncident(groupedAlert?.alerts[0]?.id);
    setSelectedAlertPayload(currentIncidentRawResponse?.raw_request_data);
    onSelectAlertGroup(groupedAlert);
    onEditPayload(currentIncidentRawResponse?.raw_request_data);
  };

  return (
    <div className={cx('template-block-list')}>
      {selectedAlertPayload ? (
        <>
          <div className={cx('template-block-title')}>
            <HorizontalGroup justify="space-between">
              <Text>Selected Alert</Text>

              <HorizontalGroup>
                <IconButton name="edit" onClick={() => setIsEditMode(true)} />
                <IconButton name="times" onClick={() => setSelectedAlertPayload(undefined)} />
              </HorizontalGroup>
            </HorizontalGroup>
          </div>
          <div className={cx('alert-groups-list')}>
            {isEditMode ? (
              <MonacoJinja2Editor
                value={JSON.stringify(selectedAlertPayload, null, 4)}
                data={undefined}
                height={'600px'}
                onChange={getChangeHandler()}
                showLineNumbers
              />
            ) : (
              <SourceCode>{JSON.stringify(selectedAlertPayload, null, 4)}</SourceCode>
            )}
          </div>
        </>
      ) : (
        <>
          <div className={cx('template-block-title')}>
            <HorizontalGroup justify="space-between">
              <HorizontalGroup>
                <Text>Recent Alert groups</Text>
                <Tooltip content="Here will be information about alert groups">
                  <Icon name="info-circle" />
                </Tooltip>
              </HorizontalGroup>

              <Button variant="secondary" fill="outline" onClick={() => setIsEditMode(true)} size="sm">
                Use custom payload
              </Button>
            </HorizontalGroup>
          </div>
          <div className={cx('alert-groups-list')}>
            {isEditMode ? (
              <MonacoJinja2Editor
                value={null}
                data={undefined}
                height={'600px'}
                onChange={getChangeHandler()}
                showLineNumbers
              />
            ) : (
              <>
                {alertGroupsList && (
                  <>
                    {alertGroupsList.map((alertGroup) => {
                      return (
                        <div key={alertGroup.pk}>
                          <Button fill="text" onClick={() => getAlertGroupPayload(alertGroup.pk)}>
                            {alertGroup?.render_for_web.title}
                          </Button>
                        </div>
                      );
                    })}
                  </>
                )}
              </>
            )}
          </div>
        </>
      )}
    </div>
  );
};

interface ResultProps {
  alertReceiveChannelId: AlertReceiveChannel['id'];
  templateName: string;
  templateBody: string;
  alertGroup?: Alert;
  slackPermalink?: string;
  payload?: JSON;
}

const Result = (props: ResultProps) => {
  const { alertReceiveChannelId, templateName, slackPermalink, payload, templateBody } = props;

  return (
    <div className={cx('template-block-result')}>
      <div className={cx('template-block-title')}>
        <HorizontalGroup justify="space-between">
          <Text>Result</Text>
        </HorizontalGroup>
      </div>
      <div className={cx('result')}>
        <TemplatePreview
          key={templateName}
          templateName={templateName}
          templateBody={templateBody}
          alertReceiveChannelId={alertReceiveChannelId}
          // onResult={handleResult}
          payload={payload}
        />
        {templateName.includes('slack') && slackPermalink && (
          <>
            <a href={slackPermalink} target="_blank" rel="noreferrer">
              <Button>Save and open Alert Group in Slack</Button>
            </a>

            <Text type="secondary">Click "Acknowledge" and then "Unacknowledge" in Slack to trigger re-rendering.</Text>
          </>
        )}
      </div>
    </div>
  );
};

export default IntegrationTemplate;
