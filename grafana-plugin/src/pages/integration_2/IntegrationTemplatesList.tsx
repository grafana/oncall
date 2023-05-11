import React, { useState } from 'react';

import { ButtonCascader, CascaderOption, ConfirmModal, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';

import MonacoEditor from 'components/MonacoEditor/MonacoEditor';
import Text from 'components/Text/Text';
import { AlertTemplatesDTO } from 'models/alert_templates';

import { MONACO_INPUT_HEIGHT_SMALL, MONACO_INPUT_HEIGHT_TALL, MONACO_OPTIONS } from './Integration2.config';
import IntegrationHelper from './Integration2.helper';
import styles from './Integration2.module.scss';
import IntegrationBlockItem from './IntegrationBlockItem';
import IntegrationTemplateBlock from './IntegrationTemplateBlock';

const cx = cn.bind(styles);

interface IntegrationTemplateListProps {
  templates: AlertTemplatesDTO[];
  getTemplatesList(): CascaderOption[];
  openEditTemplateModal: (templateName: string | string[]) => void;
}

const IntegrationTemplateList: React.FC<IntegrationTemplateListProps> = ({
  templates,
  openEditTemplateModal,
  getTemplatesList,
}) => {
  const [templateRestoreName, setTemplateRestoreName] = useState<string>(undefined);

  return (
    <div className={cx('integration__templates')}>
      {templateRestoreName && (
        <ConfirmModal
          isOpen={true}
          title={'Are you sure you want to reset Slack Title template to default state'}
          confirmText={'Delete'}
          dismissText="Cancel"
          body={undefined}
          description={undefined}
          confirmationText={undefined}
          onConfirm={() => onResetTemplate(templateRestoreName)}
          onDismiss={undefined}
        />
      )}

      <IntegrationBlockItem>
        <Text type="secondary">
          Templates are used to interpret alert from monitoring. Reduce noise, customize visualization
        </Text>
      </IntegrationBlockItem>

      <IntegrationBlockItem>
        <VerticalGroup>
          <IntegrationTemplateBlock
            onRemove={() => onRemove('grouping_id_template')}
            isLoading={templateRestoreName === 'grouping_id_template'}
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
            isLoading={templateRestoreName === 'resolve_condition_template'}
            onRemove={() => onRemove('resolve_condition_template')}
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
        </VerticalGroup>
      </IntegrationBlockItem>

      <IntegrationBlockItem>
        <VerticalGroup>
          <Text type={'primary'}>Web</Text>

          <IntegrationTemplateBlock
            isLoading={templateRestoreName === 'web_title_template'}
            onRemove={() => onRemove('web_title_template')}
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
            isLoading={templateRestoreName === 'web_message_template'}
            onRemove={() => onRemove('web_message_template')}
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
            isLoading={templateRestoreName === 'web_image_url_template'}
            onRemove={() => onRemove('web_image_url_template')}
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
        </VerticalGroup>
      </IntegrationBlockItem>

      <IntegrationBlockItem>
        <VerticalGroup>
          <IntegrationTemplateBlock
            isLoading={templateRestoreName === 'acknowledge_condition_template'}
            onRemove={() => onRemove('acknowledge_condition_template')}
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
            isLoading={templateRestoreName === 'source_link_template'}
            onRemove={() => onRemove('source_link_template')}
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
        </VerticalGroup>
      </IntegrationBlockItem>

      <IntegrationBlockItem>
        <VerticalGroup>
          <IntegrationTemplateBlock
            isLoading={templateRestoreName === 'phone_call_title_template'}
            onRemove={() => onRemove('phone_call_title_template')}
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
            isLoading={templateRestoreName === 'sms_title_template'}
            onRemove={() => onRemove('sms_title_template')}
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
        </VerticalGroup>
      </IntegrationBlockItem>

      <IntegrationBlockItem>
        <VerticalGroup>
          <Text type={'primary'}>Slack</Text>

          <IntegrationTemplateBlock
            isLoading={templateRestoreName === 'slack_title_template'}
            onRemove={() => onRemove('slack_title_template')}
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
            isLoading={templateRestoreName === 'slack_message_template'}
            onRemove={() => onRemove('slack_message_template')}
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
            isLoading={templateRestoreName === 'slack_image_url_template'}
            onRemove={() => onRemove('slack_image_url_template')}
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
        </VerticalGroup>
      </IntegrationBlockItem>

      <IntegrationBlockItem>
        <VerticalGroup>
          <Text type={'primary'}>Telegram</Text>
          <IntegrationTemplateBlock
            isLoading={templateRestoreName === 'telegram_title_template'}
            onRemove={() => onRemove('telegram_title_template')}
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
            isLoading={templateRestoreName === 'telegram_message_template'}
            onRemove={() => onRemove('telegram_message_template')}
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
            isLoading={templateRestoreName === 'telegram_image_url_template'}
            onRemove={() => onRemove('telegram_image_url_template')}
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
        </VerticalGroup>
      </IntegrationBlockItem>

      <IntegrationBlockItem>
        <VerticalGroup>
          <Text type={'primary'}>Email</Text>
          <IntegrationTemplateBlock
            isLoading={templateRestoreName === 'email_title_template'}
            onRemove={() => onRemove('email_title_template')}
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
            isLoading={templateRestoreName === 'email_message_template'}
            onRemove={() => onRemove('email_message_template')}
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
        </VerticalGroup>
      </IntegrationBlockItem>

      <IntegrationBlockItem>
        <VerticalGroup>
          <Text type={'secondary'}>By default alert groups rendered based on Web templates.</Text>
          <Text type={'secondary'}>
            Customise how they rendered in SMS, Phone Calls, Mobile App, Slack, Telegram, MS Teams{' '}
          </Text>

          <div className={cx('customise-button')}>
            <ButtonCascader
              variant="secondary"
              onChange={(_key) => {
                if (Object.values(_key).length > 1) {
                  openEditTemplateModal(Object.values(_key)[1]);
                } else {
                  openEditTemplateModal(_key);
                }
              }}
              options={getTemplatesList()}
              icon="plus"
              value={undefined}
              buttonProps={{ size: 'sm' }}
            >
              Customise templates
            </ButtonCascader>
          </div>
        </VerticalGroup>
      </IntegrationBlockItem>
    </div>
  );

  function onResetTemplate(_templateName: string) {
    // here goes the logic

    setTemplateRestoreName(undefined);
  }

  function onRemove(templateName: string) {
    setTemplateRestoreName(templateName);
  }
};

export default IntegrationTemplateList;
