import React, { FC, useState } from 'react';

import { Button, Drawer, HorizontalGroup, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';

import EscalationVariants from 'components/EscalationVariants/EscalationVariants';
import GForm from 'components/GForm/GForm';
import { FormItem, FormItemType } from 'components/GForm/GForm.types';

import styles from './ManualAlertGroup.module.css';

interface ManualAlertGroupProps {
  onHide: () => void;
}

const cx = cn.bind(styles);

const manualAlertFormConfig: { name: string; fields: FormItem[] } = {
  name: 'Manual Alert Group',
  fields: [
    {
      name: 'title',
      type: FormItemType.Input,
      label: 'Title',
      validation: { required: true },
    },
    {
      name: 'description',
      type: FormItemType.TextArea,
      label: 'Describe what is going on',
    },
  ],
};

const handleSubmit = () => {
  console.log('SUBMIT');
};

const ManualAlertGroup: FC<ManualAlertGroupProps> = (props) => {
  const { onHide } = props;
  const [showEscalationVariants, setShowEscalationVariants] = useState(false);

  const handleOpenEscalationVariants = (status) => {
    if (status) {
      setShowEscalationVariants(false);
    } else {
      setShowEscalationVariants(true);
    }
  };

  return (
    <>
      <Drawer scrollableContent title="Create an alert group" onClose={onHide} closeOnMaskClick>
        <div className={cx('content')}>
          <VerticalGroup>
            <div>
              <div className={cx('assign-responders-button')}>
                <Button variant="secondary">Escalate to</Button>
                <Button
                  variant="secondary"
                  onClick={() => handleOpenEscalationVariants(showEscalationVariants)}
                  icon="angle-down"
                  style={{ width: '24px' }}
                ></Button>
              </div>
              {showEscalationVariants && <EscalationVariants onHide={() => setShowEscalationVariants(false)} />}
            </div>
            <GForm form={manualAlertFormConfig} data={{}} onSubmit={handleSubmit} />
          </VerticalGroup>
        </div>
        <HorizontalGroup>
          <Button variant="secondary">Cancel</Button>
          <Button>Create</Button>
        </HorizontalGroup>
      </Drawer>
    </>
  );
};

export default ManualAlertGroup;
