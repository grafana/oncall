import React, { useCallback, useState } from 'react';

import { Button, Drawer, HorizontalGroup, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { debounce } from 'lodash-es';

import { CheatSheet } from 'components/CheatSheet/CheatSheet';
import { genericTemplateCheatSheet, webhookPayloadCheatSheet } from 'components/CheatSheet/CheatSheet.config';
import { MonacoEditor } from 'components/MonacoEditor/MonacoEditor';
import { Text } from 'components/Text/Text';
import styles from 'containers/IntegrationTemplate/IntegrationTemplate.module.scss';
import { TemplateResult } from 'containers/TemplateResult/TemplateResult';
import { TemplatesAlertGroupsList, TEMPLATE_PAGE } from 'containers/TemplatesAlertGroupsList/TemplatesAlertGroupsList';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { UserActions } from 'utils/authorization/authorization';

const cx = cn.bind(styles);

interface Template {
  value: string;
  displayName: string;
  description?: string;
  name: string;
}

interface WebhooksTemplateEditorProps {
  template: Template;
  id: ApiSchemas['Webhook']['id'];
  onHide: () => void;
  handleSubmit: (template: string) => void;
}

export const WebhooksTemplateEditor: React.FC<WebhooksTemplateEditorProps> = ({
  template,
  id,
  onHide,
  handleSubmit,
}) => {
  const [isCheatSheetVisible, setIsCheatSheetVisible] = useState(false);
  const [changedTemplateBody, setChangedTemplateBody] = useState(template.value);
  const [selectedPayload, setSelectedPayload] = useState();
  const [resultError, setResultError] = useState<string>(undefined);

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
          setSelectedPayload(JSON.parse(alertPayload));
        } else {
          setResultError('Please check your JSON format');
        }
      } catch (e) {
        setResultError(e.message);
      }
    } else {
      setResultError(undefined);
      setSelectedPayload(undefined);
    }
  };

  const onShowCheatSheet = useCallback(() => {
    setIsCheatSheetVisible(true);
  }, []);

  const onCloseCheatSheet = useCallback(() => {
    setIsCheatSheetVisible(false);
  }, []);

  const getCheatSheet = (templateKey: string) => {
    switch (templateKey) {
      case 'data':
        return webhookPayloadCheatSheet;
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
              <WithPermissionControlTooltip userAction={UserActions.OutgoingWebhooksWrite}>
                <Button variant="secondary" onClick={onHide}>
                  Cancel
                </Button>
              </WithPermissionControlTooltip>
              <WithPermissionControlTooltip userAction={UserActions.OutgoingWebhooksWrite}>
                <Button variant="primary" onClick={() => handleSubmit(changedTemplateBody)}>
                  Save
                </Button>
              </WithPermissionControlTooltip>
            </HorizontalGroup>
          </HorizontalGroup>
        </div>
      }
      onClose={onHide}
      closeOnMaskClick={false}
      width="95%"
    >
      <div className={cx('container-wrapper')}>
        <div className={cx('container')}>
          <TemplatesAlertGroupsList
            heading="Last events"
            templatePage={TEMPLATE_PAGE.Webhooks}
            outgoingwebhookId={id}
            onEditPayload={onEditPayload}
            templates={
              {
                // TODO: this is just some dummy data, this will need replaced with an actual Webhook Template
                acknowledge_condition_template: null,
                acknowledge_condition_template_is_default: true,
              } as any
            }
            onLoadAlertGroupsList={(_isRecentAlertExisting: boolean) => {}}
          />

          {isCheatSheetVisible ? (
            <CheatSheet
              cheatSheetName={template.displayName}
              cheatSheetData={getCheatSheet(template.name)}
              onClose={onCloseCheatSheet}
            />
          ) : (
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
                    value={template.value}
                    data={{ payload_example: selectedPayload }}
                    showLineNumbers={true}
                    height="100%"
                    onChange={getChangeHandler()}
                    suggestionPrefix=""
                  />
                </div>
              </div>
            </>
          )}
          <TemplateResult
            templatePage={TEMPLATE_PAGE.Webhooks}
            outgoingWebhookId={id}
            template={template}
            templateBody={changedTemplateBody}
            isAlertGroupExisting={false}
            chatOpsPermalink={undefined}
            payload={selectedPayload}
            error={resultError}
            onSaveAndFollowLink={undefined}
          />
        </div>
      </div>
    </Drawer>
  );
};
