import React from 'react';
import styles from './IntegrationBlockItem.module.scss';
import cn from 'classnames/bind';

const cx = cn.bind(styles);

interface IntegrationBlockItemProps {
  children: React.ReactNode;
}

const IntegrationBlockItem: React.FC<IntegrationBlockItemProps> = (props) => {
  return (
    <div className={cx('blockItem')}>
      <div className={cx('blockItem__leftDelimitator')} />
      <div className={cx('blockItem__content')}>{props.children}</div>
    </div>
  );
};

export default IntegrationBlockItem;
