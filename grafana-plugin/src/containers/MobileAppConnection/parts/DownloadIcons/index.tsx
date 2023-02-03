import React, { FC } from 'react';

import { VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';

import AppleLogoSVG from 'assets/img/brand/apple-logo.svg';
import PlayStoreLogoSVG from 'assets/img/brand/play-store-logo.svg';
import Block from 'components/GBlock/Block';
import Tag from 'components/Tag/Tag';
import Text from 'components/Text/Text';
import { COLOR_PRIMARY } from 'utils/consts';

import styles from './DownloadIcons.module.scss';

const cx = cn.bind(styles);

const DownloadIcons: FC = () => (
  <VerticalGroup spacing="lg">
    <Text type="primary" strong>
      Download
    </Text>
    <Text type="primary">The Grafana IRM app is available on both the App Store and Google Play Store.</Text>
    <VerticalGroup>
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
      <Block hover fullWidth withBackground bordered className={cx('icon-block')}>
        <img src={AppleLogoSVG} alt="Apple" className={cx('icon')} />
        <Text type="primary" className={cx('icon-text')}>
          iOS
        </Text>
        <Tag color={COLOR_PRIMARY} className={cx('icon-tag')}>
          Coming Soon
        </Tag>
      </Block>
    </VerticalGroup>
  </VerticalGroup>
);

export default DownloadIcons;
