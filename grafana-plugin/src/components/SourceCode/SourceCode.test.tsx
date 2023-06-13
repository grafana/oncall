import 'jest/matchMedia.ts';
import React from 'react';

import { render, screen } from '@testing-library/react';

import SourceCode from './SourceCode';

describe('SourceCode', () => {
  test("SourceCode doesn't render clipboard for [showCopyToClipboard=false]", () => {
    render(<SourceCode showCopyToClipboard={false} />);
    const codeEl = screen.queryByRole<HTMLElement>('code');
    expect(codeEl).toBeNull();
  });

  test('SourceCode renders clipboard for [showCopyToClipboard=true]', () => {
    render(<SourceCode showCopyToClipboard />);
    const codeEl = screen.queryByRole<HTMLElement>('code');
    expect(codeEl).toBeDefined();
  });

  test('SourceCode displays just copy icon for [showClipboardIconOnly=true]', () => {
    render(<SourceCode showClipboardIconOnly />);
    expect(screen.queryByTestId<HTMLElement>('test__copyIcon')).toBeDefined();
    expect(screen.queryByTestId<HTMLElement>('test__copyIconWithText')).toBeNull();
  });

  test('SourceCode displays copy icon and text for [showClipboardIconOnly=false]', () => {
    render(<SourceCode />);
    expect(screen.queryByTestId<HTMLElement>('test__copyIcon')).toBeNull();
    expect(screen.queryByTestId<HTMLElement>('test__copyIconWithText')).toBeDefined();
  });
});
