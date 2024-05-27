import React from 'react';

import { cx } from '@emotion/css';
import { useStyles2 } from '@grafana/ui';
import { bem } from 'styles/utils.styles';

import { getScheduleQualityProgressBarStyles } from './ScheduleQualityProgressBar.styles';

interface ProgressBarProps {
  completed: number;
  className?: string;
  numTotalSteps?: number;
}

export const ScheduleQualityProgressBar: React.FC<ProgressBarProps> = ({ className, completed, numTotalSteps }) => {
  const styles = useStyles2(getScheduleQualityProgressBarStyles);
  const classList = [styles.bar, className || ''];

  return (
    <div className={styles.wrapper}>
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
          className={cx(styles.row, bem(styles.row, 'progress'))}
          data-testid="progressBar__row"
          style={{ width: `${maxFillPerRow}%` }}
        >
          <div
            className={cx(styles.bar, getClassForCompletionLevel())}
            data-testid="progressBar__bar"
            style={{ width: `${percentWidth}%` }}
          />
        </div>
      );
    });
  }

  function getClassForCompletionLevel() {
    if (completed < 20) {
      return bem(styles.bar, 'danger');
    }
    if (completed < 60) {
      return bem(styles.bar, 'warning');
    }
    return bem(styles.bar, 'primary');
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
