import React, { FC } from 'react';

import cn from 'classnames/bind';

import { SelectOption } from 'state/types';

import { logoCoors } from './IntegrationLogo.config';

import styles from 'components/IntegrationLogo/IntegrationLogo.module.css';

interface IntegrationLogoProps {
  integration: SelectOption;
  scale: number;
}

const cx = cn.bind(styles);

const SPRITESHEET_WIDTH = 3000;
const LOGO_WIDTH = 200;

const IntegrationLogo: FC<IntegrationLogoProps> = (props) => {
  const { integration, scale } = props;
  if (!integration) {
    return null;
  }

  const coors = logoCoors[integration.value] || { x: 2, y: 14 };

  const bgStyle = {
    backgroundPosition: `-${coors?.x * LOGO_WIDTH * scale}px -${coors?.y * LOGO_WIDTH * scale}px`,
    width: LOGO_WIDTH * scale,
    height: LOGO_WIDTH * scale,
    backgroundSize: `${SPRITESHEET_WIDTH * scale}px ${SPRITESHEET_WIDTH * scale}px`,
  };

  return (
    <div className={cx('root')}>
      <div
        className={cx('bg', {
          [`bg_${integration.display_name.replace(' ', '')}`]: true,
        })}
        style={bgStyle}
      />
    </div>
  );
};

export default IntegrationLogo;
