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
import { AppChip } from '../../../components/ui/AppChip';
import { AppInput } from '../../../components/ui/AppInput';
import { HeroText } from '../../../components/ui/heroui';
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
  FeedbackSentimentTag,
} from '../../../types/domain';

const SENTIMENT_OPTIONS: {
  id: FeedbackSentimentTag;
  label: string;
}[] = [
  { id: 'crisp_feel', label: 'Crisp feel' },
  { id: 'good_communication', label: 'Good communication' },
  { id: 'fast_turnaround', label: 'Fast turnaround' },
  { id: 'would_book_again', label: 'Would book again' },
];

const DETAIL_RATINGS = [
  ['recommendationRelevance', 'Recommendation relevance'],
  ['stringSatisfaction', 'String satisfaction'],
  ['tensionSatisfaction', 'Tension satisfaction'],
  ['comfort', 'Comfort'],
  ['control', 'Control'],
  ['repulsion', 'Repulsion'],
  ['durability', 'Durability'],
] as const;

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
  const [rating, setRating] = useState(5);
  const [detailRatings, setDetailRatings] = useState(
    Object.fromEntries(DETAIL_RATINGS.map(([key]) => [key, 5])) as Record<
      (typeof DETAIL_RATINGS)[number][0],
      number
    >,
  );
  const [wouldUseAgain, setWouldUseAgain] = useState(true);
  const [comment, setComment] = useState('');
  const [stringFeedback, setStringFeedback] = useState('');
  const [serviceFeedback, setServiceFeedback] = useState('');
  const [sentimentTags, setSentimentTags] = useState<FeedbackSentimentTag[]>([]);
  const [isLoading, setIsLoading] = useState(Boolean(token && bookingId));
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

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

      try {
        const feedback = await backendApi.fetchBookingFeedback(
          token,
          bookingId,
        );
        setExistingFeedback(
          feedback ? mapBackendFeedbackToBookingFeedback(feedback) : null,
        );
      } catch (error) {
        if (error instanceof BackendApiError && error.statusCode === 404) {
          setExistingFeedback(null);
        } else {
          throw error;
        }
      }
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

  const toggleSentiment = (tag: FeedbackSentimentTag) => {
    setSentimentTags((current) =>
      current.includes(tag)
        ? current.filter((item) => item !== tag)
        : [...current, tag],
    );
  };

  const hasFeedbackContent =
    Boolean(comment.trim()) ||
    Boolean(stringFeedback.trim()) ||
    Boolean(serviceFeedback.trim()) ||
    sentimentTags.length > 0;

  const submitFeedback = async () => {
    if (!booking || booking.status !== 'completed') {
      setSubmitError('Feedback is only available for a completed booking.');
      return;
    }
    if (!token) {
      setSubmitError('A live player login is required to submit feedback.');
      return;
    }
    if (!hasFeedbackContent) {
      setSubmitError('Add feedback text or select at least one sentiment tag.');
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);
    setSuccessMessage(null);
    try {
      const response = await backendApi.createBookingFeedback(
        token,
        booking.id,
        {
          rating,
          recommendation_relevance: detailRatings.recommendationRelevance,
          string_satisfaction: detailRatings.stringSatisfaction,
          tension_satisfaction: detailRatings.tensionSatisfaction,
          comfort: detailRatings.comfort,
          control: detailRatings.control,
          repulsion: detailRatings.repulsion,
          durability: detailRatings.durability,
          would_use_again: wouldUseAgain,
          comment: comment.trim() || null,
          string_feedback: stringFeedback.trim() || null,
          service_feedback: serviceFeedback.trim() || null,
          sentiment_tags: sentimentTags,
        },
      );
      setExistingFeedback(mapBackendFeedbackToBookingFeedback(response));
      setSuccessMessage('Your feedback has been saved to this service record.');
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

  if (existingFeedback) {
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
          {successMessage ? (
            <HeroText className="mt-2 text-sm font-medium text-green-700">
              {successMessage}
            </HeroText>
          ) : null}
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
        {existingFeedback.sentimentTags.length > 0 ? (
          <AppSection eyebrow="Tags" title="Recorded sentiment">
            <View className="flex-row flex-wrap gap-2">
              {existingFeedback.sentimentTags.map((tag) => (
                <AppChip
                  key={tag}
                  label={
                    SENTIMENT_OPTIONS.find((item) => item.id === tag)?.label ??
                    tag
                  }
                  variant="primary"
                />
              ))}
            </View>
          </AppSection>
        ) : null}
        <AppButton
          label="Back to booking"
          className="mb-12 mt-8"
          onPress={() => router.replace(`/player/bookings/${booking.id}`)}
        />
      </AppScreen>
    );
  }

  return (
    <AppScreen
      headerVariant="flow"
      title="Rate your service"
      subtitle={`Save one feedback record for booking ${orderCode}.`}
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

      <AppSection eyebrow="Booking" title={`Feedback for ${orderCode}`}>
        <AppCard variant="highlighted" padding="lg">
          <View
            className="flex-row gap-2"
            accessibilityRole="radiogroup"
            accessibilityLabel="Overall service rating"
          >
            {[1, 2, 3, 4, 5].map((value) => (
              <Pressable
                key={value}
                accessibilityRole="radio"
                accessibilityLabel={`${value} out of 5 stars`}
                accessibilityState={{ checked: rating === value }}
                onPress={() => setRating(value)}
                className="h-12 w-12 items-center justify-center rounded-full bg-white/70"
              >
                <Star
                  size={22}
                  color={value <= rating ? '#FBBF24' : '#CBD5E1'}
                  fill={value <= rating ? '#FBBF24' : 'transparent'}
                />
              </Pressable>
            ))}
          </View>
          <HeroText className="mt-4 text-base font-semibold text-neutral-900">
            Overall rating: {rating}/5
          </HeroText>
        </AppCard>
      </AppSection>

      <AppSection eyebrow="Detailed ratings" title="Rate each part">
        <View className="gap-3">
          {DETAIL_RATINGS.map(([key, label]) => (
            <AppCard key={key} variant="elevated" padding="md">
              <HeroText className="mb-3 text-sm font-semibold text-neutral-900">
                {label}: {detailRatings[key]}/5
              </HeroText>
              <View
                className="flex-row gap-2"
                accessibilityRole="radiogroup"
                accessibilityLabel={label}
              >
                {[1, 2, 3, 4, 5].map((value) => (
                  <Pressable
                    key={value}
                    accessibilityRole="radio"
                    accessibilityLabel={`${label} ${value} out of 5`}
                    accessibilityState={{
                      checked: detailRatings[key] === value,
                    }}
                    className={`h-11 flex-1 items-center justify-center rounded-xl ${
                      detailRatings[key] === value
                        ? 'bg-primary-600'
                        : 'bg-neutral-100'
                    }`}
                    onPress={() =>
                      setDetailRatings((current) => ({
                        ...current,
                        [key]: value,
                      }))
                    }
                  >
                    <HeroText
                      className={`text-sm font-bold ${
                        detailRatings[key] === value
                          ? 'text-white'
                          : 'text-neutral-600'
                      }`}
                    >
                      {value}
                    </HeroText>
                  </Pressable>
                ))}
              </View>
            </AppCard>
          ))}
        </View>
      </AppSection>

      <AppSection eyebrow="Reuse" title="Would you use this setup again?">
        <View className="flex-row gap-3">
          {[true, false].map((value) => (
            <View key={String(value)} className="flex-1">
              <AppButton
                label={value ? 'Yes' : 'No'}
                variant={wouldUseAgain === value ? 'primary' : 'outline'}
                onPress={() => setWouldUseAgain(value)}
              />
            </View>
          ))}
        </View>
      </AppSection>

      <AppSection eyebrow="Comment" title="Anything else?">
        <AppInput
          value={comment}
          onChangeText={setComment}
          maxLength={2000}
          multiline
          inputClassName="min-h-24"
          placeholder="Add your overall comment..."
        />
      </AppSection>

      <AppSection eyebrow="String feedback" title="How did the setup feel?">
        <AppInput
          value={stringFeedback}
          onChangeText={setStringFeedback}
          maxLength={2000}
          multiline
          inputClassName="min-h-24"
          placeholder="Describe feel, repulsion, control, or durability..."
        />
      </AppSection>

      <AppSection eyebrow="Service feedback" title="How was the experience?">
        <AppInput
          value={serviceFeedback}
          onChangeText={setServiceFeedback}
          maxLength={2000}
          multiline
          inputClassName="min-h-24"
          placeholder="Share your experience with updates and turnaround..."
        />
      </AppSection>

      <AppSection eyebrow="Tags" title="Quick sentiment">
        <View className="flex-row flex-wrap gap-2">
          {SENTIMENT_OPTIONS.map((item) => {
            const isSelected = sentimentTags.includes(item.id);
            return (
              <AppChip
                key={item.id}
                label={item.label}
                variant={isSelected ? 'primary' : 'neutral'}
                accessibilityLabel={`${item.label} sentiment`}
                accessibilityState={{ selected: isSelected }}
                onPress={() => toggleSentiment(item.id)}
              />
            );
          })}
        </View>
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
        label="Submit feedback"
        size="lg"
        className="mb-12 mt-8"
        isLoading={isSubmitting}
        isDisabled={!token || !hasFeedbackContent}
        onPress={() => void submitFeedback()}
      />
    </AppScreen>
  );
}
