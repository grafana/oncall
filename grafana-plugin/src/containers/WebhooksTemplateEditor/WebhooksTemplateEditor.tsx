import { Button, Drawer, HorizontalGroup, VerticalGroup } from '@grafana/ui';
import Text from 'components/Text/Text';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import React, { useEffect, useState } from 'react';
import { UserActions } from 'utils/authorization';
import cn from 'classnames/bind';

import styles from 'containers/IntegrationTemplate/IntegrationTemplate.module.scss';
import CheatSheet from 'components/CheatSheet/CheatSheet';
import MonacoEditor from 'components/MonacoEditor/MonacoEditor';
import { noop } from 'lodash-es';
import TemplatesAlertGroupsList, { TEMPLATE_PAGE } from 'containers/TemplatesAlertGroupsList/TemplatesAlertGroupsList';
import TemplateResult from 'containers/TemplateResult/TemplateResult';
import { waitForElement } from 'utils/DOM';

const cx = cn.bind(styles);

interface Template {
  value: string;
  displayName: string;
  description: string;
  name: undefined;
}

interface WebhooksTemplateEditorProps {
  template: Template;
  onHide: () => void;
  handleSubmit: () => void;
}

const WebhooksTemplateEditor: React.FC<WebhooksTemplateEditorProps> = ({ template, onHide, handleSubmit }) => {
  const [isCheatSheetVisible] = useState(false);
  const [editorHeight, setEditorHeight] = useState<string>(undefined);
  const [selectedAG, setSelectedAG] = useState(undefined);

  useEffect(() => {
    waitForElement('#content-container-id').then(() => {
      const mainDiv = document.getElementById('content-container-id');
      const height = mainDiv?.getBoundingClientRect().height - 59;
      setEditorHeight(`${height}px`);
    });
  }, []);

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
            heading="Alert groups"
            templatePage={TEMPLATE_PAGE.Webhooks}
            onEditPayload={(_payload: string) => {}} // TODO: add handler
            onSelectAlertGroup={setSelectedAG}
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
                  <MonacoEditor
                    value={template.value}
                    data={undefined}
                    showLineNumbers={true}
                    height={editorHeight}
                    onChange={noop}
                  />
                </div>
              </div>
            </>
          )}

          <TemplateResult
            templateBody={template.value}
            isAlertGroupExisting={true}
            chatOpsPermalink={undefined}
            payload={selectedAG}
            error={undefined}
            // this most likely is not needed for webhooks
            onSaveAndFollowLink={noop}
            template={{} as any} // todo: figure out a template config object?
          />
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
