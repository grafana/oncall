import React, { FC, useEffect } from 'react';

import { Tooltip, VerticalGroup } from '@grafana/ui';
import cn from 'classnames/bind';
import { observer } from 'mobx-react';

import { PluginLink } from 'components/PluginLink/PluginLink';
import { ScheduleQualityDetails } from 'components/ScheduleQualityDetails/ScheduleQualityDetails';
import { Tag } from 'components/Tag/Tag';
import { Text } from 'components/Text/Text';
import { TooltipBadge } from 'components/TooltipBadge/TooltipBadge';
import { Schedule, ScheduleScoreQualityResult } from 'models/schedule/schedule.types';
import { useStore } from 'state/useStore';

import styles from './ScheduleQuality.module.scss';

const cx = cn.bind(styles);

interface ScheduleQualityProps {
  schedule: Schedule;
}

export const ScheduleQuality: FC<ScheduleQualityProps> = observer(({ schedule }) => {
  const {
    scheduleStore: { getScoreQuality, relatedEscalationChains, quality },
  } = useStore();

  useEffect(() => {
    if (schedule.id) {
      getScoreQuality(schedule.id);
    }
  }, [schedule.id]);

  if (!quality) {
    return null;
  }

  const relatedScheduleEscalationChains = relatedEscalationChains[schedule.id];

  return (
    <>
      <div className={cx('root')} data-testid="schedule-quality">
        {relatedScheduleEscalationChains?.length > 0 && schedule?.number_of_escalation_chains > 0 && (
          <TooltipBadge
            borderType="success"
            icon="link"
            addPadding
            text={schedule.number_of_escalation_chains}
            tooltipTitle="Used in escalations"
            tooltipContent={
              <VerticalGroup spacing="sm">
                {relatedScheduleEscalationChains.map((escalationChain) => (
                  <div key={escalationChain.pk}>
                    <PluginLink query={{ page: 'escalations', id: escalationChain.pk }} className="link">
                      <Text type="link">{escalationChain.name}</Text>
                    </PluginLink>
                  </div>
                ))}
              </VerticalGroup>
            }
          />
        )}

        {schedule.warnings?.length > 0 && (
          <TooltipBadge
            borderType="warning"
            icon="exclamation-triangle"
            addPadding
            text={schedule.warnings.length}
            tooltipTitle="Warnings"
            tooltipContent={
              <VerticalGroup spacing="none">
                {schedule.warnings.map((warning, index) => (
                  <Text type="primary" key={index}>
                    {warning}
                  </Text>
                ))}
              </VerticalGroup>
            }
          />
        )}

        <Tooltip
          placement="bottom-start"
          interactive
          content={<ScheduleQualityDetails quality={quality} getScheduleQualityString={getScheduleQualityString} />}
        >
          <div className={cx('u-cursor-default')}>
            <Tag className={cx('tag', getTagClass())}>
              Quality: <strong>{getScheduleQualityString(quality.total_score)}</strong>
            </Tag>
          </div>
        </Tooltip>
      </div>
    </>
  );

  function getScheduleQualityString(score: number): ScheduleScoreQualityResult {
    if (score < 20) {
      return ScheduleScoreQualityResult.Bad;
    }
    if (score < 40) {
      return ScheduleScoreQualityResult.Low;
    }
    if (score < 60) {
      return ScheduleScoreQualityResult.Medium;
    }
    if (score < 80) {
      return ScheduleScoreQualityResult.Good;
    }
    return ScheduleScoreQualityResult.Great;
  }

  function getTagClass() {
    if (quality?.total_score < 20) {
      return 'tag--danger';
    }
    if (quality?.total_score < 60) {
      return 'tag--warning';
    }
    return 'tag--primary';
  }
});
