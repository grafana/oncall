import React from 'react';

import cn from 'classnames/bind';

import Block from 'components/GBlock/Block';

import styles from './IntegrationBlock.module.scss';

const cx = cn.bind(styles);

interface IntegrationBlockProps {
  heading: React.ReactNode;
  content: React.ReactNode;
}

const IntegrationBlock: React.FC<IntegrationBlockProps> = (props) => {
  const { heading, content } = props;
  return (
    <div className={cx('integrationBlock')}>
      <Block bordered shadowed className={cx('integrationBlock__heading')}>
        {heading}
      </Block>
      <div className={cx('integrationBlock__content')}>{content}</div>
    </div>
  );
};

export default IntegrationBlock;
