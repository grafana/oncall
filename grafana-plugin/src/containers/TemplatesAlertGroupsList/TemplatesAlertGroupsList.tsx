import React, { useEffect, useState } from 'react';

import { Button, HorizontalGroup, Icon, IconButton, Badge, LoadingPlaceholder } from '@grafana/ui';
import cn from 'classnames/bind';
import { debounce } from 'lodash-es';

import { MonacoEditor, MONACO_LANGUAGE } from 'components/MonacoEditor/MonacoEditor';
import { MONACO_EDITABLE_CONFIG } from 'components/MonacoEditor/MonacoEditor.config';
import { Text } from 'components/Text/Text';
import { TooltipBadge } from 'components/TooltipBadge/TooltipBadge';
import { AlertTemplatesDTO } from 'models/alert_templates/alert_templates';
import { AlertGroupHelper } from 'models/alertgroup/alertgroup.helpers';
import { OutgoingWebhookResponse } from 'models/outgoing_webhook/outgoing_webhook.types';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useStore } from 'state/useStore';

import styles from './TemplatesAlertGroupsList.module.css';

const cx = cn.bind(styles);

export enum TEMPLATE_PAGE {
  Integrations,
  Webhooks,
}

interface TemplatesAlertGroupsListProps {
  templatePage: TEMPLATE_PAGE;
  templates: AlertTemplatesDTO[];
  alertReceiveChannelId?: ApiSchemas['AlertReceiveChannel']['id'];
  outgoingwebhookId?: ApiSchemas['Webhook']['id'];
  heading?: string;

  onSelectAlertGroup?: (alertGroup: ApiSchemas['AlertGroup']) => void;

  onEditPayload?: (payload: string) => void;
  onLoadAlertGroupsList?: (isRecentAlertExising: boolean) => void;
}

