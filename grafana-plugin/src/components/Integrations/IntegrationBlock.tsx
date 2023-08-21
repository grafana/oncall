import React from 'react';

import cn from 'classnames/bind';
import { noop } from 'lodash-es';

import Block from 'components/GBlock/Block';

import styles from './IntegrationBlock.module.scss';

const cx = cn.bind(styles);

interface IntegrationBlockProps {
  className?: string;
  noContent: boolean;
  heading: React.ReactNode;
  content: React.ReactNode;
  toggle?: () => void;
}

const IntegrationBlock: React.FC<IntegrationBlockProps> = ({
  heading,
  content,
  noContent,
  className,
  toggle = noop,
}) => {
  return (
    <div className={cx('integrationBlock', className)}>
      {heading && (
        <Block
          bordered
          shadowed
          className={cx('integrationBlock__heading', {
            'integrationBlock__heading--noBorderBottom': !noContent,
          })}
          onClick={toggle}
        >
          {heading}
        </Block>
      )}
      {content && (
        <div className={cx('integrationBlock__content')} onClick={toggle}>
          {content}
        </div>
      )}
    </div>
  );
};

export default IntegrationBlock;
