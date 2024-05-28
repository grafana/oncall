import React, { FC } from 'react';

import { cx } from '@emotion/css';
import { VerticalGroup, useStyles2 } from '@grafana/ui';

import { Block } from 'components/GBlock/Block';
import { Text } from 'components/Text/Text';

import { getCardButtonStyles } from './CardButton.styles';

interface CardButtonProps {
  icon: React.ReactElement;
  description: string;
  title: string;
  selected: boolean;
  onClick: (selected: boolean) => void;
}

export const CardButton: FC<CardButtonProps> = (props) => {
  const { icon, description, title, selected, onClick } = props;

  const styles = useStyles2(getCardButtonStyles);

  return (
    <Block
      onClick={() => onClick(!selected)}
      withBackground
      className={cx(styles.root, { [styles.rootSelected]: selected })}
      data-testid="test__cardButton"
    >
      <div className={styles.icon}>{icon}</div>
      <div className={styles.meta}>
        <VerticalGroup spacing="xs">
          <Text type="secondary">{description}</Text>
          <Text.Title level={1}>{title}</Text.Title>
        </VerticalGroup>
      </div>
    </Block>
  );
};
