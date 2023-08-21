import React, { FC } from 'react';

import { VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';

import AppleLogoSVG from 'assets/img/apple-logo.svg';
import PlayStoreLogoSVG from 'assets/img/play-store-logo.svg';
import Block from 'components/GBlock/Block';
import Text from 'components/Text/Text';

import styles from './DownloadIcons.module.scss';

const cx = cn.bind(styles);

const DownloadIcons: FC = () => (
  <VerticalGroup spacing="lg">
    <Text type="primary" strong>
      Download
    </Text>
    <Text type="primary">The Grafana OnCall app is available on both the App Store and Google Play Store.</Text>
    <VerticalGroup>
      <a
        style={{ width: '100%' }}
        href="https://apps.apple.com/us/app/grafana-oncall-preview/id1669759048"
        target="_blank"
        rel="noreferrer"
      >
        <Block hover fullWidth withBackground bordered className={cx('icon-block')}>
          <img src={AppleLogoSVG} alt="Apple" className={cx('icon')} />
          <Text type="primary" className={cx('icon-text')}>
            iOS
          </Text>
        </Block>
      </a>
      <a
        style={{ width: '100%' }}
        href="https://play.google.com/store/apps/details?id=com.grafana.oncall.prod"
        target="_blank"
        rel="noreferrer"
      >
        <Block hover fullWidth bordered className={cx('icon-block')}>
          <img src={PlayStoreLogoSVG} alt="Play Store" className={cx('icon')} />
          <Text type="primary" className={cx('icon-text')}>
            Android
          </Text>
        </Block>
      </a>
    </VerticalGroup>
  </VerticalGroup>
);

export default DownloadIcons;
