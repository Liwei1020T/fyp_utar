import React, { useCallback, useState } from 'react';
import { useFocusEffect, useLocalSearchParams, useRouter } from 'expo-router';
import { View } from 'react-native';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { HeroText } from '../../../components/ui/heroui';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { formatDateTime } from '../../../lib/formatters';
import { BackendApiError, backendApi } from '../../../services/backendApi';
import {
  useBackendAccessToken,
  useCurrentUser,
} from '../../../store/appStore';
import type { BackendAdminFeedback } from '../../../types/backend';

function ratingLabel(value: number | null) {
  return value == null ? 'Not rated' : `${value}/5`;
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <View className="flex-row items-center justify-between gap-4 border-b border-neutral-100 py-3 last:border-b-0">
      <HeroText className="text-sm text-neutral-600">{label}</HeroText>
      <HeroText className="max-w-[62%] text-right text-sm font-semibold text-neutral-950">
        {value}
      </HeroText>
    </View>
  );
}

export default function AdminFeedbackDetailScreen() {
  const router = useRouter();
  const { bookingId } = useLocalSearchParams<{ bookingId?: string }>();
  const token = useBackendAccessToken();
  const user = useCurrentUser();
  const [feedback, setFeedback] = useState<BackendAdminFeedback | null>(null);
  const [isLoading, setIsLoading] = useState(Boolean(token && bookingId));
  const [error, setError] = useState<string | null>(null);

  const loadFeedback = useCallback(async () => {
    if (!token || user?.role !== 'admin' || !bookingId) {
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const response = await backendApi.adminListFeedback(token, {
        booking_id: bookingId,
        limit: 1,
      });
      const record = response.items[0] ?? null;
      if (!record) {
        setFeedback(null);
        setError('Feedback record not found.');
        return;
      }
      setFeedback(record);
    } catch (loadError) {
      setFeedback(null);
      setError(
        loadError instanceof BackendApiError
          ? loadError.message
          : 'Failed to load feedback detail.',
      );
    } finally {
      setIsLoading(false);
    }
  }, [bookingId, token, user?.role]);

  useFocusEffect(
    useCallback(() => {
      void loadFeedback();
    }, [loadFeedback]),
  );

  if (!user || user.role !== 'admin') return null;

  if (isLoading) {
    return (
      <AppScreen
        tone="admin"
        headerVariant="flow"
        title="Feedback detail"
        subtitle="Loading the player's complete evaluation."
        showBackButton
        onBackPress={() => router.back()}
      >
        <AppCard variant="subtle" className="mt-6" padding="md">
          <HeroText className="text-sm leading-6 text-neutral-600">
            Loading feedback record...
          </HeroText>
        </AppCard>
      </AppScreen>
    );
  }

  if (!feedback || error) {
    return (
      <AppScreen
        tone="admin"
        headerVariant="flow"
        title="Feedback unavailable"
        subtitle="The selected feedback record could not be loaded."
        showBackButton
        onBackPress={() => router.back()}
      >
        <AppCard variant="subtle" className="mt-6" padding="md">
          <HeroText className="text-sm leading-6 text-red-700">
            {error ?? 'Feedback record not found.'}
          </HeroText>
          <AppButton
            label="Back to feedback"
            variant="outline"
            className="mt-4"
            onPress={() => router.replace('/admin/feedback')}
          />
        </AppCard>
      </AppScreen>
    );
  }

  const writtenFeedback = [
    { label: 'Player comment', value: feedback.comment },
    { label: 'String experience', value: feedback.string_feedback },
    { label: 'Service experience', value: feedback.service_feedback },
  ].filter((entry) => entry.value);

  return (
    <AppScreen
      tone="admin"
      headerVariant="flow"
      title="Feedback detail"
      subtitle={`Full player evaluation for ${feedback.order_code}.`}
      showBackButton
      onBackPress={() => router.back()}
    >
      <AppCard variant="highlighted" padding="lg">
        <View className="flex-row items-start justify-between gap-4">
          <View className="min-w-0 flex-1">
            <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary-700">
              Player feedback
            </HeroText>
            <HeroText className="mt-2 text-xl font-bold text-neutral-950">
              {feedback.string_name}
            </HeroText>
            <HeroText className="mt-1 text-sm text-neutral-600">
              {feedback.customer_username} · {feedback.order_code}
            </HeroText>
          </View>
          <AppChip label={`${feedback.rating}/5`} variant="success" size="md" />
        </View>
        <HeroText className="mt-4 text-xs leading-5 text-neutral-500">
          Submitted {formatDateTime(feedback.created_at)}
        </HeroText>
      </AppCard>

      <AppSection eyebrow="Detailed ratings" title="Recorded experience">
        <AppCard variant="elevated" padding="md">
          <DetailRow label="Overall service" value={ratingLabel(feedback.rating)} />
          <DetailRow
            label="Recommendation relevance"
            value={ratingLabel(feedback.recommendation_relevance)}
          />
          <DetailRow
            label="String satisfaction"
            value={ratingLabel(feedback.string_satisfaction)}
          />
          <DetailRow
            label="Tension satisfaction"
            value={ratingLabel(feedback.tension_satisfaction)}
          />
          <DetailRow label="Comfort" value={ratingLabel(feedback.comfort)} />
          <DetailRow label="Control" value={ratingLabel(feedback.control)} />
          <DetailRow label="Repulsion" value={ratingLabel(feedback.repulsion)} />
          <DetailRow
            label="Would use again"
            value={
              feedback.would_use_again == null
                ? 'Not answered'
                : feedback.would_use_again
                  ? 'Yes'
                  : 'No'
            }
          />
        </AppCard>
      </AppSection>

      <AppSection eyebrow="Written feedback" title="Player comments">
        {writtenFeedback.length > 0 ? (
          <View className="gap-3">
            {writtenFeedback.map(({ label, value }) => (
              <AppCard key={label} variant="elevated" padding="md">
                <HeroText className="text-sm font-semibold text-neutral-950">
                  {label}
                </HeroText>
                <HeroText className="mt-2 text-sm leading-6 text-neutral-700">
                  {value}
                </HeroText>
              </AppCard>
            ))}
          </View>
        ) : (
          <AppCard variant="subtle" padding="md">
            <HeroText className="text-sm leading-6 text-neutral-600">
              No written comments were submitted.
            </HeroText>
          </AppCard>
        )}
      </AppSection>

      <AppSection eyebrow="Related booking" title="Order context">
        <AppCard variant="subtle" padding="md">
          <DetailRow label="Order" value={feedback.order_code} />
          <DetailRow label="String" value={feedback.string_name} />
          <AppButton
            label="Open related booking"
            variant="outline"
            className="mt-4"
            onPress={() => router.push(`/admin/bookings/${feedback.booking_id}`)}
          />
        </AppCard>
      </AppSection>

      <AppButton
        label="Back to feedback"
        variant="outline"
        className="mt-2"
        onPress={() => router.replace('/admin/feedback')}
      />
    </AppScreen>
  );
}
