import React, { useCallback, useState } from 'react';

import { Button, HorizontalGroup, Icon, IconButton, TextArea, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import Draggable from 'react-draggable';

import Modal from 'components/Modal/Modal';
import Text from 'components/Text/Text';
import TooltipBadge from 'components/TooltipBadge/TooltipBadge';
import { WithPermissionControlTooltip } from 'containers/WithPermissionControl/WithPermissionControlTooltip';
import { ShiftSwap } from 'models/schedule/schedule.types';
import { useStore } from 'state/useStore';
import { UserActions } from 'utils/authorization';

import styles from './RotationForm.module.css';

const cx = cn.bind(styles);

interface ShiftSwapFormProps {
  params: Partial<ShiftSwap>;

  onCreate: (params: Partial<ShiftSwap>) => void;
  onHide: () => void;
}

const ShiftSwapForm = (props: ShiftSwapFormProps) => {
  const { onCreate, onHide, params: defaultParams } = props;

  const [params] = useState(defaultParams);

  const store = useStore();
  const {} = store;

  const allowDelete = true;

  console.log('params', params);

  const handleCreate = useCallback(() => {
    onHide();
    onCreate(params);
  }, [params]);

  return (
    <Modal
      top="0"
      isOpen
      width="430px"
      onDismiss={onHide}
      contentElement={(props, children) => (
        <Draggable handle=".drag-handler" defaultClassName={cx('draggable')} positionOffset={{ x: 0, y: 200 }}>
          <div {...props}>{children}</div>
        </Draggable>
      )}
    >
      <div className={cx('root')}>
        <VerticalGroup>
          <HorizontalGroup justify="space-between">
            <HorizontalGroup spacing="sm">
              <Text.Title level={5} editable>
                Shift swap details
              </Text.Title>
            </HorizontalGroup>
            <HorizontalGroup>
              <IconButton
                disabled={!allowDelete}
                variant="secondary"
                tooltip="Delete"
                name="trash-alt"
                //onClick={() => setShowDeleteRotationConfirmation(true)}
              />
              <IconButton variant="secondary" className={cx('drag-handler')} name="draggabledots" />
              <IconButton name="times" variant="secondary" tooltip="Close" onClick={onHide} />
            </HorizontalGroup>
          </HorizontalGroup>

          <HorizontalGroup align="flex-start">
            <div className={cx('details-icon')}>
              <Icon className={cx('icon')} name="info-circle" />
            </div>
            <VerticalGroup>
              <Text type="primary">Current status and deadline</Text>
              <HorizontalGroup>
                <TooltipBadge borderType="warning" text="Open" />
                <TooltipBadge borderType="primary" text="? till deadline" />
              </HorizontalGroup>
            </VerticalGroup>
          </HorizontalGroup>

          <HorizontalGroup align="flex-start">
            <div className={cx('details-icon')}>
              <Icon className={cx('icon')} name="user" />
            </div>
            <VerticalGroup>
              <Text type="primary">Swap pair</Text>
              <Text>{params.beneficiary}</Text>
            </VerticalGroup>
          </HorizontalGroup>

          <HorizontalGroup align="flex-start">
            <div className={cx('details-icon')}>
              <Icon className={cx('icon')} name="arrows-h" />
            </div>
            <VerticalGroup>
              <Text type="primary">Swap settings</Text>
              <Text>
                from {params.swap_start} to {params.swap_end}
              </Text>
            </VerticalGroup>
          </HorizontalGroup>

          <HorizontalGroup align="flex-start">
            <div className={cx('details-icon')}>
              <Icon className={cx('icon')} name="text-fields" />
            </div>
            <VerticalGroup>
              <Text type="primary">Description</Text>
              <div style={{ width: '100%' }}>
                <TextArea />
              </div>
            </VerticalGroup>
          </HorizontalGroup>

          <HorizontalGroup justify="space-between">
            <Text type="secondary">Blabla</Text>
            <HorizontalGroup>
              <WithPermissionControlTooltip userAction={UserActions.SchedulesWrite}>
                <Button variant="secondary" onClick={handleCreate}>
                  Request
                </Button>
              </WithPermissionControlTooltip>
            </HorizontalGroup>
          </HorizontalGroup>
        </VerticalGroup>
      </div>
    </Modal>
  );
};

export default ShiftSwapForm;
