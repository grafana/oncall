import React from 'react';

import { cx } from '@emotion/css';
import { useStyles2 } from '@grafana/ui';
import { noop } from 'lodash-es';
import { bem } from 'styles/utils.styles';

import { Block } from 'components/GBlock/Block';

import { getIntegrationBlockStyles } from './IntegrationBlock.styles';

interface IntegrationBlockProps {
  className?: string;
  noContent?: boolean;
  heading: React.ReactNode;
  content?: React.ReactNode;
  toggle?: () => void;
}

export const IntegrationBlock: React.FC<IntegrationBlockProps> = ({
  heading,
  content,
  noContent,
  className,
  toggle = noop,
}) => {
  const styles = useStyles2(getIntegrationBlockStyles);

  return (
    <div className={cx(className)}>
      {heading && (
        <Block
          bordered
          shadowed
          className={cx(styles.integrationBlockHeading, {
            [bem(styles.integrationBlockHeading, 'noBorderBottom')]: !noContent,
          })}
          onClick={toggle}
        >
          {heading}
        </Block>
      )}
      {content && (
        <div className={styles.integrationBlockContent} onClick={toggle}>
          {content}
        </div>
      )}
    </div>
  );
};
