import React, { useEffect, useState } from 'react';

import { LoadingPlaceholder } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { Alert } from 'models/alertgroup/alertgroup.types';
import { useStore } from 'state/useStore';
import { useDebouncedCallback } from 'utils/hooks';
import sanitize from 'utils/sanitize';

import styles from './TemplatePreview.module.css';

const cx = cn.bind(styles);

interface TemplatePreviewProps {
  templateName: string;
  templateBody: string | null;
  alertReceiveChannelId: AlertReceiveChannel['id'];
  onEditClick: () => void;
  alertGroupId?: Alert['pk'];
  active?: boolean;
}

const TemplatePreview = observer(
  ({ templateName, templateBody, alertReceiveChannelId, alertGroupId }: TemplatePreviewProps) => {
    const [result, setResult] = useState<{ preview: string | null } | undefined>(undefined);
    const { alertReceiveChannelStore, alertGroupStore } = useStore();

    const handleTemplateBodyChange = useDebouncedCallback(() => {
      (alertGroupId
        ? alertGroupStore.renderPreview(alertGroupId, templateName, templateBody)
        : alertReceiveChannelStore.renderPreview(alertReceiveChannelId, templateName, templateBody)
      ).then(setResult);
    }, 1000);

    useEffect(handleTemplateBodyChange, [templateBody]);

    return result ? (
      <div
        className={cx('message')}
        dangerouslySetInnerHTML={{
          __html: sanitize(result.preview || ''),
        }}
      />
    ) : (
      <LoadingPlaceholder text="Loading..." />
    );
  }
);

export default TemplatePreview;
