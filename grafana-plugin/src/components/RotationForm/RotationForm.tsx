import React, { FC } from 'react';

import { IconButton, VerticalGroup, HorizontalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import Draggable from 'react-draggable';

import Modal from 'components/Modal/Modal';
import Text from 'components/Text/Text';
import UserGroups from 'components/UserGroups/UserGroups';

import styles from './RotationForm.module.css';

interface RotationFormProps {
  layerId: string;
  onHide: () => void;
  id: number | 'new';
}

const cx = cn.bind(styles);

const RotationForm: FC<RotationFormProps> = (props) => {
  const { onHide } = props;

  return (
    <Modal
      width="400px"
      title="New Rotation"
      onDismiss={onHide}
      contentElement={(props, children) => (
        <Draggable handle=".drag-handler" positionOffset={{ x: 0, y: 0 }}>
          <div {...props}>{children}</div>
        </Draggable>
      )}
    >
      <VerticalGroup>
        <div className={cx('header')}>
          <Text size="medium">Rotation 1</Text>
          <div className={cx('header-buttons')}>
            <IconButton className={cx('handle', 'drag-handler')} name="draggabledots" />
          </div>
        </div>
        <UserGroups />
        {/*<HorizontalGroup justify="end">
          <Button variant="primary">Create</Button>
        </HorizontalGroup>*/}
      </VerticalGroup>
    </Modal>
  );
};

export default RotationForm;
