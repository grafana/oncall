import React, { useCallback, useEffect, useMemo, useState } from 'react';

import { SelectableValue } from '@grafana/data';
import { getLocationSrv } from '@grafana/runtime';
import { Label, Button, HorizontalGroup, VerticalGroup, Select, LoadingPlaceholder } from '@grafana/ui';
import { capitalCase } from 'change-case';
import cn from 'classnames/bind';
import { omit } from 'lodash-es';

import { templatesToRender, Template } from 'components/AlertTemplates/AlertTemplatesForm.config';
import { getLabelFromTemplateName, includeTemplateGroup } from 'components/AlertTemplates/AlertTemplatesForm.helper';
import Collapse from 'components/Collapse/Collapse';
import Block from 'components/GBlock/Block';
import MonacoJinja2Editor from 'components/MonacoJinja2Editor/MonacoJinja2Editor';
import SourceCode from 'components/SourceCode/SourceCode';
import Text from 'components/Text/Text';
import TemplatePreview from 'containers/TemplatePreview/TemplatePreview';
import { WithPermissionControl } from 'containers/WithPermissionControl/WithPermissionControl';
import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { Alert } from 'models/alertgroup/alertgroup.types';
import { makeRequest } from 'network';
import { UserAction } from 'state/userAction';

import styles from './AlertTemplatesForm.module.css';

const cx = cn.bind(styles);

interface AlertTemplatesFormProps {
  templates: any;
  onUpdateTemplates: (values: any) => void;
  errors: any;
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
    errors,
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
      groups[activeGroup].map((group: any) => group.name)
    );
    setTempValues(temValuesCopy);
  };

  const [activeGroup, setActiveGroup] = useState<string>();
  const [activeTemplate, setActiveTemplate] = useState<any>();

  const filteredTemplatesToRender = useMemo(() => {
    return templates
      ? templatesToRender.filter((template) => {
          return template.name in templates;
        })
      : [];
  }, [templates]);

  const groups = useMemo(() => {
    const groups: { [key: string]: any } = {};

    filteredTemplatesToRender.forEach((templateToRender) => {
      if (!groups[templateToRender.group]) {
        if (!includeTemplateGroup(templateToRender.group)) {
          return;
        }
        groups[templateToRender.group] = [];
      }
      groups[templateToRender.group].push(templateToRender);
    });
    return groups;
  }, [filteredTemplatesToRender]);

  const getGroupByTemplateName = (templateName: string) => {
    Object.values(groups).find((group) => {
      const foundTemplate = group.find((obj: any) => {
        if (obj.name == templateName) {
          return obj;
        }
      });
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

  const getTemplatePreviewEditClickHandler = (templateName: string) => {
    return () => {
      const template = templatesToRender.find((template) => template.name === templateName);
      setActiveTemplate(template);
    };
  };

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
        <WithPermissionControl userAction={UserAction.SendDemoAlert}>
          <Button className={cx('button')} variant="primary" onClick={handleSendDemoAlertClick} size="sm">
            Send demo alert
          </Button>
        </WithPermissionControl>
      ) : null}
    </HorizontalGroup>
  );
  const handleGoToTemplateSettingsCllick = () => {
    getLocationSrv().update({ partial: true, query: { tab: 'Autoresolve' } });
  };

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
                <a href="https://jinja.palletsprojects.com/en/3.0.x/" target="_blank">
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
            {groups[activeGroup].map((activeTemplate: any) => (
              <div
                key={activeTemplate.name}
                className={cx('template-form', {
                  'template-form-full': true,
                  'autoresolve-condition': selectedTemplateName && activeTemplate.name == 'resolve_condition_template',
                })}
              >
                <Label className={cx({ 'autoresolve-label': activeTemplate.name == 'resolve_condition_template' })}>
                  {getLabelFromTemplateName(activeTemplate.name, activeGroup)}
                </Label>
                {activeTemplate.name == 'resolve_condition_template' && (
                  <Text type="secondary" size="small">
                    To activate autoresolving change integration
                    <Button fill="text" size="sm" onClick={handleGoToTemplateSettingsCllick}>
                      settings
                    </Button>
                  </Text>
                )}
                <MonacoJinja2Editor
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
                </div>
              </div>
            ))}
            <HorizontalGroup spacing="sm">
              <WithPermissionControl userAction={UserAction.UpdateAlertReceiveChannels}>
                <Button variant="primary" onClick={handleSubmit}>
                  Save Templates
                </Button>
              </WithPermissionControl>
              <Button variant="destructive" onClick={handleReset}>
                Reset Template
              </Button>
            </HorizontalGroup>
          </VerticalGroup>
        </Block>
        <Block className={cx('templates', 'borderRightBottom')}>
          <VerticalGroup>
            {templates?.payload_example ? (
              <VerticalGroup>
                <VerticalGroup>
                  <Label>{`${capitalCase(activeGroup)} Preview`}</Label>
                  <VerticalGroup style={{ width: '100%' }}>
                    {groups[activeGroup].map((template: any) => (
                      <TemplatePreview
                        active={template.name === activeTemplate?.name}
                        key={template.name}
                        templateName={template.name}
                        templateBody={tempValues[template.name] ?? templates[template.name]}
                        onEditClick={getTemplatePreviewEditClickHandler(template.name)}
                        alertReceiveChannelId={alertReceiveChannelId}
                        alertGroupId={alertGroupId}
                      />
                    ))}
                  </VerticalGroup>
                </VerticalGroup>
                <div className={cx('payloadExample')}>
                  <VerticalGroup>
                    <Label>Payload Example</Label>
                    <SourceCode>{JSON.stringify(templates?.payload_example, null, 4)}</SourceCode>
                  </VerticalGroup>
                </div>
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
