import React from 'react';

import { Button, HorizontalGroup, Icon, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';

import { TemplateForEdit } from 'components/AlertTemplates/CommonAlertTemplatesForm.config';
import Block from 'components/GBlock/Block';
import Text from 'components/Text/Text';
import styles from 'containers/IntegrationTemplate/IntegrationTemplate.module.scss';
import TemplatePreview, { TEMPLATE_PAGE } from 'containers/TemplatePreview/TemplatePreview';
import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { OutgoingWebhook } from 'models/outgoing_webhook/outgoing_webhook.types';

const cx = cn.bind(styles);

interface ResultProps {
  alertReceiveChannelId?: AlertReceiveChannel['id'];
  outgoingWebhookId?: OutgoingWebhook['id'];
  templateBody: string;
  template: TemplateForEdit;
  isAlertGroupExisting?: boolean;
  chatOpsPermalink?: string;
  payload?: JSON;
  error?: string;
  onSaveAndFollowLink?: (link: string) => void;
  templateIsRoute?: boolean;
  templatePage?: TEMPLATE_PAGE;
}

const TemplateResult = (props: ResultProps) => {
  const {
    alertReceiveChannelId,
    outgoingWebhookId,
    template,
    templateBody,
    chatOpsPermalink,
    payload,
    error,
    isAlertGroupExisting,
    onSaveAndFollowLink,
    templatePage = TEMPLATE_PAGE.Integrations,
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
                  templatePage={templatePage}
                  templateName={template.name}
                  templateBody={templateBody}
                  templateType={template.type}
                  templateIsRoute={template.isRoute}
                  alertReceiveChannelId={alertReceiveChannelId}
                  outgoingWebhookId={outgoingWebhookId}
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
              <Text>
                ← Select {templatePage === TEMPLATE_PAGE.Webhooks ? 'event' : 'alert group'} or "Use custom payload"
              </Text>
            </Block>
          </div>
        )}
      </div>
    </div>
  );
};

export default TemplateResult;
