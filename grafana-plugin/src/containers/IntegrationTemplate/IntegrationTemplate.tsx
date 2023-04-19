import React, { useCallback, useEffect, useState } from 'react';

import { Button, HorizontalGroup, Tooltip, Icon, Drawer, VerticalGroup, IconButton, InfoBox } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

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
  const [tempValues, setTempValues] = useState<{
    [key: string]: string | null;
  }>({});

  const onShowCheatSheet = useCallback(() => {
    setIsCheatSheetVisible(true);
  }, []);

  const onCloseCheatSheet = useCallback(() => {
    setIsCheatSheetVisible(false);
  }, []);

  const getChangeHandler = (templateName: string) => {
    return (value: string) => {
      setTempValues(() => ({
        [templateName]: value,
      }));
    };
  };

  const onSelectAlertGroup = useCallback((alert: Alert) => {
    if (alert?.slack_permalink) {
      setSlackPermalink(alert?.slack_permalink);
    }
  }, []);

  const handleSubmit = useCallback(() => {
    onUpdateTemplates(tempValues);
    onHide();
  }, [onUpdateTemplates, tempValues]);

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
          <AlertGroupsList alertReceiveChannelId={id} onSelectAlertGroup={onSelectAlertGroup} />
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
                  value={template.payload}
                  data={undefined}
                  showLineNumbers={true}
                  height={'1000px'}
                  onChange={getChangeHandler(template.name)}
                />
              </div>
            </>
          )}
          <Result
            alertReceiveChannelId={id}
            template={template}
            alertGroup={undefined}
            slackPermalink={slackPermalink}
          />
        </div>
      </Drawer>
    </>
  );
});

interface AlertGroupsListProps {
  alertReceiveChannelId: AlertReceiveChannel['id'];
  onSelectAlertGroup?: (alertGroup: Alert) => void;
}

const AlertGroupsList = (props: AlertGroupsListProps) => {
  const { alertReceiveChannelId, onSelectAlertGroup } = props;
  const store = useStore();
  const [alertGroupsList, setAlertGroupsList] = useState(undefined);
  const [selectedAlertPayload, setSelectedAlertPayload] = useState(undefined);
  const [isEditMode, setIsEditMode] = useState(false);

  useEffect(() => {
    store.alertGroupStore
      .getAlertGroupsForIntegration(alertReceiveChannelId)
      .then((result) => setAlertGroupsList(result));
    // const payload = store.alertReceiveChannelStore.templates[alertReceiveChannelId];
  }, []);

  const getAlertGroupPayload = async (id) => {
    const payloadIncident = await store.alertGroupStore.getAlertsFromGroup(id);
    const currentIncidentRawResponse = await store.alertGroupStore.getPayloadForIncident(
      payloadIncident?.alerts[0]?.id
    );
    onSelectAlertGroup(payloadIncident);
    setSelectedAlertPayload(currentIncidentRawResponse);
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

              <Button variant="secondary" fill="outline" onClick={undefined} size="sm">
                Use custom payload
              </Button>
            </HorizontalGroup>
          </div>
          <div className={cx('alert-groups-list')}>
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
          </div>
        </>
      )}
    </div>
  );
};

// interface TemplateEditorProps {
//   templateBody: any;
//   templateName: string;
//   onShowCheatSheet: () => void;
//   onEdit: () => void;
// }
// const TemplateEditor = (props: TemplateEditorProps) => {
//   const { templateBody, templateName, onShowCheatSheet } = props;

//   const [tempValues, setTempValues] = useState<{
//     [key: string]: string | null;
//   }>({});

//   const getChangeHandler = (templateName: string) => {
//     return (value: string) => {
//       setTempValues((oldTempValues) => ({
//         ...oldTempValues, // erase another edited templates
//         [templateName]: value,
//       }));
//     };
//   };

//   const handleSubmit = useCallback(() => {
//     const data = Object.keys(tempValues).reduce((acc: { [key: string]: string }, key: string) => {
//       if (templates[key] !== tempValues[key]) {
//         acc = { ...acc, [key]: tempValues[key] };
//       }
//       return acc;
//     }, {});
//     onUpdateTemplates(data);
//   }, [onUpdateTemplates, tempValues]);

//   return (
//     <div className={cx('template-block-codeeditor')}>
//       <div className={cx('template-editor-block-title')}>
//         <HorizontalGroup justify="space-between">
//           <Text>Template editor</Text>

//           <Button variant="secondary" fill="outline" onClick={onShowCheatSheet} icon="book" size="sm">
//             Cheatsheat
//           </Button>
//         </HorizontalGroup>
//       </div>

//       <MonacoJinja2Editor
//         value={templateBody}
//         data={undefined}
//         showLineNumbers={true}
//         height={'1000px'}
//         onChange={getChangeHandler(templateName)}
//       />
//     </div>
//   );
// };

interface ResultProps {
  alertReceiveChannelId: AlertReceiveChannel['id'];
  template: TemplateForEdit;
  alertGroup?: Alert;
  slackPermalink?: string;
}

const Result = (props: ResultProps) => {
  const { alertReceiveChannelId, template, slackPermalink } = props;
  const [isCondition, setIsCondition] = useState(false);

  const handleResult = (result) => {
    if (result?.preview === 'True') {
      setIsCondition(true);
    } else {
      setIsCondition(false);
    }
  };

  return (
    <div className={cx('template-block-result')}>
      <div className={cx('template-block-title')}>
        <HorizontalGroup justify="space-between">
          <Text>Result</Text>
        </HorizontalGroup>
      </div>
      <div className={cx('result')}>
        <TemplatePreview
          key={template.name}
          templateName={template.name}
          templateBody={template.payload}
          alertReceiveChannelId={alertReceiveChannelId}
          onResult={handleResult}
        />
        {template.name.includes('slack') && slackPermalink && (
          <>
            <a href={slackPermalink} target="_blank" rel="noreferrer">
              <Button>Save and open Alert Group in Slack</Button>
            </a>

            <Text type="secondary">Click "Acknowledge" and then "Unacknowledge" in Slack to trigger re-rendering.</Text>
          </>
        )}
        {template.name.includes('condition_template') && (
          <InfoBox severity={isCondition ? 'success' : 'error'}>{isCondition ? 'success' : 'error'}</InfoBox>
        )}
      </div>
    </div>
  );
};

export default IntegrationTemplate;
