import React from 'react';

import { css } from '@emotion/css';
import { useStyles2 } from '@grafana/ui';

interface ScheduleBorderedAvatarProps {
  colors: string[];
  width: number;
  height: number;
  renderAvatar: () => JSX.Element;
  renderIcon: () => JSX.Element;
}

export const ScheduleBorderedAvatar = function ({
  colors,
  renderAvatar,
  renderIcon,
  width,
  height,
}: ScheduleBorderedAvatarProps) {
  const styles = useStyles2(getStyles);

  return <div className={styles.root}>{renderSVG()}</div>;

  function renderAvatarIcon() {
    return (
      <>
        <div className={styles.avatar}>{renderAvatar()}</div>
        <div className={styles.icon}>{renderIcon()}</div>
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
};

const getStyles = () => {
  return {
    root: css`
      position: relative;
      z-index: 1;
    `,

    avatar: css`
      position: absolute;
      top: 0;
      left: 0;
      z-index: -1;
    `,

    icon: css`
      position: relative;
      top: -8px;
    `,
  };
};
