import React, { useEffect, useState } from 'react';

import { HorizontalGroup, Icon, LoadingPlaceholder, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import Text from 'components/Text/Text';
import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { Alert } from 'models/alertgroup/alertgroup.types';
import { useStore } from 'state/useStore';
import { openErrorNotification } from 'utils';
import { useDebouncedCallback } from 'utils/hooks';
import sanitize from 'utils/sanitize';

import styles from './TemplatePreview.module.css';

const cx = cn.bind(styles);

interface TemplatePreviewProps {
  templateName: string;
  templateBody: string | null;
  payload?: JSON;
  alertReceiveChannelId: AlertReceiveChannel['id'];
  onEditClick?: () => void;
  alertGroupId?: Alert['pk'];
  active?: boolean;
  onResult?: (result) => void;
}
interface ConditionalResult {
  isResult?: boolean;
  value?: string;
}

const TemplatePreview = observer((props: TemplatePreviewProps) => {
  const { templateName, templateBody, payload, alertReceiveChannelId, alertGroupId } = props;

  const [result, setResult] = useState<{ preview: string | null } | undefined>(undefined);
  const [conditionalResult, setConditionalResult] = useState<ConditionalResult>({});

  const store = useStore();
  const { alertReceiveChannelStore, alertGroupStore } = store;

  const handleTemplateBodyChange = useDebouncedCallback(() => {
    (alertGroupId
      ? alertGroupStore.renderPreview(alertGroupId, templateName, templateBody)
      : alertReceiveChannelStore.renderPreview(alertReceiveChannelId, templateName, templateBody, payload)
    )
      .then((data) => {
        setResult(data);
        if (data?.preview === 'True') {
          setConditionalResult({ isResult: true, value: 'True' });
        } else if (data?.preview.includes('False')) {
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
    if (templateName.includes('route')) {
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

  return result ? (
    <>
      {conditionalResult?.isResult ? (
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
                    __html: sanitize(result.preview?.substring(0, 5) || ''),
                  }}
                />
              </HorizontalGroup>
              <div
                className={cx('message')}
                dangerouslySetInnerHTML={{
                  __html: sanitize(result.preview?.substring(5, result.preview?.length) || ''),
                }}
              />
              {conditionalMessage(conditionalResult.value === 'True')}
            </VerticalGroup>
          )}
        </Text>
      ) : (
        <>
          {templateName.includes('image') ? (
            <div className={cx('image-result')}>
              <img src={result.preview} />
            </div>
          ) : (
            <div
              className={cx('message')}
              dangerouslySetInnerHTML={{
                __html: sanitize(result.preview?.replace(/\n/g, '<br />') || ''),
              }}
            />
          )}
        </>
      )}
    </>
  ) : (
    <LoadingPlaceholder text="Loading..." />
  );
});

export default TemplatePreview;
