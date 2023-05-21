import React, { useState } from 'react';

import { ConfirmModal } from '@grafana/ui';
import cn from 'classnames/bind';

import MonacoEditor from 'components/MonacoEditor/MonacoEditor';
import Text from 'components/Text/Text';
import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { AlertTemplatesDTO } from 'models/alert_templates';
import { useStore } from 'state/useStore';
import { openErrorNotification, openNotification } from 'utils';

import { MONACO_INPUT_HEIGHT_SMALL, MONACO_INPUT_HEIGHT_TALL, MONACO_OPTIONS } from './Integration2.config';
import IntegrationHelper from './Integration2.helper';
import styles from './Integration2.module.scss';
import IntegrationBlockItem from './IntegrationBlockItem';
import IntegrationTemplateBlock from './IntegrationTemplateBlock';

const cx = cn.bind(styles);

interface IntegrationTemplateListProps {
  templates: AlertTemplatesDTO[];
  alertReceiveChannelId: AlertReceiveChannel['id'];
  openEditTemplateModal: (templateName: string | string[]) => void;
}

const IntegrationTemplateList: React.FC<IntegrationTemplateListProps> = ({
  templates,
  openEditTemplateModal,
  alertReceiveChannelId,
}) => {
  const { alertReceiveChannelStore } = useStore();
  const [isRestoringTemplate, setIsRestoringTemplate] = useState<boolean>(false);
  const [templateRestoreName, setTemplateRestoreName] = useState<string>(undefined);
  const [showConfirmModal, setShowConfirmModal] = useState(false);

  return (
    <div className={cx('integration__templates')}>
      {showConfirmModal && (
        <ConfirmModal
          isOpen={true}
          title={undefined}
          confirmText={'Reset'}
          dismissText="Cancel"
          body={'Are you sure you want to reset Slack Title template to default state?'}
          description={undefined}
          confirmationText={undefined}
          onConfirm={() => onResetTemplate(templateRestoreName)}
          onDismiss={() => onDismiss()}
        />
      )}

      <IntegrationBlockItem>
        <Text type="secondary">
          Templates are used to interpret alert from monitoring. Reduce noise, customize visualization
        </Text>
      </IntegrationBlockItem>

      <IntegrationBlockItem>
        <VerticalBlock>
          <IntegrationTemplateBlock
            onRemove={() => onShowConfirmModal('grouping_id_template')}
            isLoading={isRestoringTemplate && templateRestoreName === 'grouping_id_template'}
            label={'Grouping'}
            renderInput={() => (
              <div className={cx('input', 'input--short')}>
                <MonacoEditor
                  value={IntegrationHelper.getFilteredTemplate(templates['grouping_id_template'] || '', false)}
                  disabled={true}
                  height={MONACO_INPUT_HEIGHT_SMALL}
                  data={templates}
                  showLineNumbers={false}
                  monacoOptions={MONACO_OPTIONS}
                />
              </div>
            )}
            onEdit={() => openEditTemplateModal('grouping_id_template')}
          />

          <IntegrationTemplateBlock
            isLoading={isRestoringTemplate && templateRestoreName === 'resolve_condition_template'}
            onRemove={() => onShowConfirmModal('resolve_condition_template')}
            label={'Auto resolve'}
            renderInput={() => (
              <div className={cx('input', 'input--short')}>
                <MonacoEditor
                  value={IntegrationHelper.getFilteredTemplate(templates['resolve_condition_template'] || '', false)}
                  disabled={true}
                  height={MONACO_INPUT_HEIGHT_SMALL}
                  data={templates}
                  showLineNumbers={false}
                  monacoOptions={MONACO_OPTIONS}
                />
              </div>
            )}
            onEdit={() => openEditTemplateModal('resolve_condition_template')}
          />
        </VerticalBlock>
      </IntegrationBlockItem>

      <IntegrationBlockItem>
        <VerticalBlock>
          <Text type={'primary'}>Web</Text>

          <IntegrationTemplateBlock
            isLoading={isRestoringTemplate && templateRestoreName === 'web_title_template'}
            onRemove={() => onShowConfirmModal('web_title_template')}
            label={'Title'}
            renderInput={() => (
              <div className={cx('input', 'input--long')}>
                <MonacoEditor
                  value={IntegrationHelper.getFilteredTemplate(templates['web_title_template'] || '', true)}
                  disabled={true}
                  height={MONACO_INPUT_HEIGHT_TALL}
                  data={templates}
                  showLineNumbers={false}
                  monacoOptions={MONACO_OPTIONS}
                />
              </div>
            )}
            onEdit={() => openEditTemplateModal('web_title_template')}
          />

          <IntegrationTemplateBlock
            isLoading={isRestoringTemplate && templateRestoreName === 'web_message_template'}
            onRemove={() => onShowConfirmModal('web_message_template')}
            label={'Message'}
            renderInput={() => (
              <div className={cx('input', 'input--long')}>
                <MonacoEditor
                  value={IntegrationHelper.getFilteredTemplate(templates['web_message_template'] || '', true)}
                  disabled={true}
                  height={MONACO_INPUT_HEIGHT_TALL}
                  data={templates}
                  showLineNumbers={false}
                  monacoOptions={MONACO_OPTIONS}
                />
              </div>
            )}
            onEdit={() => openEditTemplateModal('web_message_template')}
          />

          <IntegrationTemplateBlock
            isLoading={isRestoringTemplate && templateRestoreName === 'web_image_url_template'}
            onRemove={() => onShowConfirmModal('web_image_url_template')}
            label={'Image'}
            renderInput={() => (
              <div className={cx('input', 'input--long')}>
                <MonacoEditor
                  value={IntegrationHelper.getFilteredTemplate(templates['web_image_url_template'] || '', false)}
                  disabled={true}
                  height={MONACO_INPUT_HEIGHT_SMALL}
                  data={templates}
                  showLineNumbers={false}
                  monacoOptions={MONACO_OPTIONS}
                />
              </div>
            )}
            onEdit={() => openEditTemplateModal('web_image_url_template')}
          />
        </VerticalBlock>
      </IntegrationBlockItem>

      <IntegrationBlockItem>
        <VerticalBlock>
          <IntegrationTemplateBlock
            isLoading={isRestoringTemplate && templateRestoreName === 'acknowledge_condition_template'}
            onRemove={() => onShowConfirmModal('acknowledge_condition_template')}
            label={'Auto acknowledge'}
            renderInput={() => (
              <div className={cx('input', 'input--short')}>
                <MonacoEditor
                  value={IntegrationHelper.getFilteredTemplate(
                    templates['acknowledge_condition_template'] || '',
                    false
                  )}
                  disabled={true}
                  height={MONACO_INPUT_HEIGHT_SMALL}
                  data={templates}
                  showLineNumbers={false}
                  monacoOptions={MONACO_OPTIONS}
                />
              </div>
            )}
            onEdit={() => openEditTemplateModal('acknowledge_condition_template')}
          />

          <IntegrationTemplateBlock
            isLoading={isRestoringTemplate && templateRestoreName === 'source_link_template'}
            onRemove={() => onShowConfirmModal('source_link_template')}
            label={'Source Link'}
            renderInput={() => (
              <div className={cx('input', 'input--short')}>
                <MonacoEditor
                  value={IntegrationHelper.getFilteredTemplate(templates['source_link_template'] || '', false)}
                  disabled={true}
                  height={MONACO_INPUT_HEIGHT_SMALL}
                  data={templates}
                  showLineNumbers={false}
                  monacoOptions={MONACO_OPTIONS}
                />
              </div>
            )}
            onEdit={() => openEditTemplateModal('source_link_template')}
          />
        </VerticalBlock>
      </IntegrationBlockItem>

      <IntegrationBlockItem>
        <VerticalBlock>
          <IntegrationTemplateBlock
            isLoading={isRestoringTemplate && templateRestoreName === 'phone_call_title_template'}
            onRemove={() => onShowConfirmModal('phone_call_title_template')}
            label={'Phone Call'}
            renderInput={() => (
              <div className={cx('input', 'input--short')}>
                <MonacoEditor
                  value={IntegrationHelper.getFilteredTemplate(templates['phone_call_title_template'] || '', false)}
                  disabled={true}
                  height={MONACO_INPUT_HEIGHT_SMALL}
                  data={templates}
                  showLineNumbers={false}
                  monacoOptions={MONACO_OPTIONS}
                />
              </div>
            )}
            onEdit={() => openEditTemplateModal('phone_call_title_template')}
          />

          <IntegrationTemplateBlock
            isLoading={isRestoringTemplate && templateRestoreName === 'sms_title_template'}
            onRemove={() => onShowConfirmModal('sms_title_template')}
            label={'SMS'}
            renderInput={() => (
              <div className={cx('input', 'input--short')}>
                <MonacoEditor
                  value={IntegrationHelper.getFilteredTemplate(templates['sms_title_template'] || '', false)}
                  disabled={true}
                  height={MONACO_INPUT_HEIGHT_SMALL}
                  data={templates}
                  showLineNumbers={false}
                  monacoOptions={MONACO_OPTIONS}
                />
              </div>
            )}
            onEdit={() => openEditTemplateModal('sms_title_template')}
          />
        </VerticalBlock>
      </IntegrationBlockItem>

      <IntegrationBlockItem>
        <VerticalBlock>
          <Text type={'primary'}>Slack</Text>

          <IntegrationTemplateBlock
            isLoading={isRestoringTemplate && templateRestoreName === 'slack_title_template'}
            onRemove={() => onShowConfirmModal('slack_title_template')}
            label={'Title'}
            renderInput={() => (
              <div className={cx('input', 'input--long')}>
                <MonacoEditor
                  value={IntegrationHelper.getFilteredTemplate(templates['slack_title_template'] || '', false)}
                  disabled={true}
                  height={MONACO_INPUT_HEIGHT_SMALL}
                  data={templates}
                  showLineNumbers={false}
                  monacoOptions={MONACO_OPTIONS}
                />
              </div>
            )}
            onEdit={() => openEditTemplateModal('slack_title_template')}
          />

          <IntegrationTemplateBlock
            isLoading={isRestoringTemplate && templateRestoreName === 'slack_message_template'}
            onRemove={() => onShowConfirmModal('slack_message_template')}
            label={'Message'}
            renderInput={() => (
              <div className={cx('input', 'input--long')}>
                <MonacoEditor
                  value={IntegrationHelper.getFilteredTemplate(templates['slack_message_template'] || '', true)}
                  disabled={true}
                  height={MONACO_INPUT_HEIGHT_TALL}
                  data={templates}
                  showLineNumbers={false}
                  monacoOptions={MONACO_OPTIONS}
                />
              </div>
            )}
            onEdit={() => openEditTemplateModal('slack_message_template')}
          />

          <IntegrationTemplateBlock
            isLoading={isRestoringTemplate && templateRestoreName === 'slack_image_url_template'}
            onRemove={() => onShowConfirmModal('slack_image_url_template')}
            label={'Image'}
            renderInput={() => (
              <div className={cx('input', 'input--long')}>
                <MonacoEditor
                  value={IntegrationHelper.getFilteredTemplate(templates['slack_image_url_template'] || '', false)}
                  disabled={true}
                  height={MONACO_INPUT_HEIGHT_SMALL}
                  data={templates}
                  showLineNumbers={false}
                  monacoOptions={MONACO_OPTIONS}
                />
              </div>
            )}
            onEdit={() => openEditTemplateModal('slack_image_url_template')}
          />
        </VerticalBlock>
      </IntegrationBlockItem>

      <IntegrationBlockItem>
        <VerticalBlock>
          <Text type={'primary'}>Telegram</Text>
          <IntegrationTemplateBlock
            isLoading={isRestoringTemplate && templateRestoreName === 'telegram_title_template'}
            onRemove={() => onShowConfirmModal('telegram_title_template')}
            label={'Title'}
            renderInput={() => (
              <div className={cx('input', 'input--long')}>
                <MonacoEditor
                  value={IntegrationHelper.getFilteredTemplate(templates['telegram_title_template'] || '', false)}
                  disabled={true}
                  height={MONACO_INPUT_HEIGHT_SMALL}
                  data={templates}
                  showLineNumbers={false}
                  monacoOptions={MONACO_OPTIONS}
                />
              </div>
            )}
            onEdit={() => openEditTemplateModal('telegram_title_template')}
          />

          <IntegrationTemplateBlock
            isLoading={isRestoringTemplate && templateRestoreName === 'telegram_message_template'}
            onRemove={() => onShowConfirmModal('telegram_message_template')}
            label={'Message'}
            renderInput={() => (
              <div className={cx('input', 'input--long')}>
                <MonacoEditor
                  value={IntegrationHelper.getFilteredTemplate(templates['telegram_message_template'] || '', true)}
                  disabled={true}
                  height={MONACO_INPUT_HEIGHT_TALL}
                  data={templates}
                  showLineNumbers={false}
                  monacoOptions={MONACO_OPTIONS}
                />
              </div>
            )}
            onEdit={() => openEditTemplateModal('telegram_message_template')}
          />

          <IntegrationTemplateBlock
            isLoading={isRestoringTemplate && templateRestoreName === 'telegram_image_url_template'}
            onRemove={() => onShowConfirmModal('telegram_image_url_template')}
            label={'Image'}
            renderInput={() => (
              <div className={cx('input', 'input--long')}>
                <MonacoEditor
                  value={IntegrationHelper.getFilteredTemplate(templates['telegram_image_url_template'] || '', false)}
                  disabled={true}
                  height={MONACO_INPUT_HEIGHT_SMALL}
                  data={templates}
                  showLineNumbers={false}
                  monacoOptions={MONACO_OPTIONS}
                />
              </div>
            )}
            onEdit={() => openEditTemplateModal('telegram_image_url_template')}
          />
        </VerticalBlock>
      </IntegrationBlockItem>

      <IntegrationBlockItem>
        <VerticalBlock>
          <Text type={'primary'}>Email</Text>
          <IntegrationTemplateBlock
            isLoading={isRestoringTemplate && templateRestoreName === 'email_title_template'}
            onRemove={() => onShowConfirmModal('email_title_template')}
            label={'Title'}
            renderInput={() => (
              <div className={cx('input', 'input--long')}>
                <MonacoEditor
                  value={IntegrationHelper.getFilteredTemplate(templates['email_title_template'] || '', false)}
                  disabled={true}
                  height={MONACO_INPUT_HEIGHT_SMALL}
                  data={templates}
                  showLineNumbers={false}
                  monacoOptions={MONACO_OPTIONS}
                />
              </div>
            )}
            onEdit={() => openEditTemplateModal('email_title_template')}
          />

          <IntegrationTemplateBlock
            isLoading={isRestoringTemplate && templateRestoreName === 'email_message_template'}
            onRemove={() => onShowConfirmModal('email_message_template')}
            label={'Message'}
            renderInput={() => (
              <div className={cx('input', 'input--long')}>
                <MonacoEditor
                  value={IntegrationHelper.getFilteredTemplate(templates['email_message_template'] || '', true)}
                  disabled={true}
                  height={MONACO_INPUT_HEIGHT_TALL}
                  data={templates}
                  showLineNumbers={false}
                  monacoOptions={MONACO_OPTIONS}
                />
              </div>
            )}
            onEdit={() => openEditTemplateModal('email_message_template')}
          />
        </VerticalBlock>
      </IntegrationBlockItem>
    </div>
  );

  function onShowConfirmModal(templateName: string) {
    setTemplateRestoreName(templateName);
    setShowConfirmModal(true);
  }

  function onDismiss() {
    setTemplateRestoreName(undefined);
    setShowConfirmModal(false);
  }

  function onResetTemplate(templateName: string) {
    setTemplateRestoreName(undefined);
    setIsRestoringTemplate(true);

    alertReceiveChannelStore
      .saveTemplates(alertReceiveChannelId, { [templateName]: '' })
      .then(() => {
        openNotification('The Alert template has been updated');
      })
      .catch((err) => {
        if (err.response?.data?.length > 0) {
          openErrorNotification(err.response.data);
        } else {
          openErrorNotification(err.message);
        }
      })
      .finally(() => {
        setIsRestoringTemplate(false);
        setShowConfirmModal(false);
      });
  }
};

const VerticalBlock: React.FC<{ children: React.ReactElement[] }> = ({ children }) => {
  return <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>{children}</div>;
};

export default IntegrationTemplateList;
