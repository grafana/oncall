import React, { useEffect, useState } from 'react';

import { HorizontalGroup, Icon, LoadingPlaceholder, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import Text from 'components/Text/Text';
import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { Alert } from 'models/alertgroup/alertgroup.types';
import { OutgoingWebhook } from 'models/outgoing_webhook/outgoing_webhook.types';
import { useStore } from 'state/useStore';
import { openErrorNotification } from 'utils';
import { useDebouncedCallback } from 'utils/hooks';
import sanitize from 'utils/sanitize';

import styles from './TemplatePreview.module.css';

const cx = cn.bind(styles);

interface TemplatePreviewProps {
  templateName: string;
  templateBody: string | null;
  templateType?: 'plain' | 'html' | 'image' | 'boolean';
  templateIsRoute?: boolean;
  payload?: JSON;
  alertReceiveChannelId: AlertReceiveChannel['id'];
  alertGroupId?: Alert['pk'];
  outgoingWebhookId?: OutgoingWebhook['id'];
  templatePage: TEMPLATE_PAGE;
}
interface ConditionalResult {
  isResult?: boolean;
  value?: string;
}

export enum TEMPLATE_PAGE {
  Integrations,
  Webhooks,
}

const TemplatePreview = observer((props: TemplatePreviewProps) => {
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

  const [result, setResult] = useState<{ preview: string | null } | undefined>(undefined);
  const [conditionalResult, setConditionalResult] = useState<ConditionalResult>({});

  const store = useStore();
  const { alertReceiveChannelStore, alertGroupStore, outgoingWebhookStore } = store;

  const handleTemplateBodyChange = useDebouncedCallback(() => {
    (templatePage === TEMPLATE_PAGE.Webhooks
      ? outgoingWebhookStore.renderPreview(outgoingWebhookId, templateName, templateBody, payload)
      : alertGroupId
      ? alertGroupStore.renderPreview(alertGroupId, templateName, templateBody)
      : alertReceiveChannelStore.renderPreview(alertReceiveChannelId, templateName, templateBody, payload)
    )
      .then((data) => {
        setResult(data);
        if (data?.preview === 'True') {
          setConditionalResult({ isResult: true, value: 'True' });
        } else if (templateType === 'boolean') {
          setConditionalResult({ isResult: true, value: 'False' });
        } else {
          setConditionalResult({ isResult: false, value: undefined });
        }
      })
      .catch((err) => {
        if (err.response?.data?.length > 0) {
          openErrorNotification(err.response.data);
        } else {
          openErrorNotification(err.message);
        }
      });
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
          <VerticalGroup>
            <HorizontalGroup>
              <Icon name="check" size="lg" /> {conditionalResult.value}
            </HorizontalGroup>
            {conditionalMessage(conditionalResult.value === 'True')}
          </VerticalGroup>
        ) : (
          <VerticalGroup>
            <HorizontalGroup>
              <Icon name="times-circle" size="lg" />
              <div
                className={cx('message')}
                dangerouslySetInnerHTML={{
                  __html: sanitize(result.preview),
                }}
              />
            </HorizontalGroup>
            {conditionalMessage(conditionalResult.value === 'True')}
          </VerticalGroup>
        )}
      </Text>
    );
  }
  function renderHtmlResult() {
    return (
      <div
        className={cx('message')}
        dangerouslySetInnerHTML={{
          __html: sanitize(result.preview),
        }}
      />
    );
  }
  function renderPlainResult() {
    return (
      <div
        className={cx('message', 'display-linebreak')}
        dangerouslySetInnerHTML={{
          __html: sanitize(result.preview),
        }}
      />
    );
  }
  function renderImageResult() {
    return (
      <div className={cx('image-result')}>
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

  return result ? <>{renderResult()}</> : <LoadingPlaceholder text="Loading..." />;
});

export default TemplatePreview;
