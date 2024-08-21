import React from 'react';

import { Button, Icon, Stack } from '@grafana/ui';
import cn from 'classnames/bind';

import { TemplateForEdit } from 'components/AlertTemplates/CommonAlertTemplatesForm.config';
import { Block } from 'components/GBlock/Block';
import { Text } from 'components/Text/Text';
import styles from 'containers/IntegrationTemplate/IntegrationTemplate.module.scss';
import { TemplatePreview, TemplatePage } from 'containers/TemplatePreview/TemplatePreview';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { StackSize } from 'utils/consts';

const cx = cn.bind(styles);

interface ResultProps {
  alertReceiveChannelId?: ApiSchemas['AlertReceiveChannel']['id'];
  outgoingWebhookId?: ApiSchemas['Webhook']['id'];
  templateBody: string;
  template: TemplateForEdit;
  isAlertGroupExisting?: boolean;
  chatOpsPermalink?: string;
  payload?: { [key: string]: unknown };
  error?: string;
  onSaveAndFollowLink?: (link: string) => void;
  templateIsRoute?: boolean;
  templatePage?: TemplatePage;
}

export const TemplateResult = (props: ResultProps) => {
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
    templatePage = TemplatePage.Integrations,
  } = props;

  return (
    <div className={cx('template-block-result')}>
      <div className={cx('template-block-title')}>
        <Stack justifyContent='space-between'>
          <Text>Result</Text>
        </Stack>
      </div>
      <div className={cx('result')}>
        {payload || error ? (
          <Stack direction="column" gap={StackSize.lg}>
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
              <Stack direction="column">
                <Button onClick={() => onSaveAndFollowLink(chatOpsPermalink)}>
                  <Stack gap={StackSize.xs} align="center">
                    Save and open Alert Group in {template.additionalData.chatOpsDisplayName}{' '}
                    <Icon name="external-link-alt" />
                  </Stack>
                </Button>

                {template.additionalData.data && <Text type="secondary">{template.additionalData.data}</Text>}
              </Stack>
            )}
          </Stack>
        ) : (
          <div>
            <Block bordered fullWidth className={cx('block-style')} withBackground>
              <Text>
                ← Select {templatePage === TemplatePage.Webhooks ? 'event' : 'alert group'} or "Use custom payload"
              </Text>
            </Block>
          </div>
        )}
      </div>
    </div>
  );
};
