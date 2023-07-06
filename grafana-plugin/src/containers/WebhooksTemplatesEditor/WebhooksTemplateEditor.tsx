import { Button, Drawer, HorizontalGroup, VerticalGroup } from '@grafana/ui';
import Text from 'components/Text/Text';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import React, { useState } from 'react';
import { UserActions } from 'utils/authorization';
import cn from 'classnames/bind';

import styles from 'containers/IntegrationTemplate/IntegrationTemplate.module.scss';
import CheatSheet from 'components/CheatSheet/CheatSheet';
import MonacoEditor from 'components/MonacoEditor/MonacoEditor';
import { noop } from 'lodash-es';
import TemplatesAlertGroupsList, { TEMPLATE_PAGE } from 'containers/TemplatesAlertGroupsList/TemplatesAlertGroupsList';
import { Alert } from 'models/alertgroup/alertgroup.types';

const cx = cn.bind(styles);

interface WebhooksTemplateEditorProps {
  template: any;
  onHide: () => void;
  handleSubmit: () => void;
}

const WebhooksTemplateEditor: React.FC<WebhooksTemplateEditorProps> = ({ template, onHide, handleSubmit }) => {
  const [isCheatSheetVisible] = useState(false);

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
            templatePage={TEMPLATE_PAGE.Webhooks}
            onEditPayload={(_payload: string) => {}}
            onSelectAlertGroup={(_alertGroup: Alert) => {}}
            templates={
              {
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
                  <MonacoEditor value={''} data={undefined} showLineNumbers={true} height={`400px`} onChange={noop} />
                </div>
              </div>
            </>
          )}

          {/* <Result
            alertReceiveChannelId={id}
            template={template}
            templateBody={changedTemplateBody}
            isAlertGroupExisting={isRecentAlertGroupExisting}
            chatOpsPermalink={chatOpsPermalink}
            payload={alertGroupPayload}
            error={resultError}
            onSaveAndFollowLink={onSaveAndFollowLink}
          /> */}
        </div>
      </div>
    </Drawer>
  );

  function onShowCheatSheet() {}

  function onCloseCheatSheet() {}

  function getCheatSheet(_templateName: string) {
    return undefined;
  }
};

export default WebhooksTemplateEditor;
