import React, { useState, useCallback } from 'react';

import { ConfirmModal, InlineSwitch, Tooltip } from '@grafana/ui';
import cn from 'classnames/bind';

import IntegrationBlockItem from 'components/Integrations/IntegrationBlockItem';
import IntegrationTemplateBlock from 'components/Integrations/IntegrationTemplateBlock';
import MonacoEditor from 'components/MonacoEditor/MonacoEditor';
import { MONACO_READONLY_CONFIG } from 'components/MonacoEditor/MonacoEditor.config';
import Text from 'components/Text/Text';
import { templatesToRender } from 'containers/IntegrationContainers/IntegrationTemplatesList.config';
import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { AlertTemplatesDTO } from 'models/alert_templates';
import IntegrationHelper from 'pages/integration/Integration.helper';
import styles from 'pages/integration/Integration.module.scss';
import { MONACO_INPUT_HEIGHT_TALL } from 'pages/integration/IntegrationCommon.config';
import { useStore } from 'state/useStore';
import { openErrorNotification, openNotification } from 'utils';

const cx = cn.bind(styles);

interface IntegrationTemplateListProps {
  templates: AlertTemplatesDTO[];
  alertReceiveChannelId: AlertReceiveChannel['id'];
  openEditTemplateModal: (templateName: string | string[]) => void;
  alertReceiveChannelIsBasedOnAlertManager: boolean;
  alertReceiveChannelAllowSourceBasedResolving: boolean;
}

const IntegrationTemplateList: React.FC<IntegrationTemplateListProps> = ({
  templates,
  openEditTemplateModal,
  alertReceiveChannelId,
  alertReceiveChannelIsBasedOnAlertManager,
  alertReceiveChannelAllowSourceBasedResolving,
}) => {
  const { alertReceiveChannelStore } = useStore();
  const [isRestoringTemplate, setIsRestoringTemplate] = useState<boolean>(false);
  const [templateRestoreName, setTemplateRestoreName] = useState<string>(undefined);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [autoresolveValue, setAutoresolveValue] = useState<boolean>(alertReceiveChannelAllowSourceBasedResolving);

  const handleSaveClick = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    setAutoresolveValue(event.target.checked);
    alertReceiveChannelStore
      .saveAlertReceiveChannel(alertReceiveChannelId, {
        allow_source_based_resolving: event.target.checked,
      })
      .then(() => {
        openNotification('Autoresolve ' + (event.target.checked ? 'enabled' : 'disabled'));
      });
  }, []);

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
          Set templates to interpret monitoring alerts and minimize noise. Group alerts, enable auto-resolution,
          customize visualizations and notifications by extracting data from alerts.
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
                isTemplateEditable={isResolveConditionTemplateEditable(contents.name)}
                renderInput={() => (
                  <>
                    {isResolveConditionTemplate(contents.name) && (
                      <Tooltip content={'Edit'}>
                        <InlineSwitch
                          value={autoresolveValue}
                          onChange={handleSaveClick}
                          className={cx('inline-switch')}
                        />
                      </Tooltip>
                    )}
                    {isResolveConditionTemplateEditable(contents.name) && (
                      <div className={cx('input', { 'input-with-toggle': isResolveConditionTemplate(contents.name) })}>
                        <MonacoEditor
                          value={IntegrationHelper.getFilteredTemplate(
                            templates[contents.name] || '',
                            contents.height === MONACO_INPUT_HEIGHT_TALL
                          )}
                          disabled={true}
                          height={contents.height}
                          data={templates}
                          showLineNumbers={false}
                          monacoOptions={MONACO_READONLY_CONFIG}
                        />
                      </div>
                    )}
                  </>
                )}
                onEdit={() => openEditTemplateModal(contents.name)}
              />
            ))}
          </VerticalBlock>
        </IntegrationBlockItem>
      ))}
    </div>
  );

  function isResolveConditionTemplateEditable(templateName: string) {
    return (
      !(alertReceiveChannelIsBasedOnAlertManager && isResolveConditionTemplate(templateName)) &&
      (alertReceiveChannelAllowSourceBasedResolving || !isResolveConditionTemplate(templateName))
    );
  }

  function isResolveConditionTemplate(templateName: string) {
    return templateName === 'resolve_condition_template';
  }

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
