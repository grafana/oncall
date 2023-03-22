import React, { FC } from 'react';

import { VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';

import Block from 'components/GBlock/Block';
import Text from 'components/Text/Text';

import styles from './CardButton.module.css';

interface CardButtonProps {
  icon: React.ReactElement;
  description: string;
  title: string;
  selected: boolean;
  onClick: (selected: boolean) => void;
}

const cx = cn.bind(styles);

const CardButton: FC<CardButtonProps> = (props) => {
  const { icon, description, title, selected, onClick } = props;

  return (
    <Block
      onClick={() => onClick(!selected)}
      withBackground
      className={cx('root', { root_selected: selected })}
      data-testid="test__cardButton"
    >
      <div className={cx('icon')}>{icon}</div>
      <div className={cx('meta')}>
        <VerticalGroup spacing="xs">
          <Text type="secondary" className={cx('description')}>
            {description}
          </Text>
          <Text.Title level={1} className={cx('title')}>
            {title}
          </Text.Title>
        </VerticalGroup>
      </div>
    </Block>
  );
};

export default CardButton;
