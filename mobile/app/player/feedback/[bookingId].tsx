import React, { useCallback, useState } from 'react';
import { Pressable, View } from 'react-native';
import {
  useFocusEffect,
  useLocalSearchParams,
  useRouter,
} from 'expo-router';
import { Star } from 'lucide-react-native';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppInput } from '../../../components/ui/AppInput';
import { HeroText } from '../../../components/ui/heroui';
import { appChromeColors } from '../../../components/ui/theme';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import {
  formatBookingOrderCode,
  formatBookingStatus,
} from '../../../lib/formatters';
import {
  useAppStore,
  useBackendAccessToken,
  useBookings,
} from '../../../store/appStore';
import { BackendApiError, backendApi } from '../../../services/backendApi';
import {
  mapBackendBookingToBooking,
  mapBackendFeedbackToBookingFeedback,
} from '../../../services/backendMappers';
import type {
  Booking,
  BookingFeedback,
} from '../../../types/domain';
import type { BackendUpdateFeedbackPayload } from '../../../types/backend';
import { showAlert } from '../../../lib/alerts';

const DETAIL_RATINGS = [
  ['recommendationRelevance', 'Recommendation relevance'],
  ['stringSatisfaction', 'String satisfaction'],
  ['tensionSatisfaction', 'Tension satisfaction'],
  ['comfort', 'Comfort'],
  ['control', 'Control'],
  ['repulsion', 'Repulsion'],
] as const;

type DetailRatingKey = (typeof DETAIL_RATINGS)[number][0];

const DETAIL_API_KEYS: Record<DetailRatingKey, string> = {
  recommendationRelevance: 'recommendation_relevance',
  stringSatisfaction: 'string_satisfaction',
  tensionSatisfaction: 'tension_satisfaction',
  comfort: 'comfort',
  control: 'control',
  repulsion: 'repulsion',
};

function emptyDetailRatings(): Record<DetailRatingKey, number | null> {
  return Object.fromEntries(DETAIL_RATINGS.map(([key]) => [key, null])) as Record<
    DetailRatingKey,
    number | null
  >;
}

const RATING_VALUES = [1, 2, 3, 4, 5];

