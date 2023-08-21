import React, { useCallback, useEffect, useMemo, useState } from 'react';

import { SelectableValue } from '@grafana/data';
import { Label, Button, HorizontalGroup, VerticalGroup, Select, LoadingPlaceholder } from '@grafana/ui';
import { capitalCase } from 'change-case';
import cn from 'classnames/bind';
import { omit } from 'lodash-es';

import { templatesToRender, Template } from 'components/AlertTemplates/AlertTemplatesForm.config';
import { getLabelFromTemplateName } from 'components/AlertTemplates/AlertTemplatesForm.helper';
import Block from 'components/GBlock/Block';
import MonacoEditor from 'components/MonacoEditor/MonacoEditor';
import SourceCode from 'components/SourceCode/SourceCode';
import Text from 'components/Text/Text';
import TemplatePreview, { TEMPLATE_PAGE } from 'containers/TemplatePreview/TemplatePreview';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { Alert } from 'models/alertgroup/alertgroup.types';
import { makeRequest } from 'network';
import LocationHelper from 'utils/LocationHelper';
import { UserActions, isUserActionAllowed } from 'utils/authorization';

import styles from './AlertTemplatesForm.module.css';

const cx = cn.bind(styles);

interface AlertTemplatesFormProps {
  templates: any;
  onUpdateTemplates: (values: any) => void;
  alertReceiveChannelId: AlertReceiveChannel['id'];
  alertGroupId?: Alert['pk'];
  demoAlertEnabled: boolean;
  handleSendDemoAlertClick: () => void;
  templatesRefreshing: boolean;
  selectedTemplateName?: string;
}

