import React, { useEffect, useState } from 'react';

import { Button, HorizontalGroup, Tooltip, Icon, IconButton, Badge, LoadingPlaceholder } from '@grafana/ui';
import cn from 'classnames/bind';
import { debounce } from 'lodash-es';

import MonacoEditor, { MONACO_LANGUAGE } from 'components/MonacoEditor/MonacoEditor';
import Text from 'components/Text/Text';
import TooltipBadge from 'components/TooltipBadge/TooltipBadge';
import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { AlertTemplatesDTO } from 'models/alert_templates';
import { Alert } from 'models/alertgroup/alertgroup.types';
import { MONACO_OPTIONS, MONACO_PAYLOAD_OPTIONS } from 'pages/integration_2/Integration2.config';
import { useStore } from 'state/useStore';

import styles from './TemplatesAlertGroupsList.module.css';

const cx = cn.bind(styles);
const HEADER_OF_CONTAINER_HEIGHT = 59;
const BADGE_WITH_PADDINGS_HEIGHT = 42;

interface TemplatesAlertGroupsListProps {
  templates: AlertTemplatesDTO[];
  alertReceiveChannelId: AlertReceiveChannel['id'];
  onSelectAlertGroup?: (alertGroup: Alert) => void;
  onEditPayload?: (payload: string) => void;
}

