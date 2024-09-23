import React, { useEffect, useState } from 'react';

import { cx } from '@emotion/css';
import { Badge, Icon, LoadingPlaceholder, Stack, useStyles2 } from '@grafana/ui';
import { openErrorNotification } from 'helpers/helpers';
import { useDebouncedCallback } from 'helpers/hooks';
import { sanitize } from 'helpers/sanitize';
import { observer } from 'mobx-react';

import { Text } from 'components/Text/Text';
import { AlertReceiveChannelHelper } from 'models/alert_receive_channel/alert_receive_channel.helpers';
import { AlertGroupHelper } from 'models/alertgroup/alertgroup.helpers';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { LabelTemplateOptions } from 'pages/integration/IntegrationCommon.config';
import { useStore } from 'state/useStore';

import { getTemplatePreviewStyles } from './TemplatePreview.styles';

interface TemplatePreviewProps {
  templateName: string;
  templateBody: string | null;
  templateType?: 'plain' | 'html' | 'image' | 'boolean';
  templateIsRoute?: boolean;
  payload?: { [key: string]: unknown };
  alertReceiveChannelId: ApiSchemas['AlertReceiveChannel']['id'];
  alertGroupId?: ApiSchemas['AlertGroup']['pk'];
  outgoingWebhookId?: ApiSchemas['Webhook']['id'];
  templatePage: TemplatePage;
}
interface ConditionalResult {
  isResult?: boolean;
  value?: string;
}

export enum TemplatePage {
  Integrations,
  Webhooks,
}

export const TemplatePreview = observer((props: TemplatePreviewProps) => {
  const {
    templateName,
    templateBody,
    templateType,
    payload,
    alertReceiveChannelId,
    outgoingWebhookId,
    alertGroupId,
    templateIsRoute,
    templatePage,
  } = props;

  const styles = useStyles2(getTemplatePreviewStyles);

  const [result, setResult] = useState<
    ApiSchemas['WebhookPreviewTemplateResponse'] & { is_valid_json_object?: boolean }
  >(undefined);
  const [conditionalResult, setConditionalResult] = useState<ConditionalResult>({});

  const store = useStore();
  const { outgoingWebhookStore } = store;

  const handleTemplateBodyChange = useDebouncedCallback(async () => {
    try {
      let data: ApiSchemas['WebhookPreviewTemplateResponse'] & { is_valid_json_object?: boolean } = undefined;

      if (templatePage === TemplatePage.Webhooks) {
        data = await outgoingWebhookStore.renderPreview(outgoingWebhookId, templateName, templateBody, payload);
      } else if (alertGroupId) {
        data = await AlertGroupHelper.renderPreview(alertGroupId, templateName, templateBody);
      } else {
        data = await AlertReceiveChannelHelper.renderPreview(
          alertReceiveChannelId,
          templateName,
          templateBody,
          payload
        );
      }

      setResult(data);

      if (data?.preview === 'True') {
        setConditionalResult({ isResult: true, value: 'True' });
      } else if (templateType === 'boolean') {
        setConditionalResult({ isResult: true, value: 'False' });
      } else {
        setConditionalResult({ isResult: false, value: undefined });
      }
    } catch (err) {
      if (err.response?.data?.length > 0) {
        openErrorNotification(err.response.data);
      } else {
        openErrorNotification(err.message);
      }
    }
  }, 1000);

  useEffect(handleTemplateBodyChange, [templateBody, payload]);

  const conditionalMessage = (success: boolean) => {
    if (templateIsRoute) {
      return (
        <Text type="secondary">
          Selected alert will {!success && <Text type="secondary">not</Text>} be matched with this route
        </Text>
      );
    } else {
      return (
        <Text type="secondary">
          Selected alert will {!success && <Text type="secondary">not</Text>}{' '}
          {`${templateName.substring(0, templateName.indexOf('_'))} alert group`}
        </Text>
      );
    }
  };

  function renderExtraChecks() {
    function getExtraCheckResult() {
      switch (templateName) {
        case LabelTemplateOptions.AlertGroupMultiLabel.key:
          return result.is_valid_json_object ? (
            <Badge color="green" icon="check" text="Output is a valid labels dictionary" />
          ) : (
            <Badge
              color="red"
              icon="times"
              text="Output is not a labels dictionary. Template should produce valid JSON object. Consider using tojson filter."
            />
          );
        default:
          return null;
      }
    }

    const checkResult = getExtraCheckResult();

    return checkResult ? <div className={styles.extraCheck}>{checkResult}</div> : null;
  }

  function renderResult() {
    switch (templateType) {
      case 'html': {
        return renderHtmlResult();
      }
      case 'image': {
        return renderImageResult();
      }
      case 'boolean': {
        return renderBooleanResult();
      }
      case 'plain': {
        return renderPlainResult();
      }
      default: {
        return renderPlainResult();
      }
    }
  }
  function renderBooleanResult() {
    return (
      <Text type={conditionalResult.value === 'True' ? 'success' : 'danger'}>
        {conditionalResult.value === 'True' ? (
          <Stack direction="column">
            <Stack>
              <Icon name="check" size="lg" /> {conditionalResult.value}
            </Stack>
            {conditionalMessage(conditionalResult.value === 'True')}
          </Stack>
        ) : (
          <Stack direction="column">
            <Stack>
              <Icon name="times-circle" size="lg" />
              <div
                className={styles.message}
                dangerouslySetInnerHTML={{
                  __html: sanitize(result.preview),
                }}
              />
            </Stack>
            {conditionalMessage(conditionalResult.value === 'True')}
          </Stack>
        )}
      </Text>
    );
  }

  function renderHtmlResult() {
    return (
      <div
        className={styles.message}
        dangerouslySetInnerHTML={{
          __html: sanitize(result.preview),
        }}
      />
    );
  }

  function renderPlainResult() {
    return (
      <div
        className={cx(styles.message, styles.displayLinebreak)}
        dangerouslySetInnerHTML={{
          __html: sanitize(result.preview),
        }}
      />
    );
  }

  function renderImageResult() {
    return (
      <div className={styles.imageResult}>
        <img
          src={result.preview}
          onError={(e) => {
            const target = e.target as HTMLImageElement;
            target.alt = result.preview || 'No image found';
          }}
        />
      </div>
    );
  }

  return result ? (
    <>
      {renderExtraChecks()}
      {renderResult()}
    </>
  ) : (
    <LoadingPlaceholder text="Loading..." />
  );
});
