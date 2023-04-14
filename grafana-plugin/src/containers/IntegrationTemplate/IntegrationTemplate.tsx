import React, { useCallback, useEffect, useState } from 'react';

import { Button, HorizontalGroup, Tooltip, Icon, Drawer, VerticalGroup, IconButton } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import { TemplateForEdit } from 'components/AlertTemplates/AlertTemplatesForm.config';
import CheatSheet from 'components/CheatSheet/CheatSheet';
import { groupingTemplateCheatSheet } from 'components/CheatSheet/CheatSheet.config';
import MonacoJinja2Editor from 'components/MonacoJinja2Editor/MonacoJinja2Editor';
import SourceCode from 'components/SourceCode/SourceCode';
import Text from 'components/Text/Text';
import TemplatePreview from 'containers/TemplatePreview/TemplatePreview';
import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { useStore } from 'state/useStore';

import styles from './IntegrationTemplate.module.css';

const cx = cn.bind(styles);

interface IntegrationTemplateProps {
  id: AlertReceiveChannel['id'];
  template: TemplateForEdit;
  onHide: () => void;
  onUpdate?: () => void;
}

const IntegrationTemplate = observer((props: IntegrationTemplateProps) => {
  const [isCheatSheetVisible, setIsCheatSheetVisible] = useState<boolean>(false);
  const { id, onHide, onUpdate, template } = props;

  const onShowCheatSheet = useCallback(() => {
    setIsCheatSheetVisible(true);
  }, []);

  const onCloseCheatSheet = useCallback(() => {
    setIsCheatSheetVisible(false);
  }, []);
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
                <Button variant="primary" onClick={onUpdate}>
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
          <AlertGroupsList alertReceiveChannelId={id} />
          {isCheatSheetVisible ? (
            <CheatSheet cheatSheetData={groupingTemplateCheatSheet} onClose={onCloseCheatSheet} />
          ) : (
            <TemplateEditor payload={template.payload} onShowCheatSheet={onShowCheatSheet} />
          )}
          <Result alertReceiveChannelId={id} template={template} />
        </div>
      </Drawer>
    </>
  );
});

interface AlertGroupsListProps {
  alertReceiveChannelId: AlertReceiveChannel['id'];
}

const AlertGroupsList = (props: AlertGroupsListProps) => {
  const { alertReceiveChannelId } = props;
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
              <MonacoJinja2Editor value={selectedAlertPayload} data={undefined} />
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
                      <Button fill="text" onClick={() => setSelectedAlertPayload(alertGroup?.render_for_web.message)}>
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

interface TemplateEditorProps {
  payload: any;
  onShowCheatSheet: () => void;
}
const TemplateEditor = (props: TemplateEditorProps) => {
  const { payload, onShowCheatSheet } = props;
  return (
    <div className={cx('template-block-codeeditor')}>
      <div className={cx('template-editor-block-title')}>
        <HorizontalGroup justify="space-between">
          <Text>Template editor</Text>

          <Button variant="secondary" fill="outline" onClick={onShowCheatSheet} icon="book" size="sm">
            Cheatsheat
          </Button>
        </HorizontalGroup>
      </div>

      <MonacoJinja2Editor value={payload} data={undefined} showLineNumbers={true} height={'1000px'} />
    </div>
  );
};

interface ResultProps {
  alertReceiveChannelId: AlertReceiveChannel['id'];
  template: TemplateForEdit;
}

const Result = (props: ResultProps) => {
  const { alertReceiveChannelId, template } = props;

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
        />
      </div>
    </div>
  );
};

export default IntegrationTemplate;