const AlertTemplatesForm = (props: AlertTemplatesFormProps) => {
  const {
    onUpdateTemplates,
    templates,
    alertReceiveChannelId,
    alertGroupId,
    demoAlertEnabled,
    handleSendDemoAlertClick,
    templatesRefreshing,
    selectedTemplateName,
  } = props;

  const [tempValues, setTempValues] = useState<{
    [key: string]: string | null;
  }>({});
  const [activeGroup, setActiveGroup] = useState<string>();
  const [activeTemplate, setActiveTemplate] = useState<Template>();

  useEffect(() => {
    makeRequest('/preview_template_options/', {});
  }, []);

  const getChangeHandler = (templateName: string) => {
    return (value: string) => {
      setTempValues((oldTempValues) => ({
        ...oldTempValues, // erase another edited templates
        [templateName]: value,
      }));
    };
  };

  const handleSubmit = useCallback(() => {
    const data = Object.keys(tempValues).reduce((acc: { [key: string]: string }, key: string) => {
      if (templates[key] !== tempValues[key]) {
        acc = { ...acc, [key]: tempValues[key] };
      }
      return acc;
    }, {});
    onUpdateTemplates(data);
  }, [onUpdateTemplates, tempValues]);

  const handleReset = () => {
    const temValuesCopy = omit(
      tempValues,
      groups[activeGroup].map((group) => group.name)
    );
    setTempValues(temValuesCopy);
  };

  const filteredTemplatesToRender = useMemo(() => {
    return templates
      ? templatesToRender.filter((template) => {
          return template.name in templates;
        })
      : [];
  }, [templates]);

  const groups = useMemo(() => {
    const groups: { [key: string]: Template[] } = {};

    filteredTemplatesToRender.forEach((templateToRender) => {
      if (!groups[templateToRender.group]) {
        groups[templateToRender.group] = [];
      }
      groups[templateToRender.group].push(templateToRender);
    });
    return groups;
  }, [filteredTemplatesToRender]);

  const getGroupByTemplateName = (templateName: string) => {
    Object.values(groups).find((group) => {
      const foundTemplate = group.find((obj) => obj.name === templateName);
      setActiveGroup(foundTemplate?.group);
    });
  };

  const handleChangeActiveGroup = useCallback((group: SelectableValue) => {
    setActiveGroup(group.value);
  }, []);

  useEffect(() => {
    const groupsArr = Object.keys(groups);
    if (selectedTemplateName) {
      getGroupByTemplateName(selectedTemplateName);
    } else {
      if (!activeGroup && groupsArr.length) {
        setActiveGroup(groupsArr[0]);
      }
    }
  }, [groups, activeGroup]);

  useEffect(() => {
    if (activeGroup && groups[activeGroup]) {
      setActiveTemplate(groups[activeGroup][0]);
    }
  }, [activeGroup]);

  useEffect(() => {
    if (!activeTemplate && filteredTemplatesToRender.length) {
      setActiveTemplate(filteredTemplatesToRender[0]);
    }
  }, [activeTemplate, filteredTemplatesToRender]);

  if (!activeTemplate) {
    return <LoadingPlaceholder text="Loading..." />;
  }

  const sendDemoAlertBlock = (
    <HorizontalGroup>
      <Text type="secondary">There are no alerts from this monitoring yet.</Text>
      {demoAlertEnabled ? (
        <WithPermissionControlTooltip userAction={UserActions.IntegrationsTest}>
          <Button className={cx('button')} variant="primary" onClick={handleSendDemoAlertClick} size="sm">
            Send demo alert
          </Button>
        </WithPermissionControlTooltip>
      ) : null}
    </HorizontalGroup>
  );
  const handleGoToTemplateSettingsCllick = () => LocationHelper.update({ tab: 'Autoresolve' }, 'partial');

  return (
    <div className={cx('root')}>
      <Block bordered>
        <VerticalGroup>
          <Label>Edit template for</Label>
          <Select
            options={Object.keys(groups).map((group: string) => ({
              value: group,
              label: capitalCase(group),
            }))}
            value={activeGroup}
            onChange={handleChangeActiveGroup}
            className={cx('select', 'select-template')}
          />
        </VerticalGroup>
      </Block>
      <div className={cx('templatesInfo')}>
        <Block className={cx('templates', 'borderLeftRightBottom')}>
          <VerticalGroup>
            <Text type="secondary">
              <p>
                <a href="https://jinja.palletsprojects.com/en/3.0.x/" target="_blank" rel="noreferrer">
                  Jinja2
                </a>
                {activeGroup === 'slack' && ', Slack markdown'}
                {activeGroup === 'web' && ', Markdown'}
                {activeGroup === 'telegram' && ', html'}
                {' supported. '}
                Reserved variables available: <Text keyboard>payload</Text>, <Text keyboard>grafana_oncall_link</Text>,{' '}
                <Text keyboard>grafana_oncall_incident_id</Text>, <Text keyboard>integration_name</Text>,
                <Text keyboard>source_link</Text>. Press <Text keyboard>Ctrl</Text>+<Text keyboard>Space</Text> to get
                suggestions
              </p>
            </Text>
            {groups[activeGroup].map((activeTemplate) => (
              <div
                key={activeTemplate.name}
                className={cx('template-form', {
                  'template-form-full': true,
                  'autoresolve-condition': selectedTemplateName && activeTemplate.name === 'resolve_condition_template',
                })}
              >
                <Label className={cx({ 'autoresolve-label': activeTemplate.name === 'resolve_condition_template' })}>
                  {getLabelFromTemplateName(activeTemplate.name, activeGroup)}
                </Label>
                {activeTemplate.name === 'resolve_condition_template' && (
                  <Text type="secondary" size="small">
                    To activate autoresolving change integration
                    <Button fill="text" size="sm" onClick={handleGoToTemplateSettingsCllick}>
                      settings
                    </Button>
                  </Text>
                )}
                <MonacoEditor
                  value={tempValues[activeTemplate.name] ?? (templates[activeTemplate.name] || '')}
                  disabled={false}
                  data={templates}
                  onChange={getChangeHandler(activeTemplate.name)}
                  loading={templatesRefreshing}
                />
                <div className={cx('typographyText')}>
                  <Text type="secondary">
                    Press <Text keyboard>Ctrl</Text>+<Text keyboard>Space</Text> to get suggestions
                  </Text>
                  {activeGroup === 'web' && activeTemplate.name === 'web_title_template' && (
                    <div className={cx('web-title-message')}>
                      <Text type="secondary" size="small">
                        Please note that after changing the web title template new alert groups will be searchable by
                        new title. Alert Groups created before the template was changed will be still searchable by old
                        title only.
                      </Text>
                    </div>
                  )}
                </div>
              </div>
            ))}
            <HorizontalGroup spacing="sm">
              <WithPermissionControlTooltip userAction={UserActions.IntegrationsWrite}>
                <Button variant="primary" onClick={handleSubmit}>
                  Save Templates
                </Button>
              </WithPermissionControlTooltip>
              <Button variant="destructive" onClick={handleReset}>
                Reset Template
              </Button>
            </HorizontalGroup>
          </VerticalGroup>
        </Block>
        <Block className={cx('templates', 'borderRightBottom')}>
          <VerticalGroup>
            {templates?.payload_example ? (
              <VerticalGroup spacing="md">
                {isUserActionAllowed(UserActions.IntegrationsTest) && (
                  <VerticalGroup>
                    <Label>{`${capitalCase(activeGroup)} Preview`}</Label>
                    <VerticalGroup style={{ width: '100%' }}>
                      {groups[activeGroup].map((template) => (
                        <TemplatePreview
                          templatePage={TEMPLATE_PAGE.Integrations}
                          key={template.name}
                          templateName={template.name}
                          templateBody={tempValues[template.name] ?? templates[template.name]}
                          alertReceiveChannelId={alertReceiveChannelId}
                          alertGroupId={alertGroupId}
                        />
                      ))}
                    </VerticalGroup>
                  </VerticalGroup>
                )}
                <VerticalGroup>
                  <Label>Payload Example</Label>
                  <SourceCode>{JSON.stringify(templates?.payload_example, null, 4)}</SourceCode>
                </VerticalGroup>
              </VerticalGroup>
            ) : (
              sendDemoAlertBlock
            )}
          </VerticalGroup>
        </Block>
      </div>
    </div>
  );
};

export default AlertTemplatesForm;
