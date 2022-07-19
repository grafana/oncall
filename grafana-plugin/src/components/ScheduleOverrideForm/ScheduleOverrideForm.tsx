import React, { FC } from 'react';
import cn from 'classnames/bind';

import styles from './ScheduleOverrideForm.module.css';

interface ScheduleOverrideFormProps {

}

const cx = cn.bind(styles);

const ScheduleOverrideForm: FC<ScheduleOverrideFormProps> = props => {
    const { } = props;

    return (
        <div className={cx('root')} />
    );
};

export default ScheduleOverrideForm;
