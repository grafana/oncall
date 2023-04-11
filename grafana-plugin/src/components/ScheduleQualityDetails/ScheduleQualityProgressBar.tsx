import React from 'react';

import cn from 'classnames/bind';

import styles from './ScheduleQualityProgressBar.module.scss';

interface ProgressBarProps {
  completed: number;
  className?: string;
  numTotalSteps?: number;
}

const cx = cn.bind(styles);

export const ScheduleQualityProgressBar: React.FC<ProgressBarProps> = ({ className, completed, numTotalSteps }) => {
  const classList = ['c-progressBar__bar', className || ''];

  return (
    <div className={cx('c-progressBar__wrapper')}>
      {!numTotalSteps && <div className={classList.join(' ')} style={{ width: `${completed}%` }} />}
      {renderSteps(numTotalSteps, completed)}
    </div>
  );

  function renderSteps(numTotalSteps: number, completed: number) {
    if (!numTotalSteps) {
      return null;
    }

    const maxFillPerRow = 100 / numTotalSteps;
    const rowFill = calculateRowFill(numTotalSteps, completed);

    return new Array(numTotalSteps).fill(0).map((_row, index) => {
      const percentWidth = rowFill[index];

      return (
        <div
          key={index}
          className={cx('c-progressBar__row', 'c-progressBar__row--progress')}
          data-testid="progressBar__row"
          style={{ width: `${maxFillPerRow}%` }}
        >
          <div
            className={cx('c-progressBar__bar', getClassForCompletionLevel())}
            data-testid="progressBar__bar"
            style={{ width: `${percentWidth}%` }}
          />
        </div>
      );
    });
  }

  function getClassForCompletionLevel() {
    if (completed < 20) {
      return 'c-progressBar__bar--danger';
    }
    if (completed < 60) {
      return 'c-progressBar__bar--warning';
    }
    return 'c-progressBar__bar--primary';
  }

  function calculateRowFill(numTotalSteps: number, completed: number): number[] {
    const fillPerRows = [];
    const maxFillPerRow = 100 / numTotalSteps;
    let leftToFill = completed;

    new Array(numTotalSteps).fill(0).forEach((_value, index) => {
      let currentFill: number;

      currentFill = leftToFill - maxFillPerRow < 0 ? leftToFill : maxFillPerRow;

      leftToFill -= maxFillPerRow;

      let percentWidth = Math.max(0, (currentFill * 100) / maxFillPerRow);
      const shouldSetMinValueInitially = completed > 0 && Math.floor(percentWidth) === 0 && !index;

      if (shouldSetMinValueInitially) {
        percentWidth = 1;
      }

      fillPerRows.push(percentWidth);
    });

    return fillPerRows;
  }
};
