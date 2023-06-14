import React, { useState } from 'react';

import { ConfirmModal } from '@grafana/ui';
import cn from 'classnames/bind';

import IntegrationBlockItem from 'components/Integrations/IntegrationBlockItem';
import IntegrationTemplateBlock from 'components/Integrations/IntegrationTemplateBlock';
import MonacoEditor from 'components/MonacoEditor/MonacoEditor';
import Text from 'components/Text/Text';
import { templatesToRender } from 'containers/IntegrationContainers/IntegrationTemplatesList.config';
import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { AlertTemplatesDTO } from 'models/alert_templates';
import { MONACO_INPUT_HEIGHT_TALL, MONACO_OPTIONS } from 'pages/integration_2/Integration2.config';
import IntegrationHelper from 'pages/integration_2/Integration2.helper';
import styles from 'pages/integration_2/Integration2.module.scss';
import { useStore } from 'state/useStore';
import { openErrorNotification, openNotification } from 'utils';

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
          Templates are used to interpret alert from monitoring. Reduce noise by grouping, set auto-resolution,
          customize visualization and notifications by extracting data from alert.
        </Text>
      </IntegrationBlockItem>

      {templatesToRender.map((template, key) => (
        <IntegrationBlockItem key={key}>
          <VerticalBlock>
            {template.name && <Text type={'primary'}>{template.name}</Text>}

            {template.contents.map((contents, innerKey) => (
              <IntegrationTemplateBlock
                key={innerKey}
                isLoading={isRestoringTemplate && templateRestoreName === contents.name}
                onRemove={() => onShowConfirmModal(contents.name)}
                label={contents.label}
                labelTooltip={contents.labelTooltip}
                renderInput={() => (
                  <div className={cx('input')}>
                    <MonacoEditor
                      value={IntegrationHelper.getFilteredTemplate(
                        templates[contents.name] || '',
                        contents.height === MONACO_INPUT_HEIGHT_TALL
                      )}
                      disabled={true}
                      height={contents.height}
                      data={templates}
                      showLineNumbers={false}
                      monacoOptions={MONACO_OPTIONS}
                    />
                  </div>
                )}
                onEdit={() => openEditTemplateModal(contents.name)}
              />
            ))}
          </VerticalBlock>
        </IntegrationBlockItem>
      ))}
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

const VerticalBlock: React.FC<{ children: any[] }> = ({ children }) => {
  return <div className={cx('vertical-block')}>{children}</div>;
};

export default IntegrationTemplateList;