const TemplatesAlertGroupsList = (props: TemplatesAlertGroupsListProps) => {
  const { alertReceiveChannelId, templates, onEditPayload, onSelectAlertGroup } = props;
  const store = useStore();
  const [alertGroupsList, setAlertGroupsList] = useState(undefined);
  const [selectedAlertPayload, setSelectedAlertPayload] = useState<string>(undefined);
  const [selectedAlertName, setSelectedAlertName] = useState<string>(undefined);
  const [isEditMode, setIsEditMode] = useState(false);

  useEffect(() => {
    store.alertGroupStore
      .getAlertGroupsForIntegration(alertReceiveChannelId)
      .then((result) => setAlertGroupsList(result.slice(0, 30)));
  }, []);

  const getCodeEditorHeight = () => {
    const mainDiv = document.getElementById('alerts-content-container-id');
    const height = mainDiv?.getBoundingClientRect().height - HEADER_OF_CONTAINER_HEIGHT;
    return `${height}px`;
  };

  const getCodeEditorHeightWithBadge = () => {
    const mainDiv = document.getElementById('alerts-content-container-id');
    const height = mainDiv?.getBoundingClientRect().height - HEADER_OF_CONTAINER_HEIGHT - BADGE_WITH_PADDINGS_HEIGHT;
    return `${height}px`;
  };

  const getChangeHandler = () => {
    return debounce((value: string) => {
      onEditPayload(value);
    }, 1000);
  };

  const returnToListView = () => {
    setIsEditMode(false);
    setSelectedAlertPayload(undefined);
    onEditPayload(null);
  };

  const getAlertGroupPayload = async (id) => {
    const groupedAlert = await store.alertGroupStore.getAlertsFromGroup(id);
    const currentIncidentRawResponse = await store.alertGroupStore.getPayloadForIncident(groupedAlert?.alerts[0]?.id);
    setSelectedAlertName(getAlertGroupName(groupedAlert));
    setSelectedAlertPayload(currentIncidentRawResponse?.raw_request_data);
    onSelectAlertGroup(groupedAlert);
    onEditPayload(JSON.stringify(currentIncidentRawResponse?.raw_request_data));
  };

  const getAlertGroupName = (alertGroup: Alert) => {
    return alertGroup.inside_organization_number
      ? `#${alertGroup.inside_organization_number} ${alertGroup.render_for_web.title}`
      : alertGroup.render_for_web.title;
  };

  return (
    <div className={cx('template-block-list')} id="alerts-content-container-id">
      {selectedAlertPayload ? (
        <>
          {isEditMode ? (
            <>
              <div className={cx('template-block-title')}>
                <HorizontalGroup justify="space-between">
                  <Text>Edit custom payload</Text>

                  <HorizontalGroup>
                    <IconButton name="times" onClick={() => returnToListView()} />
                  </HorizontalGroup>
                </HorizontalGroup>
              </div>
              <div className={cx('alert-groups-editor')}>
                <MonacoEditor
                  value={JSON.stringify(selectedAlertPayload, null, 4)}
                  data={templates}
                  height={getCodeEditorHeight()}
                  onChange={getChangeHandler()}
                  showLineNumbers
                  useAutoCompleteList={false}
                  language={MONACO_LANGUAGE.json}
                  monacoOptions={MONACO_PAYLOAD_OPTIONS}
                />
              </div>
            </>
          ) : (
            <>
              <div className={cx('template-block-title')}>
                <div className={cx('selected-alert-name-container')}>
                  <div className={cx('selected-alert-name')}>
                    <Text>{selectedAlertName}</Text>
                  </div>
                  <div className={cx('title-action-icons')}>
                    <IconButton name="edit" onClick={() => setIsEditMode(true)} />
                    <IconButton name="times" onClick={() => returnToListView()} />
                  </div>
                </div>
              </div>
              <div className={cx('alert-groups-editor')}>
                <TooltipBadge
                  borderType="primary"
                  text="Last alert payload"
                  tooltipTitle=""
                  tooltipContent=""
                  className={cx('alert-groups-last-payload-badge')}
                />
                <div className={cx('alert-groups-editor-withBadge')}>
                  {/* Editor used for Editing Given Payload */}
                  <MonacoEditor
                    value={JSON.stringify(selectedAlertPayload, null, 4)}
                    data={undefined}
                    disabled
                    height={getCodeEditorHeightWithBadge()}
                    onChange={getChangeHandler()}
                    useAutoCompleteList={false}
                    language={MONACO_LANGUAGE.json}
                    monacoOptions={{
                      ...MONACO_PAYLOAD_OPTIONS,
                      readOnly: true,
                    }}
                  />
                </div>
              </div>
            </>
          )}
        </>
      ) : (
        <>
          {isEditMode ? (
            <>
              <div className={cx('template-block-title')}>
                <HorizontalGroup justify="space-between">
                  <Text>Edit custom payload</Text>

                  <HorizontalGroup>
                    <IconButton name="times" onClick={() => returnToListView()} />
                  </HorizontalGroup>
                </HorizontalGroup>
              </div>
              <div className={cx('alert-groups-editor')}>
                <MonacoEditor
                  value={null}
                  disabled={true}
                  useAutoCompleteList={false}
                  language={MONACO_LANGUAGE.json}
                  data={templates}
                  monacoOptions={{
                    ...MONACO_OPTIONS,
                    readOnly: false,
                  }}
                  showLineNumbers={false}
                  height={getCodeEditorHeight()}
                  onChange={getChangeHandler()}
                />
              </div>
            </>
          ) : (
            <>
              <div className={cx('template-block-title')}>
                <HorizontalGroup justify="space-between" wrap>
                  <HorizontalGroup>
                    <Text>Recent Alert groups</Text>
                    <Tooltip content="Here will be information about alert groups" placement="top">
                      <Icon name="info-circle" />
                    </Tooltip>
                  </HorizontalGroup>

                  <Button variant="secondary" fill="outline" onClick={() => setIsEditMode(true)} size="sm">
                    Use custom payload
                  </Button>
                </HorizontalGroup>
              </div>
              <div className={cx('alert-groups-list')}>
                {alertGroupsList ? (
                  <>
                    {alertGroupsList?.length > 0 ? (
                      <>
                        {alertGroupsList.map((alertGroup) => {
                          return (
                            <div
                              key={alertGroup.pk}
                              onClick={() => getAlertGroupPayload(alertGroup.pk)}
                              className={cx('alert-groups-list-item')}
                            >
                              <Text type="link"> {getAlertGroupName(alertGroup)}</Text>
                            </div>
                          );
                        })}
                      </>
                    ) : (
                      <Badge
                        color="blue"
                        text={
                          <div className={cx('no-alert-groups-badge')}>
                            <Icon name="info-circle" />
                            <Text>
                              This integration did not receive any alerts. Use custom payload example to preview
                              results.
                            </Text>
                          </div>
                        }
                      />
                    )}
                  </>
                ) : (
                  <LoadingPlaceholder text="Loading alert groups..." />
                )}
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
};

export default TemplatesAlertGroupsList;
