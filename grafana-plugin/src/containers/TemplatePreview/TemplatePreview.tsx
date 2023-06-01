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

const TemplatePreview = observer((props: TemplatePreviewProps) => {
  const { templateName, templateBody, payload, alertReceiveChannelId, alertGroupId } = props;

  const [result, setResult] = useState<{ preview: string | null } | undefined>(undefined);
  const [isCondition, setIsCondition] = useState(false);
  // const [conditionalResult, setConditionalResult] = useState()

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
          setIsCondition(true);
        } else {
          setIsCondition(false);
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

  return result ? (
    <>
      {templateName.includes('condition_template') ? (
        <Text type={isCondition ? 'success' : 'danger'}>
          {isCondition ? (
            <>
              <Icon name="check" size="lg" /> True
              <Text type="secondary">{`Selected alert will ${templateName.substring(
                0,
                templateName.indexOf('_')
              )} alert group`}</Text>
            </>
          ) : (
            <VerticalGroup>
              <HorizontalGroup>
                <Icon name="times-circle" size="lg" />
                <div
                  className={cx('message')}
                  dangerouslySetInnerHTML={{
                    __html: sanitize(result.preview || ''),
                  }}
                />
              </HorizontalGroup>
              <Text type="secondary">{`Selected alert will not ${templateName.substring(
                0,
                templateName.indexOf('_')
              )} alert group`}</Text>
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
                __html: sanitize(result.preview.replace(/\n/g, '<br />') || ''),
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
