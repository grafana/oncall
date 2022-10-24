import React from 'react';

import cn from 'classnames/bind';

import styles from './ScheduleBorderedAvatar.module.scss';

const cx = cn.bind(styles);

interface ScheduleBorderedAvatarProps {
  colors: string[];
  width: number;
  height: number;
  renderAvatar: () => JSX.Element;
  renderIcon: () => JSX.Element;
}

export default function ScheduleBorderedAvatar({
  colors,
  renderAvatar,
  renderIcon,
  width,
  height,
}: ScheduleBorderedAvatarProps) {
  return <div className={cx('root')}>{renderSVG()}</div>;

  function renderAvatarIcon() {
    return (
      <>
        <div className={cx('avatar')}>{renderAvatar()}</div>
        <div className={cx('icon')}>{renderIcon()}</div>
      </>
    );
  }

  function renderSVG() {
    return (
      <>
        <svg xmlns="http://www.w3.org/2000/svg" version="1.1" width={width} height={height} viewBox="-14 -8 240 230">
          <g fill="none" strokeWidth="25" transform="translate(100,100)">
            {renderColorPaths(colors)}
          </g>
        </svg>
        {renderAvatarIcon()}
      </>
    );
  }

  function renderColorPaths(colors: string[]) {
    if (!colors?.length) {
      return null;
    }

    const colorSchemeList = colors;
    if (colors.length === 1) {
      // minimum is 2 arcs to round the circle
      colorSchemeList.push(colors[0]);
    }

    const stepAngle = (2 * Math.PI) / colors.length;
    const RADIUS = 100;

    let lastX = 0;
    let lastY = -RADIUS;

    return colorSchemeList.map((_color, colorIndex) => {
      const angle = (colorIndex + 1) * stepAngle;
      const x = RADIUS * Math.sin(angle);
      const y = -RADIUS * Math.cos(angle);
      const d = `M ${lastX.toFixed(3)},${lastY.toFixed(3)} A ${RADIUS},${RADIUS} 0 0,1 ${x.toFixed(3)},${y.toFixed(3)}`;

      lastX = x;
      lastY = y;

      return <path key={colorIndex} d={d} stroke={colors[colorIndex]} />;
    });
  }
}
