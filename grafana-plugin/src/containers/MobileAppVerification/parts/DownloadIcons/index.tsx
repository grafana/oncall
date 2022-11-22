import React, { FC } from 'react';

import { VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';

import AppleLogoSVG from 'assets/img/brand/apple-logo.svg';
import PlayStoreLogoSVG from 'assets/img/brand/play-store-logo.svg';
import Block from 'components/GBlock/Block';
import Text from 'components/Text/Text';

import styles from './DownloadIcons.module.scss';

const cx = cn.bind(styles);

const DownloadIcons: FC = () => (
  <VerticalGroup spacing="lg">
    <Text type="primary">Download</Text>
    <Text type="primary">The Grafana IRM app is available on both the App Store and Google Play Store.</Text>
    <VerticalGroup>
      <Block hover fullWidth withBackground bordered className={cx('icon-block')}>
        <img src={AppleLogoSVG} alt="Apple" className={cx('icon')} />
        <Text type="primary" className={cx('icon-text')}>
          iOS
        </Text>
      </Block>
      <Block hover fullWidth bordered className={cx('icon-block')}>
        <img src={PlayStoreLogoSVG} alt="Play Store" className={cx('icon')} />
        <Text type="primary" className={cx('icon-text')}>
          Android
        </Text>
      </Block>
    </VerticalGroup>
  </VerticalGroup>
);

export default DownloadIcons;
