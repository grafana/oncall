import { describe, expect, test } from '@jest/globals';
import { render, fireEvent, screen } from '@testing-library/react';

import Avatar from 'components/Avatar/Avatar';
import React from 'react';

import '@testing-library/jest-dom';

const MAX_PRINT = 1000000;

describe('Text', () => {
  const avatarSrc = 'http://avatar.com/'
  const avatarSizeLarge = 'large';
  const avatarSizeSmall = 'small'

  test('Usage of debug', async () => {
    render(<Avatar size="large" src={'http://avatar.com'} />);
    const image = await screen.findByTestId<HTMLImageElement>('test__avatar');

    screen.debug(image, MAX_PRINT);
  });

  test("Avatar's image points to given src attribute", async () => {
    render(<Avatar size={avatarSizeLarge} src={avatarSrc} />);
    const imageEl = await screen.findByTestId<HTMLImageElement>('test__avatar');
    expect(imageEl.src).toBe(avatarSrc);
  });

  test('Avatar appends sizing class', async () => {
    render(<Avatar size={avatarSizeSmall} src={avatarSrc} />);
    const imageEl = await screen.findByTestId<HTMLImageElement>('test__avatar');
    expect(imageEl.classList).toContain(`avatarSize-${avatarSizeSmall}`);
  });
});