export const TemplatesAlertGroupsList = (props: TemplatesAlertGroupsListProps) => {
  const {
    templatePage,
    heading = 'Recent Alert groups',
    alertReceiveChannelId,
    outgoingwebhookId,
    templates,
    onEditPayload,
    onSelectAlertGroup,
    onLoadAlertGroupsList,
  } = props;
  const store = useStore();
  const [alertGroupsList, setAlertGroupsList] = useState(undefined);
  const [outgoingWebhookLastResponses, setOutgoingWebhookLastResponses] =
    useState<OutgoingWebhookResponse[]>(undefined);

  const [selectedTitle, setSelectedTitle] = useState<string>(undefined);
  const [selectedPayload, setSelectedPayload] = useState<string>(undefined);
  const [isEditMode, setIsEditMode] = useState(false);

  useEffect(() => {
    if (templatePage === TEMPLATE_PAGE.Webhooks) {
      if (outgoingwebhookId !== 'new') {
        store.outgoingWebhookStore.getLastResponses(outgoingwebhookId).then(setOutgoingWebhookLastResponses);
      }
    } else if (templatePage === TEMPLATE_PAGE.Integrations) {
      AlertGroupHelper.getAlertGroupsForIntegration(alertReceiveChannelId).then((result) => {
        setAlertGroupsList(result.slice(0, 30));
        onLoadAlertGroupsList(result.length > 0);
      });
    }
  }, []);

  const getChangeHandler = () => {
    return debounce((value: string) => {
      onEditPayload(value);
    }, 1000);
  };

  const returnToListView = () => {
    setIsEditMode(false);
    setSelectedPayload(undefined);
    onEditPayload(null);
  };

  // for Integrations

  const getAlertGroupPayload = async (id) => {
    const groupedAlert = await AlertGroupHelper.getAlertsFromGroup(id);
    const currentIncidentRawResponse = await AlertGroupHelper.getPayloadForIncident(groupedAlert?.alerts[0]?.id);
    setSelectedTitle(getAlertGroupName(groupedAlert));
    setSelectedPayload(currentIncidentRawResponse?.raw_request_data);

    // ?
    onSelectAlertGroup(groupedAlert);
    onEditPayload(JSON.stringify(currentIncidentRawResponse?.raw_request_data));
  };

  const getAlertGroupName = (alertGroup: ApiSchemas['AlertGroup']) => {
    // Integrations page
    return alertGroup.inside_organization_number
      ? `#${alertGroup.inside_organization_number} ${alertGroup.render_for_web?.title}`
      : alertGroup.render_for_web?.title;
  };

  // for Outgoing webhooks

  const handleOutgoingWebhookResponseSelect = (response: OutgoingWebhookResponse) => {
    setSelectedTitle(response.timestamp);

    setSelectedPayload(JSON.parse(response.event_data));

    onEditPayload(response.event_data);
  };

  if (selectedPayload) {
    // IF selected we either display it as ReadOnly or in EditMode
    return (
      <div className={cx('template-block-list')} id="alerts-content-container-id">
        {isEditMode ? renderSelectedPayloadInEditMode() : renderSelectedPayloadInReadOnlyMode()}
      </div>
    );
  }

  return (
    <div className={cx('template-block-list')} id="alerts-content-container-id">
      {isEditMode ? (
        <>
          <div className={cx('template-block-title-edit-mode')}>
            <HorizontalGroup justify="space-between">
              <Text>Edit custom payload</Text>

              <HorizontalGroup>
                <IconButton aria-label="List View" name="times" onClick={returnToListView} />
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
                ...MONACO_EDITABLE_CONFIG,
                readOnly: false,
              }}
              height="100%"
              onChange={getChangeHandler()}
            />
          </div>
        </>
      ) : (
        <>
          <div className={cx('template-block-title')}>
            <HorizontalGroup justify="space-between" wrap>
              <HorizontalGroup>
                <Text>{heading}</Text>
                {/* <Tooltip content="Here will be information about alert groups" placement="top">
                  <Icon name="info-circle" />
                </Tooltip> */}
              </HorizontalGroup>

              <Button variant="secondary" fill="outline" onClick={() => setIsEditMode(true)} size="sm">
                Use custom payload
              </Button>
            </HorizontalGroup>
          </div>
          <div className={cx('alert-groups-list')}>
            {templatePage === TEMPLATE_PAGE.Webhooks ? renderOutgoingWebhookLastResponses() : renderAlertGroupList()}
          </div>
        </>
      )}
    </div>
  );

  function renderOutgoingWebhookLastResponses() {
    if (outgoingwebhookId !== 'new' && !outgoingWebhookLastResponses) {
      return <LoadingPlaceholder text="Loading last events..." />;
    }

    if (outgoingWebhookLastResponses?.length) {
      return outgoingWebhookLastResponses
        .filter((response) => response.event_data)
        .map((response) => {
          return (
            <div
              key={response.timestamp}
              onClick={() => handleOutgoingWebhookResponseSelect(response)}
              className={cx('alert-groups-list-item')}
            >
              <Text type="link"> {response.timestamp}</Text>
            </div>
          );
        });
    } else {
      return (
        <Badge
          color="blue"
          text={
            <div className={cx('no-alert-groups-badge')}>
              <Icon name="info-circle" />
              <Text>
                This outgoing webhook did not receive any events. Use custom payload example to preview results.
              </Text>
            </div>
          }
        />
      );
    }
  }

  function renderAlertGroupList() {
    if (!alertGroupsList) {
      return <LoadingPlaceholder text="Loading alert groups..." />;
    }

    if (alertGroupsList.length) {
      return alertGroupsList.map((alertGroup) => {
        return (
          <div
            key={alertGroup.pk}
            onClick={() => getAlertGroupPayload(alertGroup.pk)}
            className={cx('alert-groups-list-item')}
          >
            <Text type="link"> {getAlertGroupName(alertGroup)}</Text>
          </div>
        );
      });
    } else {
      return (
        <Badge
          color="blue"
          text={
            <div className={cx('no-alert-groups-badge')}>
              <Icon name="info-circle" />
              <Text>This integration did not receive any alerts. Use custom payload example to preview results.</Text>
            </div>
          }
        />
      );
    }
  }

  function renderSelectedPayloadInEditMode() {
    return (
      <>
        <div className={cx('template-block-title-edit-mode')}>
          <HorizontalGroup justify="space-between">
            <Text>Edit custom payload</Text>

            <HorizontalGroup>
              <IconButton aria-label="List View" name="times" onClick={() => returnToListView()} />
            </HorizontalGroup>
          </HorizontalGroup>
        </div>
        <div className={cx('alert-groups-editor')}>
          <MonacoEditor
            value={JSON.stringify(selectedPayload, null, 4)}
            data={templates}
            height="100%"
            onChange={getChangeHandler()}
            showLineNumbers
            useAutoCompleteList={false}
            language={MONACO_LANGUAGE.json}
            monacoOptions={MONACO_EDITABLE_CONFIG}
          />
        </div>
      </>
    );
  }

  function renderSelectedPayloadInReadOnlyMode() {
    return (
      <>
        <div className={cx('template-block-title')}>
          <div className={cx('selected-alert-name-container')}>
            <div className={cx('selected-alert-name')}>
              <Text>{selectedTitle}</Text>
            </div>
            <div className={cx('title-action-icons')}>
              <IconButton aria-label="Edit" name="edit" onClick={() => setIsEditMode(true)} />
              <IconButton aria-label="List View" name="times" onClick={() => returnToListView()} />
            </div>
          </div>
        </div>
        <div className={cx('alert-groups-editor')}>
          <TooltipBadge
            borderType="primary"
            text="Payload"
            tooltipContent=""
            className={cx('alert-groups-last-payload-badge')}
          />
          <div className={cx('alert-groups-editor-withBadge')}>
            {/* Editor used for Editing Given Payload */}
            <MonacoEditor
              value={JSON.stringify(selectedPayload, null, 4)}
              data={undefined}
              disabled
              height="100%"
              onChange={getChangeHandler()}
              useAutoCompleteList={false}
              language={MONACO_LANGUAGE.json}
              monacoOptions={{
                ...MONACO_EDITABLE_CONFIG,
                readOnly: true,
              }}
            />
          </div>
        </div>
      </>
    );
  }
};
