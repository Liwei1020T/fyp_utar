import React from 'react';
import { View } from 'react-native';
import {
  feedbackEvidenceLabel,
  feedbackFeatureEntries,
  formatFeedbackScore,
  formatFeedbackWeight,
} from '../../lib/feedbackSummary';
import { formatLabel } from '../../lib/formatters';
import type { BackendFeedbackStringSummary } from '../../types/backend';
import { AppChip } from '../ui/AppChip';
import { HeroText } from '../ui/heroui';

interface FeedbackFeatureListProps {
  features: BackendFeedbackStringSummary['features'];
  showScope?: boolean;
}

export function FeedbackFeatureList({
  features,
  showScope = false,
}: FeedbackFeatureListProps) {
  return (
    <View>
      {feedbackFeatureEntries(features).map(([featureKey, feature], index) => (
        <View
          key={featureKey}
          className={`flex-row items-center justify-between gap-3 py-3 ${
            index > 0 ? 'border-t border-neutral-100' : ''
          }`}
        >
          <View className="min-w-0 flex-1">
            <View className="flex-row flex-wrap items-center gap-2">
              <HeroText className="text-sm font-semibold text-neutral-900">
                {formatLabel(featureKey)}
              </HeroText>
              <AppChip
                label={feedbackEvidenceLabel(feature.distinct_users)}
                variant={
                  feature.distinct_users >= 10
                    ? 'success'
                    : feature.distinct_users >= 3
                      ? 'info'
                      : 'warning'
                }
              />
            </View>
            <HeroText
              selectable
              className="mt-1 text-xs leading-5 text-neutral-500"
            >
              {feature.distinct_users} player
              {feature.distinct_users === 1 ? '' : 's'} ·{' '}
              {feature.booking_count} completed booking
              {feature.booking_count === 1 ? '' : 's'}
              {showScope
                ? ` · ${feature.evidence_scope === 'exact_racket_model' ? 'Exact model' : 'Global fallback'}`
                : ''}
            </HeroText>
          </View>
          <View className="items-end">
            <HeroText selectable className="text-base font-bold text-neutral-950">
              {formatFeedbackScore(feature.score)}
            </HeroText>
            <HeroText selectable className="mt-1 text-[11px] text-neutral-500">
              {formatFeedbackWeight(feature.weight)} influence
            </HeroText>
          </View>
        </View>
      ))}
    </View>
  );
}
