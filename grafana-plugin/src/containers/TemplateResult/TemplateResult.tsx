import React from 'react';
import { TemplateForEdit } from 'components/AlertTemplates/CommonAlertTemplatesForm.config';
import Block from 'components/GBlock/Block';
import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { Button, HorizontalGroup, Icon, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';

import styles from 'containers/IntegrationTemplate/IntegrationTemplate.module.scss';
import Text from 'components/Text/Text';
import TemplatePreview from 'containers/TemplatePreview/TemplatePreview';

const cx = cn.bind(styles);

interface ResultProps {
  alertReceiveChannelId?: AlertReceiveChannel['id'];
  templateBody: string;
  template: TemplateForEdit;
  isAlertGroupExisting?: boolean;
  chatOpsPermalink?: string;
  payload?: JSON;
  error?: string;
  onSaveAndFollowLink?: (link: string) => void;
  templateIsRoute?: boolean;
}

const TemplateResult = (props: ResultProps) => {
  const {
    alertReceiveChannelId,
    template,
    templateBody,
    chatOpsPermalink,
    payload,
    error,
    isAlertGroupExisting,
    onSaveAndFollowLink,
  } = props;

  return (
    <div className={cx('template-block-result')}>
      <div className={cx('template-block-title')}>
        <HorizontalGroup justify="space-between">
          <Text>Result</Text>
        </HorizontalGroup>
      </div>
      <div className={cx('result')}>
        {payload || error ? (
          <VerticalGroup spacing="lg">
            {error ? (
              <Block bordered fullWidth withBackground>
                <Text>{error}</Text>
              </Block>
            ) : (
              <Block bordered fullWidth withBackground>
                <TemplatePreview
                  key={template.name}
                  templateName={template.name}
                  templateBody={templateBody}
                  templateType={template.type}
                  templateIsRoute={template.isRoute}
                  alertReceiveChannelId={alertReceiveChannelId}
                  payload={payload}
                />
              </Block>
            )}

            {template?.additionalData?.additionalDescription && (
              <Text type="secondary">{template?.additionalData.additionalDescription}</Text>
            )}

            {template?.additionalData?.chatOpsName && isAlertGroupExisting && (
              <VerticalGroup>
                <Button onClick={() => onSaveAndFollowLink(chatOpsPermalink)}>
                  <HorizontalGroup spacing="xs" align="center">
                    Save and open Alert Group in {template.additionalData.chatOpsDisplayName}{' '}
                    <Icon name="external-link-alt" />
                  </HorizontalGroup>
                </Button>

                {template.additionalData.data && <Text type="secondary">{template.additionalData.data}</Text>}
              </VerticalGroup>
            )}
          </VerticalGroup>
        ) : (
          <div>
            <Block bordered fullWidth className={cx('block-style')} withBackground>
              <Text>← Select alert group or "Use custom payload"</Text>
            </Block>
          </div>
        )}
      </div>
    </div>
  );
};

export default TemplateResult;
