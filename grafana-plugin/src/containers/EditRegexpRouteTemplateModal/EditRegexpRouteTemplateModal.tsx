import React, { useState, useCallback } from 'react';

import { HorizontalGroup, VerticalGroup, Modal, Tooltip, Icon, Button } from '@grafana/ui';
import cn from 'classnames/bind';
import { debounce } from 'lodash-es';
import { observer } from 'mobx-react';

import { TemplateForEdit } from 'components/AlertTemplates/CommonAlertTemplatesForm.config';
import Block from 'components/GBlock/Block';
import MonacoEditor from 'components/MonacoEditor/MonacoEditor';
import Text from 'components/Text/Text';
import { AlertReceiveChannel } from 'models/alert_receive_channel/alert_receive_channel.types';
import { ChannelFilter } from 'models/channel_filter/channel_filter.types';
import { useStore } from 'state/useStore';
import { openErrorNotification } from 'utils';

import styles from './EditRegexpRouteTemplateModal.module.css';

const cx = cn.bind(styles);

interface EditRegexpRouteTemplateModalProps {
  channelFilterId: ChannelFilter['id'];
  template?: TemplateForEdit;
  alertReceiveChannelId?: AlertReceiveChannel['id'];
  onHide: () => void;
  onUpdateRoute: (values: any, channelFilterId: ChannelFilter['id'], type: number) => void;
  onOpenEditIntegrationTemplate?: (templateName: string, channelFilterId: ChannelFilter['id']) => void;
}

const EditRegexpRouteTemplateModal = observer((props: EditRegexpRouteTemplateModalProps) => {
  const { onHide, onUpdateRoute, channelFilterId, onOpenEditIntegrationTemplate, alertReceiveChannelId } = props;
  const store = useStore();

  const regexpBody = store.alertReceiveChannelStore.channelFilters[channelFilterId]?.filtering_term;

  const [regexpTemplateBody, setRegexpTemplateBody] = useState<string>(regexpBody);
  const [showErrorTemplate, setShowErrorTemplate] = useState<boolean>(false);

  const templateJinja2Body = store.alertReceiveChannelStore.channelFilters[channelFilterId]?.filtering_term_as_jinja2;

  const { alertReceiveChannelStore } = store;

  const handleRegexpBodyChange = () => {
    return debounce((value: string) => {
      setShowErrorTemplate(false);
      setRegexpTemplateBody(value);
    }, 1000);
  };

  const handleSave = useCallback(() => {
    if (!regexpTemplateBody) {
      setShowErrorTemplate(true);
      openErrorNotification('Route template body can not be empty');
    } else {
      onUpdateRoute({ ['route_template']: regexpTemplateBody }, channelFilterId, 0);

      onHide();
    }
  }, [regexpTemplateBody]);

  const handleConvertToJinja2 = useCallback(() => {
    alertReceiveChannelStore.convertRegexpTemplateToJinja2Template(channelFilterId).then((response) => {
      alertReceiveChannelStore
        .saveChannelFilter(channelFilterId, {
          filtering_term: response?.filtering_term_as_jinja2,
          filtering_term_type: 1,
        })
        .then(() => {
          alertReceiveChannelStore.updateChannelFilters(alertReceiveChannelId, true).then(() => {
            onOpenEditIntegrationTemplate('route_template', channelFilterId);
          });
        });
    });

    onHide();
  }, []);

  return (
    <Modal
      closeOnEscape
      isOpen
      onDismiss={onHide}
      title="Edit regular expression template"
      className={cx('regexp-template-editor-modal')}
    >
      <VerticalGroup spacing="lg">
        <VerticalGroup spacing="xs">
          <HorizontalGroup spacing={'xs'}>
            <Text type={'secondary'}>Regular expression</Text>
            <Tooltip
              content={'Use python style regex to filter incidents based on a expression'}
              placement={'top-start'}
            >
              <Icon name={'info-circle'} />
            </Tooltip>
          </HorizontalGroup>

          <div className={cx('regexp-template-code', { 'regexp-template-code-error': showErrorTemplate })}>
            <MonacoEditor
              value={regexpTemplateBody}
              height={'200px'}
              data={undefined}
              showLineNumbers={true}
              onChange={handleRegexpBodyChange()}
            />
          </div>
        </VerticalGroup>
        <VerticalGroup>
          <Text>Click "Convert to Jinja2" for a rich editor with debugger and additional functionality</Text>
          <Text type={'secondary'}>Your template will be saved as the jinja2 template below</Text>
        </VerticalGroup>
        <Block bordered fullWidth withBackground>
          <Text type="link">{templateJinja2Body}</Text>
        </Block>

        <HorizontalGroup justify={'flex-end'}>
          <Button variant={'secondary'} onClick={onHide}>
            Cancel
          </Button>
          <Button variant={'secondary'} onClick={() => handleConvertToJinja2()}>
            Convert to Jinja2 template
          </Button>
          <Button variant={'primary'} onClick={() => handleSave()}>
            Save
          </Button>
        </HorizontalGroup>
      </VerticalGroup>
    </Modal>
  );
});

export default EditRegexpRouteTemplateModal;
