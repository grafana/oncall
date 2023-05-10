import React from 'react';

import { ButtonCascader, CascaderOption, VerticalGroup } from '@grafana/ui';
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
  const isAutoAcknOrSourceLinkChanged =
    !templates['acknowledge_condition_template_is_default'] || !templates['source_link_template'];
  const isPhoneOrSMSChanged =
    !templates['sms_title_template_is_default'] || !templates['phone_call_title_template_is_default'];
  const isSlackChanged =
    !templates['slack_title_template_is_default'] ||
    !templates['slack_message_template_is_default'] ||
    !templates['slack_image_url_template_is_default'];
  const isTelegramChanged =
    !templates['telegram_title_template_is_default'] ||
    !templates['telegram_message_template_is_default'] ||
    !templates['telegram_image_url_template_is_default'];
  const isEmailOrMessageChanged = !templates['email_title_template_is_default'] || !templates['email_message_template'];

  return (
    <div className={cx('integration__templates')}>
      <IntegrationBlockItem>
        <Text type="secondary">
          Templates are used to interpret alert from monitoring. Reduce noise, customize visualization
        </Text>
      </IntegrationBlockItem>

      <IntegrationBlockItem>
        <VerticalGroup>
          <IntegrationTemplateBlock
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

      {isAutoAcknOrSourceLinkChanged && (
        <IntegrationBlockItem>
          <VerticalGroup>
            {!templates['acknowledge_condition_template_is_default'] && (
              <IntegrationTemplateBlock
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
            )}

            {!templates['source_link_template_is_default'] && (
              <IntegrationTemplateBlock
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
            )}
          </VerticalGroup>
        </IntegrationBlockItem>
      )}

      {isPhoneOrSMSChanged && (
        <IntegrationBlockItem>
          <VerticalGroup>
            {!templates['phone_call_title_template_is_default'] && (
              <IntegrationTemplateBlock
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
            )}

            {!templates['sms_title_template_is_default'] && (
              <IntegrationTemplateBlock
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
            )}
          </VerticalGroup>
        </IntegrationBlockItem>
      )}

      {isSlackChanged && (
        <IntegrationBlockItem>
          <VerticalGroup>
            <Text type={'primary'}>Slack</Text>

            {!templates['slack_title_template_is_default'] && (
              <IntegrationTemplateBlock
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
            )}

            {!templates['slack_message_template_is_default'] && (
              <IntegrationTemplateBlock
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
            )}

            {!templates['slack_image_url_template_is_default'] && (
              <IntegrationTemplateBlock
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
            )}
          </VerticalGroup>
        </IntegrationBlockItem>
      )}

      {isTelegramChanged && (
        <IntegrationBlockItem>
          <VerticalGroup>
            <Text type={'primary'}>Telegram</Text>
            {!templates['telegram_title_template_is_default'] && (
              <IntegrationTemplateBlock
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
            )}

            {!templates['telegram_message_template_is_default'] && (
              <IntegrationTemplateBlock
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
            )}

            {!templates['telegram_image_url_template_is_default'] && (
              <IntegrationTemplateBlock
                label={'Image'}
                renderInput={() => (
                  <div className={cx('input', 'input--long')}>
                    <MonacoEditor
                      value={IntegrationHelper.getFilteredTemplate(
                        templates['telegram_image_url_template'] || '',
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
                onEdit={() => openEditTemplateModal('telegram_image_url_template')}
              />
            )}
          </VerticalGroup>
        </IntegrationBlockItem>
      )}

      {isEmailOrMessageChanged && (
        <IntegrationBlockItem>
          <VerticalGroup>
            <Text type={'primary'}>Email</Text>
            {!templates['email_title_template_is_default'] && (
              <IntegrationTemplateBlock
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
            )}

            {!templates['email_message_template_is_default'] && (
              <IntegrationTemplateBlock
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
            )}
          </VerticalGroup>
        </IntegrationBlockItem>
      )}

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
};

export default IntegrationTemplateList;
