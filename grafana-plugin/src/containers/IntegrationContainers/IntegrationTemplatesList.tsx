import React, { useState, useCallback } from 'react';

import { InlineSwitch, Tooltip } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import { IntegrationBlockItem } from 'components/Integrations/IntegrationBlockItem';
import { IntegrationTemplateBlock } from 'components/Integrations/IntegrationTemplateBlock';
import { MonacoEditor } from 'components/MonacoEditor/MonacoEditor';
import { MONACO_READONLY_CONFIG } from 'components/MonacoEditor/MonacoEditor.config';
import { Text } from 'components/Text/Text';
import { getTemplatesToRender } from 'containers/IntegrationContainers/IntegrationTemplatesList.config';
import { AlertTemplatesDTO } from 'models/alert_templates/alert_templates';
import { ApiSchemas } from 'network/oncall-api/api.types';
import { IntegrationHelper } from 'pages/integration/Integration.helper';
import styles from 'pages/integration/Integration.module.scss';
import { MONACO_INPUT_HEIGHT_TALL } from 'pages/integration/IntegrationCommon.config';
import { useStore } from 'state/useStore';
import { openErrorNotification, openNotification } from 'utils/utils';

const cx = cn.bind(styles);

interface IntegrationTemplateListProps {
  templates: AlertTemplatesDTO[];
  alertReceiveChannelId: ApiSchemas['AlertReceiveChannel']['id'];
  openEditTemplateModal: (templateName: string | string[]) => void;
  alertReceiveChannelIsBasedOnAlertManager: boolean;
  alertReceiveChannelAllowSourceBasedResolving: boolean;
}

export const IntegrationTemplateList: React.FC<IntegrationTemplateListProps> = observer(
  ({
    templates,
    openEditTemplateModal,
    alertReceiveChannelId,
    alertReceiveChannelIsBasedOnAlertManager,
    alertReceiveChannelAllowSourceBasedResolving,
  }) => {
    const { alertReceiveChannelStore, features } = useStore();
    const [isRestoringTemplate, setIsRestoringTemplate] = useState(false);
    const [templateRestoreName, setTemplateRestoreName] = useState<string>(undefined);
    const [autoresolveValue, setAutoresolveValue] = useState(alertReceiveChannelAllowSourceBasedResolving);

    const handleSaveClick = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
      setAutoresolveValue(event.target.checked);
      await alertReceiveChannelStore.saveAlertReceiveChannel(alertReceiveChannelId, {
        allow_source_based_resolving: event.target.checked,
      });
      openNotification('Autoresolve ' + (event.target.checked ? 'enabled' : 'disabled'));
    }, []);

    const templatesToRender = getTemplatesToRender(features);

    return (
      <div className={cx('integration__templates')}>
        {templatesToRender.map((template, key) => (
          <IntegrationBlockItem key={key}>
            <VerticalBlock>
              {template.name && <Text type={'primary'}>{template.name}</Text>}
              {template.contents.map((contents, innerKey) => (
                <IntegrationTemplateBlock
                  key={innerKey}
                  isLoading={isRestoringTemplate && templateRestoreName === contents.name}
                  onRemove={() => onResetTemplate(contents.name)}
                  label={contents.label}
                  labelTooltip={contents.labelTooltip}
                  isTemplateEditable={isTemplateEditable(contents.name)}
                  warningOnEdit={
                    alertReceiveChannelIsBasedOnAlertManager &&
                    (isGroupingIdTemplate(contents.name) || isResolveConditionTemplate(contents.name))
                      ? 'Caution: Changing this template can lead to unexpected alert behavior, ' +
                        'especially if grouping is enabled in AlertManager/Grafana Alerting. ' +
                        'Please proceed only if you are completely sure of the modifications you are about to make.'
                      : undefined
                  }
                  renderInput={() => (
                    <>
                      {isResolveConditionTemplate(contents.name) && (
                        <Tooltip content={'Edit'}>
                          <InlineSwitch
                            value={autoresolveValue}
                            onChange={handleSaveClick}
                            className={cx('inline-switch')}
                            transparent
                          />
                        </Tooltip>
                      )}
                      {isTemplateEditable(contents.name) && (
                        <div
                          className={cx('input', { 'input-with-toggle': isResolveConditionTemplate(contents.name) })}
                        >
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

    function isTemplateEditable(templateName: string) {
      return alertReceiveChannelAllowSourceBasedResolving || !isResolveConditionTemplate(templateName);
    }

    function isResolveConditionTemplate(templateName: string) {
      return templateName === 'resolve_condition_template';
    }

    function isGroupingIdTemplate(templateName: string) {
      return templateName === 'grouping_id_template';
    }

    async function onResetTemplate(templateName: string) {
      setTemplateRestoreName(undefined);
      setIsRestoringTemplate(true);

      try {
        await alertReceiveChannelStore.saveTemplates(alertReceiveChannelId, { [templateName]: '' });
        openNotification('The Alert template has been updated');
      } catch (err) {
        if (err.response?.data?.length > 0) {
          openErrorNotification(err.response.data);
        } else {
          openErrorNotification(err.message);
        }
      }
    }
  }
);

const VerticalBlock: React.FC<{ children: any[] }> = ({ children }) => {
  return <div className={cx('vertical-block')}>{children}</div>;
};