function StarRating({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number | null;
  onChange: (value: number) => void;
}) {
  return (
    <View className="gap-2">
      <View className="flex-row items-center justify-between gap-3">
        <HeroText className="text-sm font-semibold text-neutral-900">
          {label}
        </HeroText>
        <HeroText
          className={
            value == null
              ? 'text-sm text-neutral-500'
              : 'text-sm font-bold text-neutral-950'
          }
        >
          {value == null ? 'Not rated' : `${value}/5`}
        </HeroText>
      </View>
      <View
        accessibilityRole="radiogroup"
        accessibilityLabel={`${label}, ${value == null ? 'not rated' : `${value} out of 5`}`}
        className="flex-row items-center justify-between rounded-[14px] border border-primary-200 bg-white px-2 py-1"
      >
        {RATING_VALUES.map((score) => {
          const isFilled = value != null && score <= value;
          return (
            <Pressable
              key={score}
              accessibilityRole="radio"
              accessibilityLabel={`${label}: ${score} star${score === 1 ? '' : 's'}`}
              accessibilityState={{ checked: value === score }}
              className="min-h-[48px] min-w-[48px] items-center justify-center rounded-[10px] active:opacity-70"
              hitSlop={4}
              onPress={() => onChange(score)}
            >
              <Star
                size={28}
                color={isFilled ? appChromeColors.accent : appChromeColors.textMuted}
                fill={isFilled ? appChromeColors.accent : 'transparent'}
                strokeWidth={2}
              />
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

export default function FeedbackScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ bookingId?: string }>();
  const bookingId = params.bookingId;
  const token = useBackendAccessToken();
  const bookings = useBookings();
  const upsertLiveBooking = useAppStore((state) => state.upsertLiveBooking);
  const [resolvedBooking, setResolvedBooking] = useState<Booking | null>(null);
  const [existingFeedback, setExistingFeedback] =
    useState<BookingFeedback | null>(null);
  const [rating, setRating] = useState<number | null>(null);
  const [detailRatings, setDetailRatings] = useState(emptyDetailRatings);
  const [wouldUseAgain, setWouldUseAgain] = useState<boolean | null>(null);
  const [comment, setComment] = useState('');
  const [stringFeedback, setStringFeedback] = useState('');
  const [serviceFeedback, setServiceFeedback] = useState('');
  const [isLoading, setIsLoading] = useState(Boolean(token && bookingId));
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [dirtyFields, setDirtyFields] = useState<Set<string>>(new Set());

  const refreshFeedback = useCallback(async () => {
    if (!bookingId) {
      setIsLoading(false);
      return;
    }
    if (!token) {
      setResolvedBooking(null);
      setExistingFeedback(null);
      setLoadError(null);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setLoadError(null);
    try {
      const response = await backendApi.fetchBooking(token, bookingId);
      const mappedBooking = mapBackendBookingToBooking(response);
      setResolvedBooking(mappedBooking);
      upsertLiveBooking(mappedBooking);

      if (mappedBooking.status !== 'completed') {
        setExistingFeedback(null);
        return;
      }

      const feedback = await backendApi.fetchBookingFeedback(token, bookingId);
      setExistingFeedback(
        feedback ? mapBackendFeedbackToBookingFeedback(feedback) : null,
      );
    } catch (error) {
      setLoadError(
        error instanceof BackendApiError
          ? error.message
          : 'Failed to load this booking feedback.',
      );
    } finally {
      setIsLoading(false);
    }
  }, [bookingId, token, upsertLiveBooking]);

  useFocusEffect(
    useCallback(() => {
      void refreshFeedback();
    }, [refreshFeedback]),
  );

  const booking =
    resolvedBooking ?? bookings.find((item) => item.id === bookingId);
  const orderCode = booking
    ? booking.orderCode ?? formatBookingOrderCode(booking.id)
    : bookingId
      ? formatBookingOrderCode(bookingId)
      : 'recent booking';

  const markDirty = (field: string) =>
    setDirtyFields((current) => new Set(current).add(field));

  const beginEdit = () => {
    if (!existingFeedback) return;
    setRating(existingFeedback.rating);
    setDetailRatings({
      recommendationRelevance: existingFeedback.recommendationRelevance ?? null,
      stringSatisfaction: existingFeedback.stringSatisfaction ?? null,
      tensionSatisfaction: existingFeedback.tensionSatisfaction ?? null,
      comfort: existingFeedback.comfort ?? null,
      control: existingFeedback.control ?? null,
      repulsion: existingFeedback.repulsion ?? null,
    });
    setWouldUseAgain(existingFeedback.wouldUseAgain ?? null);
    setComment(existingFeedback.comment ?? '');
    setStringFeedback(existingFeedback.stringFeedback ?? '');
    setServiceFeedback(existingFeedback.serviceFeedback ?? '');
    setDirtyFields(new Set());
    setIsEditing(true);
  };

  const submitFeedback = async () => {
    if (!booking || booking.status !== 'completed') {
      setSubmitError('Feedback is only available for a completed booking.');
      return;
    }
    if (!token) {
      setSubmitError('A live player login is required to submit feedback.');
      return;
    }
    if (!existingFeedback && rating == null) {
      setSubmitError('Select the overall stringing service rating.');
      return;
    }
    if (existingFeedback && dirtyFields.size === 0) {
      setSubmitError('Change at least one feedback field before saving.');
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);
    try {
      const allValues = {
        rating,
        recommendation_relevance: detailRatings.recommendationRelevance,
        string_satisfaction: detailRatings.stringSatisfaction,
        tension_satisfaction: detailRatings.tensionSatisfaction,
        comfort: detailRatings.comfort,
        control: detailRatings.control,
        repulsion: detailRatings.repulsion,
        would_use_again: wouldUseAgain,
        comment: comment.trim() || null,
        string_feedback: stringFeedback.trim() || null,
        service_feedback: serviceFeedback.trim() || null,
      };
      const response = existingFeedback
        ? await backendApi.updateBookingFeedback(
            token,
            booking.id,
            Object.fromEntries(
              Object.entries(allValues).filter(([key]) => dirtyFields.has(key)),
            ) as BackendUpdateFeedbackPayload,
          )
        : await backendApi.createBookingFeedback(token, booking.id, {
            ...allValues,
            rating: rating as number,
          });
      setExistingFeedback(mapBackendFeedbackToBookingFeedback(response));
      setIsEditing(false);
      setDirtyFields(new Set());
      const alertTitle = existingFeedback
        ? 'Feedback updated'
        : 'Feedback submitted';
      const alertMessage = existingFeedback
        ? 'Your changes have been saved.'
        : 'Thank you. Your feedback has been saved.';
      showAlert(alertTitle, alertMessage);
    } catch (error) {
      setSubmitError(
        error instanceof BackendApiError
          ? error.message
          : 'Failed to submit feedback.',
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!bookingId) {
    return (
      <AppScreen
        title="Feedback unavailable"
        subtitle="No booking was selected."
        showBackButton
        onBackPress={() => router.back()}
      >
        <AppButton
          label="Back to bookings"
          className="mt-8"
          onPress={() => router.replace('/player/bookings')}
        />
      </AppScreen>
    );
  }

  if (isLoading) {
    return (
      <AppScreen
        title="Loading feedback"
        subtitle={`Checking booking ${orderCode} and its feedback record.`}
        showBackButton
        onBackPress={() => router.back()}
      >
        <AppCard variant="subtle" className="mt-8" padding="md">
          <HeroText className="text-sm leading-6 text-neutral-600">
            Loading the latest completed-booking record...
          </HeroText>
        </AppCard>
      </AppScreen>
    );
  }

  if (loadError) {
    return (
      <AppScreen
        title="Unable to load feedback"
        subtitle={`Booking ${orderCode} could not be verified.`}
        showBackButton
        onBackPress={() => router.back()}
      >
        <AppCard
          variant="subtle"
          className="mt-8 border border-red-100"
          padding="md"
        >
          <HeroText className="text-sm font-medium text-red-600">
            {loadError}
          </HeroText>
          <View className="mt-4 gap-3">
            <AppButton
              label="Retry"
              variant="outline"
              onPress={() => void refreshFeedback()}
            />
            <AppButton
              label="Back to bookings"
              onPress={() => router.replace('/player/bookings')}
            />
          </View>
        </AppCard>
      </AppScreen>
    );
  }

  if (!booking) {
    return (
      <AppScreen
        title="Booking not found"
        subtitle="This feedback link is invalid or the booking is unavailable."
        showBackButton
        onBackPress={() => router.back()}
      >
        <AppCard variant="subtle" className="mt-8" padding="md">
          <HeroText className="text-sm leading-6 text-neutral-600">
            Return to your bookings and choose a valid completed service.
          </HeroText>
          <AppButton
            label="Back to bookings"
            className="mt-4"
            onPress={() => router.replace('/player/bookings')}
          />
        </AppCard>
      </AppScreen>
    );
  }

  if (booking.status !== 'completed') {
    return (
      <AppScreen
        title="Feedback not open yet"
        subtitle={`Booking ${orderCode} is ${formatBookingStatus(booking.status).toLowerCase()}.`}
        showBackButton
        onBackPress={() => router.back()}
      >
        <AppCard variant="subtle" className="mt-8" padding="md">
          <HeroText className="text-sm leading-6 text-neutral-600">
            Feedback becomes available after the shop marks the service
            completed.
          </HeroText>
          <AppButton
            label="View booking"
            className="mt-4"
            onPress={() => router.replace(`/player/bookings/${booking.id}`)}
          />
        </AppCard>
      </AppScreen>
    );
  }

  if (existingFeedback && !isEditing) {
    return (
      <AppScreen
        headerVariant="flow"
        title="Service feedback"
        subtitle={`Your saved feedback for booking ${orderCode}.`}
        showBackButton
        onBackPress={() => router.back()}
      >
        <AppCard variant="highlighted" padding="lg">
          <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary-700">
            Submitted
          </HeroText>
          <HeroText className="mt-2 text-2xl font-bold text-neutral-950">
            {existingFeedback.rating}/5
          </HeroText>
        </AppCard>
        <AppSection eyebrow="Detailed scores" title="Recorded experience">
          <AppCard variant="elevated" padding="md">
            {DETAIL_RATINGS.map(([key, label]) => (
              <View
                key={key}
                className="flex-row items-center justify-between py-2"
              >
                <HeroText className="text-sm text-neutral-600">{label}</HeroText>
                <HeroText className="text-sm font-bold text-neutral-950">
                  {existingFeedback[key] ?? '—'}/5
                </HeroText>
              </View>
            ))}
            <View className="flex-row items-center justify-between py-2">
              <HeroText className="text-sm text-neutral-600">
                Would use again
              </HeroText>
              <HeroText className="text-sm font-bold text-neutral-950">
                {existingFeedback.wouldUseAgain == null
                  ? '—'
                  : existingFeedback.wouldUseAgain
                    ? 'Yes'
                    : 'No'}
              </HeroText>
            </View>
          </AppCard>
        </AppSection>
        {existingFeedback.comment ? (
          <AppSection eyebrow="Comment" title="Player note">
            <AppCard variant="elevated" padding="md">
              <HeroText className="text-sm leading-6 text-neutral-700">
                {existingFeedback.comment}
              </HeroText>
            </AppCard>
          </AppSection>
        ) : null}
        {existingFeedback.stringFeedback ? (
          <AppSection eyebrow="String" title="Setup feedback">
            <AppCard variant="elevated" padding="md">
              <HeroText className="text-sm leading-6 text-neutral-700">
                {existingFeedback.stringFeedback}
              </HeroText>
            </AppCard>
          </AppSection>
        ) : null}
        {existingFeedback.serviceFeedback ? (
          <AppSection eyebrow="Service" title="Shop feedback">
            <AppCard variant="elevated" padding="md">
              <HeroText className="text-sm leading-6 text-neutral-700">
                {existingFeedback.serviceFeedback}
              </HeroText>
            </AppCard>
          </AppSection>
        ) : null}
        <AppButton
          label="Edit feedback"
          className="mt-8"
          onPress={beginEdit}
        />
        <AppButton
          label="Back to booking"
          variant="outline"
          className="mb-12 mt-3"
          onPress={() => router.replace(`/player/bookings/${booking.id}`)}
        />
      </AppScreen>
    );
  }

  return (
    <AppScreen
      headerVariant="flow"
      title={existingFeedback ? 'Edit feedback' : 'Rate your service'}
      subtitle={`Record only what you experienced for booking ${orderCode}.`}
      showBackButton
      onBackPress={() => router.back()}
    >
      {!token ? (
        <AppCard variant="subtle" className="mb-4" padding="md">
          <HeroText className="text-sm leading-6 text-neutral-600">
            Your player session expired. Sign in again before submitting
            feedback.
          </HeroText>
        </AppCard>
      ) : null}

      <AppSection eyebrow="Service" title="Overall stringing service">
        <AppCard variant="highlighted" padding="lg">
          <StarRating
            label="Overall service rating"
            value={rating}
            onChange={(value) => {
              setRating(value);
              markDirty('rating');
            }}
          />
        </AppCard>
      </AppSection>

      <AppSection eyebrow="Installed setup" title="Optional playing experience">
        <View className="gap-3">
          {DETAIL_RATINGS.map(([key, label]) => {
            return (
              <AppCard key={key} variant="elevated" padding="md">
                <StarRating
                  label={label}
                  value={detailRatings[key]}
                  onChange={(value) => {
                    setDetailRatings((current) => ({
                      ...current,
                      [key]: value,
                    }));
                    markDirty(DETAIL_API_KEYS[key]);
                  }}
                />
              </AppCard>
            );
          })}
        </View>
      </AppSection>

      <AppSection eyebrow="Reuse" title="Would you use this setup again?">
        <View className="gap-2">
          <HeroText className="ml-1 text-sm font-semibold text-foreground">
            Use this setup again
          </HeroText>
          <View
            accessibilityRole="radiogroup"
            accessibilityLabel="Use this setup again"
            className="flex-row gap-2"
          >
            <AppButton
              label="Yes"
              variant={wouldUseAgain === true ? 'primary' : 'outline'}
              className="flex-1"
              accessibilityRole="radio"
              accessibilityState={{ selected: wouldUseAgain === true }}
              onPress={() => {
                setWouldUseAgain(true);
                markDirty('would_use_again');
              }}
            />
            <AppButton
              label="No"
              variant={wouldUseAgain === false ? 'primary' : 'outline'}
              className="flex-1"
              accessibilityRole="radio"
              accessibilityState={{ selected: wouldUseAgain === false }}
              onPress={() => {
                setWouldUseAgain(false);
                markDirty('would_use_again');
              }}
            />
          </View>
        </View>
      </AppSection>

      <AppSection eyebrow="Comment" title="Anything else?">
        <AppInput
          value={comment}
          onChangeText={(value) => {
            setComment(value);
            markDirty('comment');
          }}
          maxLength={2000}
          multiline
          inputClassName="min-h-24"
          placeholder="Add your overall comment..."
        />
      </AppSection>

      <AppSection eyebrow="String feedback" title="How did the setup feel?">
        <AppInput
          value={stringFeedback}
          onChangeText={(value) => {
            setStringFeedback(value);
            markDirty('string_feedback');
          }}
          maxLength={2000}
          multiline
          inputClassName="min-h-24"
          placeholder="Describe feel, repulsion, or control..."
        />
      </AppSection>

      <AppSection eyebrow="Service feedback" title="How was the experience?">
        <AppInput
          value={serviceFeedback}
          onChangeText={(value) => {
            setServiceFeedback(value);
            markDirty('service_feedback');
          }}
          maxLength={2000}
          multiline
          inputClassName="min-h-24"
          placeholder="Share your experience with updates and turnaround..."
        />
      </AppSection>

      {submitError ? (
        <AppCard
          variant="subtle"
          className="mt-6 border border-red-100"
          padding="md"
        >
          <HeroText className="text-sm font-medium text-red-600">
            {submitError}
          </HeroText>
        </AppCard>
      ) : null}

      <AppButton
        label={existingFeedback ? 'Save changes' : 'Submit feedback'}
        size="lg"
        className="mb-12 mt-8"
        isLoading={isSubmitting}
        isDisabled={!token || (!existingFeedback && rating == null)}
        onPress={() => void submitFeedback()}
      />
    </AppScreen>
  );
}
