import React from 'react';

import cn from 'classnames/bind';
import { noop } from 'lodash-es';

import Block from 'components/GBlock/Block';

import styles from './IntegrationBlock.module.scss';

const cx = cn.bind(styles);

interface IntegrationBlockProps {
  className?: string;
  hasCollapsedBorder: boolean;
  heading: React.ReactNode;
  content: React.ReactNode;
  toggle?: () => void;
}

const IntegrationBlock: React.FC<IntegrationBlockProps> = ({
  heading,
  content,
  hasCollapsedBorder,
  className,
  toggle = noop,
}) => {
  return (
    <div className={cx('integrationBlock', className)}>
      {heading && (
        <Block bordered shadowed className={cx('integrationBlock__heading')} onClick={toggle}>
          {heading}
        </Block>
      )}
      {content && (
        <div
          className={cx('integrationBlock__content', {
            'integrationBlock__content--collapsedBorder': hasCollapsedBorder,
          })}
          onClick={toggle}
        >
          {content}
        </div>
      )}
    </div>
  );
};

export default IntegrationBlock;
