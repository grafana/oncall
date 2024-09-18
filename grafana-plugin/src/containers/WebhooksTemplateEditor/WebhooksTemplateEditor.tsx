import React, { useCallback, useState } from 'react';

import { Button, Drawer, Stack, useStyles2 } from '@grafana/ui';
import { UserActions } from 'helpers/authorization/authorization';
import { debounce } from 'lodash-es';

import { CheatSheet } from 'components/CheatSheet/CheatSheet';
import { genericTemplateCheatSheet, webhookPayloadCheatSheet } from 'components/CheatSheet/CheatSheet.config';
import { MonacoEditor } from 'components/MonacoEditor/MonacoEditor';
import { Text } from 'components/Text/Text';
import { getIntegrationTemplateStyles } from 'containers/IntegrationTemplate/IntegrationTemplate.styles';
import { TemplatePage } from 'containers/TemplatePreview/TemplatePreview';
import { TemplateResult } from 'containers/TemplateResult/TemplateResult';
import { TemplatesAlertGroupsList } from 'containers/TemplatesAlertGroupsList/TemplatesAlertGroupsList';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { ApiSchemas } from 'network/oncall-api/api.types';

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
  const styles = useStyles2(getIntegrationTemplateStyles);

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
        <div className={styles.titleContainer}>
          <Stack justifyContent="space-between" alignItems="flex-start">
            <Stack direction="column">
              <Text.Title level={3}>Edit {template.displayName} template</Text.Title>
              {template.description && <Text type="secondary">{template.description}</Text>}
            </Stack>

            <Stack>
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
            </Stack>
          </Stack>
        </div>
      }
      onClose={onHide}
      closeOnMaskClick={false}
      width="95%"
    >
      <div className={styles.containerWrapper}>
        <div className={styles.container}>
          <TemplatesAlertGroupsList
            heading="Last events"
            templatePage={TemplatePage.Webhooks}
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
              <div className={styles.templateBlockCodeEditor}>
                <div className={styles.templateEditorBlockTitle}>
                  <Stack justifyContent="space-between" alignItems="center" wrap="wrap">
                    <Text>Template editor</Text>
                    <Button variant="secondary" fill="outline" onClick={onShowCheatSheet} icon="book" size="sm">
                      Cheatsheet
                    </Button>
                  </Stack>
                </div>
                <div className={styles.templateEditorBlockContent}>
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
            templatePage={TemplatePage.Webhooks}
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
