import React, { useEffect, useState } from 'react';

import { Button, HorizontalGroup, Tooltip, Icon, VerticalGroup, IconButton, Badge } from '@grafana/ui';
import cn from 'classnames/bind';
import { debounce } from 'lodash-es';

import MonacoJinja2Editor from 'components/MonacoJinja2Editor/MonacoJinja2Editor';
import SourceCode from 'components/SourceCode/SourceCode';
import Text from 'components/Text/Text';
import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { Alert } from 'models/alertgroup/alertgroup.types';
import { useStore } from 'state/useStore';

import styles from './TemplatesAlertGroupsList.module.css';

const cx = cn.bind(styles);

interface TemplatesAlertGroupsListProps {
  alertReceiveChannelId: AlertReceiveChannel['id'];
  onSelectAlertGroup?: (alertGroup: Alert) => void;
  onEditPayload?: (payload: string) => void;
}

const TemplatesAlertGroupsList = (props: TemplatesAlertGroupsListProps) => {
  const { alertReceiveChannelId, onEditPayload, onSelectAlertGroup } = props;
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
    <div className={cx('template-block-list')}>
      {selectedAlertPayload ? (
        <>
          {isEditMode ? (
            <>
              <div className={cx('template-block-title')}>
                <HorizontalGroup justify="space-between">
                  <Text>Edit {selectedAlertName}</Text>

                  <HorizontalGroup>
                    <IconButton name="times" onClick={() => returnToListView()} />
                  </HorizontalGroup>
                </HorizontalGroup>
              </div>
              <div className={cx('alert-groups-list')}>
                <MonacoJinja2Editor
                  value={JSON.stringify(selectedAlertPayload, null, 4)}
                  data={undefined}
                  height={'85vh'}
                  onChange={getChangeHandler()}
                  showLineNumbers
                />
              </div>
            </>
          ) : (
            <>
              <div className={cx('template-block-title')}>
                <HorizontalGroup justify="space-between">
                  <Text>{selectedAlertName}</Text>

                  <HorizontalGroup>
                    <IconButton name="edit" onClick={() => setIsEditMode(true)} />
                    <IconButton name="times" onClick={() => returnToListView()} />
                  </HorizontalGroup>
                </HorizontalGroup>
              </div>
              <div className={cx('alert-groups-list')}>
                <VerticalGroup>
                  <Badge color="blue" text="Last alert payload" />
                  <SourceCode className={cx('alert-group-payload-view')} noMaxHeight showClipboardIconOnly>
                    {JSON.stringify(selectedAlertPayload, null, 4)}
                  </SourceCode>
                </VerticalGroup>
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
              <div className={cx('alert-groups-list')}>
                <MonacoJinja2Editor
                  value={null}
                  data={undefined}
                  height={'85vh'}
                  onChange={getChangeHandler()}
                  showLineNumbers
                />
              </div>
            </>
          ) : (
            <>
              <div className={cx('template-block-title')}>
                <HorizontalGroup justify="space-between" wrap>
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
                {alertGroupsList?.length > 0 ? (
                  <>
                    {alertGroupsList.map((alertGroup) => {
                      return (
                        <div key={alertGroup.pk}>
                          <Button fill="text" onClick={() => getAlertGroupPayload(alertGroup.pk)}>
                            {getAlertGroupName(alertGroup)}
                          </Button>
                        </div>
                      );
                    })}
                  </>
                ) : (
                  <Badge
                    color="blue"
                    text={
                      <HorizontalGroup>
                        <Icon name="info-circle" />
                        <Text>
                          This integration did not receive any alerts. Use custom payload example to preview results.
                        </Text>
                      </HorizontalGroup>
                    }
                  />
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
