import React from 'react';

import cn from 'classnames/bind';

import styles from './ColorfulUserCircle.module.scss';

const cx = cn.bind(styles);

export default function ColorfulUserCircle({
  colors,
  renderAvatar,
  renderIcon,
  width,
  height,
}: {
  colors: string[];
  width: number;
  height: number;
  renderAvatar: () => JSX.Element;
  renderIcon: () => JSX.Element;
}) {
  return <div className={cx('root')}>{colors?.length ? renderSVG() : renderAvatarIcon()}</div>;

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
        <svg xmlns="http://www.w3.org/2000/svg" version="1.1" width={width} height={height} viewBox="-10 -10 220 220">
          <g fill="none" strokeWidth="15" transform="translate(100,100)">
            {renderColorPaths(colors)}
          </g>
        </svg>
        {renderAvatarIcon()}
      </>
    );
  }

  function renderColorPaths(colors: string[]) {
    const colorSchemeList = colors;
    if (colors.length === 1) {colorSchemeList.push(colors[0]);}

    const stepAngle = (2 * Math.PI) / colors.length;
    const radius = 100;

    let lastX = 0;
    let lastY = -radius;

    return colorSchemeList.map((_color, colorIndex) => {
      const angle = (colorIndex + 1) * stepAngle;
      const x = radius * Math.sin(angle);
      const y = -radius * Math.cos(angle);
      const d = `M ${lastX.toFixed(3)},${lastY.toFixed(3)} A 100,100 0 0,1 ${x.toFixed(3)},${y.toFixed(3)}`;

      lastX = x;
      lastY = y;

      return <path d={d} stroke={colors[colorIndex]} />;
    });
  }
}
