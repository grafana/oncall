import React, { useCallback, useState, useEffect } from 'react';

import { Button, HorizontalGroup, Drawer, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { debounce } from 'lodash-es';
import { observer } from 'mobx-react';

import { TemplateForEdit } from 'components/AlertTemplates/CommonAlertTemplatesForm.config';
import CheatSheet from 'components/CheatSheet/CheatSheet';
import {
  groupingTemplateCheatSheet,
  slackMessageTemplateCheatSheet,
  genericTemplateCheatSheet,
} from 'components/CheatSheet/CheatSheet.config';
import MonacoEditor from 'components/MonacoEditor/MonacoEditor';
import Text from 'components/Text/Text';
import TemplateResult from 'containers/TemplateResult/TemplateResult';
import TemplatesAlertGroupsList, { TEMPLATE_PAGE } from 'containers/TemplatesAlertGroupsList/TemplatesAlertGroupsList';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { AlertTemplatesDTO } from 'models/alert_templates';
import { Alert } from 'models/alertgroup/alertgroup.types';
import { ChannelFilter } from 'models/channel_filter/channel_filter.types';
import { TemplateOptions } from 'pages/integration/Integration.config';
import { waitForElement } from 'utils/DOM';
import LocationHelper from 'utils/LocationHelper';
import { UserActions } from 'utils/authorization';

import styles from './IntegrationTemplate.module.scss';

const cx = cn.bind(styles);

interface IntegrationTemplateProps {
  id: AlertReceiveChannel['id'];
  channelFilterId?: ChannelFilter['id'];
  template: TemplateForEdit;
  templateBody: string;
  templates: AlertTemplatesDTO[];
  onHide: () => void;
  onUpdateTemplates: (values: any) => void;
  onUpdateRoute: (values: any, channelFilterId?: ChannelFilter['id']) => void;
}

const IntegrationTemplate = observer((props: IntegrationTemplateProps) => {
  const { id, onHide, template, onUpdateTemplates, onUpdateRoute, templateBody, channelFilterId, templates } = props;

  const [isCheatSheetVisible, setIsCheatSheetVisible] = useState<boolean>(false);
  const [chatOpsPermalink, setChatOpsPermalink] = useState(undefined);
  const [alertGroupPayload, setAlertGroupPayload] = useState<JSON>(undefined);
  const [changedTemplateBody, setChangedTemplateBody] = useState<string>(templateBody);
  const [resultError, setResultError] = useState<string>(undefined);
  const [editorHeight, setEditorHeight] = useState<string>(undefined);
  const [isRecentAlertGroupExisting, setIsRecentAlertGroupExisting] = useState<boolean>(false);

  useEffect(() => {
    const locationParams: any = { template: template.name };
    if (template.isRoute) {
      locationParams.routeId = channelFilterId;
    }
    LocationHelper.update(locationParams, 'partial');
  }, []);

  useEffect(() => {
    waitForElement('#content-container-id').then(() => {
      const mainDiv = document.getElementById('content-container-id');
      const height = mainDiv?.getBoundingClientRect().height - 59;
      setEditorHeight(`${height}px`);
    });
  }, []);

  const onShowCheatSheet = useCallback(() => {
    setIsCheatSheetVisible(true);
  }, []);

  const onCloseCheatSheet = useCallback(() => {
    setIsCheatSheetVisible(false);
  }, []);

  const getChangeHandler = () => {
    return debounce((value: string) => {
      setChangedTemplateBody(value);
    }, 500);
  };

  const onEditPayload = (alertPayload: string) => {
    if (alertPayload !== null) {
      try {
        const jsonPayload = JSON.parse(alertPayload);
        if (typeof jsonPayload === 'object') {
          setResultError(undefined);
          setAlertGroupPayload(JSON.parse(alertPayload));
        } else {
          setResultError('Please check your JSON format');
        }
      } catch (e) {
        setResultError(e.message);
      }
    } else {
      setResultError(undefined);
      setAlertGroupPayload(undefined);
    }
  };

  const onSelectAlertGroup = useCallback((alertGroup: Alert) => {
    if (template.additionalData?.chatOpsName) {
      setChatOpsPermalink({
        permalink: alertGroup?.permalinks[template.additionalData?.chatOpsName],
      });
    }
  }, []);

  const onLoadAlertGroupsList = useCallback((isAlertGroup: boolean) => {
    setIsRecentAlertGroupExisting(isAlertGroup);
  }, []);

  const onSaveAndFollowLink = useCallback(
    (link: string) => {
      onUpdateTemplates({ [template.name]: changedTemplateBody });
      window.open(link, '_blank');
    },
    [onUpdateTemplates, onUpdateRoute, changedTemplateBody]
  );

  const handleSubmit = useCallback(() => {
    if (template.isRoute) {
      onUpdateRoute({ [template.name]: changedTemplateBody }, channelFilterId);
    } else {
      onUpdateTemplates({ [template.name]: changedTemplateBody });
    }
  }, [onUpdateTemplates, changedTemplateBody]);

  const getCheatSheet = (templateKey: string) => {
    switch (templateKey) {
      case TemplateOptions.Grouping.key:
      case TemplateOptions.Resolve.key:
        return groupingTemplateCheatSheet;
      case TemplateOptions.WebTitle.key:
      case TemplateOptions.WebMessage.key:
      case TemplateOptions.WebImage.key:
        return genericTemplateCheatSheet;
      case TemplateOptions.Autoacknowledge.key:
      case TemplateOptions.SourceLink.key:
      case TemplateOptions.Phone.key:
      case TemplateOptions.SMS.key:
      case TemplateOptions.SlackTitle.key:
      case TemplateOptions.SlackMessage.key:
      case TemplateOptions.SlackImage.key:
      case TemplateOptions.TelegramTitle.key:
      case TemplateOptions.TelegramMessage.key:
      case TemplateOptions.TelegramImage.key:
      case TemplateOptions.EmailTitle.key:
      case TemplateOptions.EmailMessage.key:
        return slackMessageTemplateCheatSheet;
      default:
        return genericTemplateCheatSheet;
    }
  };
  return (
    <Drawer
      title={
        <div className={cx('title-container')}>
          <HorizontalGroup justify="space-between" align="flex-start">
            <VerticalGroup>
              <Text.Title level={3}>Edit {template.displayName} template</Text.Title>
              {template.description && <Text type="secondary">{template.description}</Text>}
            </VerticalGroup>

            <HorizontalGroup>
              <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
                <Button variant="secondary" onClick={onHide}>
                  Cancel
                </Button>
              </WithPermissionControlTooltip>
              <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
                <Button variant="primary" onClick={handleSubmit}>
                  Save
                </Button>
              </WithPermissionControlTooltip>
            </HorizontalGroup>
          </HorizontalGroup>
        </div>
      }
      onClose={onHide}
      closeOnMaskClick={false}
      width={'95%'}
    >
      <div className={cx('container-wrapper')}>
        <div className={cx('container')} id={'content-container-id'}>
          <TemplatesAlertGroupsList
            templatePage={TEMPLATE_PAGE.Integrations}
            alertReceiveChannelId={id}
            onEditPayload={onEditPayload}
            onSelectAlertGroup={onSelectAlertGroup}
            templates={templates}
            onLoadAlertGroupsList={onLoadAlertGroupsList}
          />
          {renderCheatSheet()}
          <TemplateResult
            alertReceiveChannelId={id}
            template={template}
            templateBody={changedTemplateBody}
            isAlertGroupExisting={isRecentAlertGroupExisting}
            chatOpsPermalink={chatOpsPermalink}
            payload={alertGroupPayload}
            error={resultError}
            onSaveAndFollowLink={onSaveAndFollowLink}
          />
        </div>
      </div>
    </Drawer>
  );

  function renderCheatSheet() {
    if (isCheatSheetVisible) {
      return (
        <CheatSheet
          cheatSheetName={template.displayName}
          cheatSheetData={getCheatSheet(template.name)}
          onClose={onCloseCheatSheet}
        />
      );
    }

    return (
      <>
        <div className={cx('template-block-codeeditor')}>
          <div className={cx('template-editor-block-title')}>
            <HorizontalGroup justify="space-between" align="center" wrap>
              <Text>Template editor</Text>

              <Button variant="secondary" fill="outline" onClick={onShowCheatSheet} icon="book" size="sm">
                Cheatsheet
              </Button>
            </HorizontalGroup>
          </div>
          <div className={cx('template-editor-block-content')}>
            <MonacoEditor
              value={changedTemplateBody}
              data={templates}
              showLineNumbers={true}
              height={editorHeight}
              onChange={getChangeHandler()}
            />
          </div>
        </div>
      </>
    );
  }
});

export default IntegrationTemplate;
