import React from 'react';

import { render, screen } from '@testing-library/react';

import Avatar from 'components/Avatar/Avatar';

describe('Avatar', () => {
  const avatarSrc = 'http://avatar.com/';
  const avatarSizeLarge = 'large';
  const avatarSizeSmall = 'small';

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
