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
  useStrings,
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

export default function FeedbackScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ bookingId?: string }>();
  const bookingId = params.bookingId;
  const token = useBackendAccessToken();
  const bookings = useBookings();
  const strings = useStrings();
  const setLiveBookings = useAppStore((state) => state.setLiveBookings);
  const [resolvedBooking, setResolvedBooking] = useState<Booking | null>(null);
  const [existingFeedback, setExistingFeedback] =
    useState<BookingFeedback | null>(null);
  const [rating, setRating] = useState(5);
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
      const priceByStringId = new Map(
        strings.map((item) => [item.id, item.price]),
      );
      const mappedBooking = mapBackendBookingToBooking(
        response,
        priceByStringId,
      );
      setResolvedBooking(mappedBooking);
      const liveBookings = useAppStore.getState().liveBookings;
      setLiveBookings(
        liveBookings.some((item) => item.id === mappedBooking.id)
          ? liveBookings.map((item) =>
              item.id === mappedBooking.id ? mappedBooking : item,
            )
          : [mappedBooking, ...liveBookings],
      );

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
  }, [bookingId, setLiveBookings, strings, token]);

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
