import React from 'react';

import cn from 'classnames/bind';

import styles from './IntegrationBlockItem.module.scss';

const cx = cn.bind(styles);

interface IntegrationBlockItemProps {
  children: React.ReactNode;
}

const IntegrationBlockItem: React.FC<IntegrationBlockItemProps> = (props) => {
  return (
    <div className={cx('blockItem')} data-testid="integration-block-item">
      <div className={cx('blockItem__leftDelimitator')} />
      <div className={cx('blockItem__content')}>{props.children}</div>
    </div>
  );
};

export default IntegrationBlockItem;
