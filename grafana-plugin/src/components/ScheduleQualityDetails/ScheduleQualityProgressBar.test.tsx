import 'jest/matchMedia.ts';
import React from 'react';

import { render, screen } from '@testing-library/react';

import { ScheduleQualityProgressBar } from './ScheduleQualityProgressBar';

const NUM_STEPS = 5;
const DANGER_CLASS = 'c-progressBar__bar--danger';
const WARNING_CLASS = 'c-progressBar__bar--warning';
const SUCCESS_CLASS = 'c-progressBar__bar--primary';

describe('SourceCode', () => {
  test('It renders 0% complete', () => {
    render(<ScheduleQualityProgressBar completed={0} numTotalSteps={NUM_STEPS} />);

    expect(screen.queryAllByTestId<HTMLElement>('progressBar__bar').length).toEqual(NUM_STEPS);
    const allBars = screen.queryAllByTestId<HTMLElement>('progressBar__bar');
    allBars.forEach((bar) => expect(bar.getAttribute('style').includes('width: 0%')));
  });

  test('It renders 100% complete', () => {
    render(<ScheduleQualityProgressBar completed={100} numTotalSteps={NUM_STEPS} />);

    expect(screen.queryAllByTestId<HTMLElement>('progressBar__bar').length).toEqual(NUM_STEPS);
    const allBars = screen.queryAllByTestId<HTMLElement>('progressBar__bar');
    allBars.forEach((bar) => expect(bar.getAttribute('style').includes('width: 100%')));
  });

  test.each([0, 25, 30, 50, 65, 70, 100])('It renders at %p%', (completed) => {
    const component = render(<ScheduleQualityProgressBar completed={completed} numTotalSteps={NUM_STEPS} />);
    expect(component.container).toMatchSnapshot();
  });

  test('It renders as danger at <20% completion', () => {
    render(<ScheduleQualityProgressBar completed={15} numTotalSteps={NUM_STEPS} />);

    screen
      .queryAllByTestId<HTMLElement>('progress__bar')
      .forEach((elem) => expect(Array.from(elem.classList).includes(DANGER_CLASS)));
  });

  test('It renders as warning at <60% completion', () => {
    render(<ScheduleQualityProgressBar completed={40} numTotalSteps={NUM_STEPS} />);

    screen
      .queryAllByTestId<HTMLElement>('progress__bar')
      .forEach((elem) => expect(Array.from(elem.classList).includes(WARNING_CLASS)));
  });

  test('It renders as success at >=60% completion', () => {
    render(<ScheduleQualityProgressBar completed={60} numTotalSteps={NUM_STEPS} />);

    screen
      .queryAllByTestId<HTMLElement>('progress__bar')
      .forEach((elem) => expect(Array.from(elem.classList).includes(SUCCESS_CLASS)));
  });
});
