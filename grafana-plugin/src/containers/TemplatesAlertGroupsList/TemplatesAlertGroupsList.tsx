import React, { useEffect, useState } from 'react';

import { Button, Icon, IconButton, Badge, LoadingPlaceholder, Stack, useStyles2 } from '@grafana/ui';
import { debounce } from 'lodash-es';

import { MonacoEditor, MonacoLanguage } from 'components/MonacoEditor/MonacoEditor';
import { MONACO_EDITABLE_CONFIG } from 'components/MonacoEditor/MonacoEditor.config';
import { Text } from 'components/Text/Text';
import { TooltipBadge } from 'components/TooltipBadge/TooltipBadge';
import { TemplatePage } from 'containers/TemplatePreview/TemplatePreview';
import { AlertTemplatesDTO } from 'models/alert_templates/alert_templates';
import { AlertGroupHelper } from 'models/alertgroup/alertgroup.helpers';
import { OutgoingWebhookResponse } from 'models/outgoing_webhook/outgoing_webhook.types';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { useStore } from 'state/useStore';

import { getTemplatesAlertGroupsListStyles } from './TemplatesAlertGroupsList.styles';

interface TemplatesAlertGroupsListProps {
  templatePage: TemplatePage;
  templates: AlertTemplatesDTO[];
  alertReceiveChannelId?: ApiSchemas['AlertReceiveChannel']['id'];
  outgoingwebhookId?: ApiSchemas['Webhook']['id'];
  heading?: string;

  onSelectAlertGroup?: (alertGroup: ApiSchemas['AlertGroup']) => void;

  onEditPayload?: (payload: string) => void;
  onLoadAlertGroupsList?: (isRecentAlertExising: boolean) => void;
}

export const TemplatesAlertGroupsList = (props: TemplatesAlertGroupsListProps) => {
  const styles = useStyles2(getTemplatesAlertGroupsListStyles);

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
    (async () => {
      if (templatePage === TemplatePage.Webhooks) {
        if (outgoingwebhookId !== 'new') {
          const res = await store.outgoingWebhookStore.getLastResponses(outgoingwebhookId);
          setOutgoingWebhookLastResponses(res);
        }
      } else if (templatePage === TemplatePage.Integrations) {
        const result = await AlertGroupHelper.getAlertGroupsForIntegration(alertReceiveChannelId);
        setAlertGroupsList(result.slice(0, 30));
        onLoadAlertGroupsList(result.length > 0);
      }
    })();
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
      <div className={styles.templateBlockList} id="alerts-content-container-id">
        {isEditMode ? renderSelectedPayloadInEditMode() : renderSelectedPayloadInReadOnlyMode()}
      </div>
    );
  }

  return (
    <div className={styles.templateBlockList} id="alerts-content-container-id">
      {isEditMode ? (
        <>
          <div className={styles.templateBlockTitleEditMode}>
            <Stack justifyContent="space-between">
              <Text>Edit custom payload</Text>

              <Stack>
                <IconButton aria-label="List View" name="times" onClick={returnToListView} />
              </Stack>
            </Stack>
          </div>
          <div className={styles.alertGroupsEditor}>
            <MonacoEditor
              value={null}
              disabled={true}
              useAutoCompleteList={false}
              language={MonacoLanguage.json}
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
          <div className={styles.templateBlockTitle}>
            <Stack justifyContent="space-between" wrap="wrap">
              <Stack>
                <Text>{heading}</Text>
                {/* <Tooltip content="Here will be information about alert groups" placement="top">
                  <Icon name="info-circle" />
                </Tooltip> */}
              </Stack>

              <Button variant="secondary" fill="outline" onClick={() => setIsEditMode(true)} size="sm">
                Use custom payload
              </Button>
            </Stack>
          </div>
          <div className={styles.alertGroupsList}>
            {templatePage === TemplatePage.Webhooks ? renderOutgoingWebhookLastResponses() : renderAlertGroupList()}
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
              className={styles.alertGroupsListItem}
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
            <div className={styles.noAlertGroupsBadge}>
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
            className={styles.alertGroupsListItem}
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
            <div className={styles.noAlertGroupsBadge}>
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
        <div className={styles.templateBlockTitleEditMode}>
          <Stack justifyContent="space-between">
            <Text>Edit custom payload</Text>

            <Stack>
              <IconButton aria-label="List View" name="times" onClick={() => returnToListView()} />
            </Stack>
          </Stack>
        </div>
        <div className={styles.alertGroupsEditor}>
          <MonacoEditor
            value={JSON.stringify(selectedPayload, null, 4)}
            data={templates}
            height="100%"
            onChange={getChangeHandler()}
            showLineNumbers
            useAutoCompleteList={false}
            language={MonacoLanguage.json}
            monacoOptions={MONACO_EDITABLE_CONFIG}
          />
        </div>
      </>
    );
  }

  function renderSelectedPayloadInReadOnlyMode() {
    return (
      <>
        <div className={styles.templateBlockTitle}>
          <div className={styles.selectedAlertNameContainer}>
            <div className={styles.selectedAlertName}>
              <Text>{selectedTitle}</Text>
            </div>
            <div className={styles.titleActionIcons}>
              <IconButton aria-label="Edit" name="edit" onClick={() => setIsEditMode(true)} />
              <IconButton aria-label="List View" name="times" onClick={() => returnToListView()} />
            </div>
          </div>
        </div>
        <div className={styles.alertGroupsEditor}>
          <TooltipBadge
            borderType="primary"
            text="Payload"
            tooltipContent=""
            className={styles.alertGroupsLastPayloadBadge}
          />
          <div className={styles.alertGroupsEditorWithBadge}>
            {/* Editor used for Editing Given Payload */}
            <MonacoEditor
              value={JSON.stringify(selectedPayload, null, 4)}
              data={undefined}
              disabled
              height="100%"
              onChange={getChangeHandler()}
              useAutoCompleteList={false}
              language={MonacoLanguage.json}
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
