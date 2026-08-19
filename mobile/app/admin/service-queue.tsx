import React, { useEffect, useState } from 'react';
import { View } from 'react-native';
import { useRouter } from 'expo-router';
import { ArrowRight } from 'lucide-react-native';
import { AppCard } from '../../components/ui/AppCard';
import { AppButton } from '../../components/ui/AppButton';
import { AppChip } from '../../components/ui/AppChip';
import { HeroText } from '../../components/ui/heroui';
import { AppScreen } from '../../components/shared/AppScreen';
import { AppSection } from '../../components/shared/AppSection';
import { formatDateTime, formatLabel } from '../../lib/formatters';
import { BackendApiError, backendApi } from '../../services/backendApi';
import { useBackendAccessToken, useCurrentUser } from '../../store/appStore';
import type { BackendServiceQueue } from '../../types/backend';

export default function AdminServiceQueueScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const [queue, setQueue] = useState<BackendServiceQueue | null>(null);
  const [isLoading, setIsLoading] = useState(Boolean(token));
  const [error, setError] = useState<string | null>(null);
  const [loadAttempt, setLoadAttempt] = useState(0);
  const isAdmin = user?.role === 'admin';

  useEffect(() => {
    if (!isAdmin) {
      setQueue(null);
      setIsLoading(false);
      setError(null);
      return;
    }

    if (!token) {
      setQueue(null);
      setIsLoading(false);
      setError('Backend admin login is required to view the live service queue.');
      return;
    }

    let cancelled = false;

    const hydrate = async () => {
      setQueue(null);
      setIsLoading(true);
      setError(null);
      try {
        const response = await backendApi.adminFetchServiceQueue(token);
        if (!cancelled) {
          setQueue(response);
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(
            loadError instanceof BackendApiError
              ? loadError.message
              : 'Failed to load the service queue.',
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    void hydrate();

    return () => {
      cancelled = true;
    };
  }, [isAdmin, loadAttempt, token]);

  if (!isAdmin) {
    return null;
  }

  const hasQueueItems = queue?.lanes.some((lane) => lane.items.length > 0) ?? false;

  return (
    <AppScreen
      tone="admin"
      headerVariant="primary"
      title="Service queue"
      subtitle="Visual board of active service jobs."
      showBackButton
      onBackPress={() => router.back()}
    >
      {isLoading ? (
        <AppCard variant="subtle" padding="lg">
          <HeroText className="text-base font-semibold text-neutral-900">
            Loading live service queue...
          </HeroText>
          <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
            Pulling the latest job order and queue positions from the backend.
          </HeroText>
        </AppCard>
      ) : null}

      {error ? (
        <AppCard variant="subtle" className="border border-red-100" padding="md">
          <HeroText className="text-sm font-medium leading-6 text-red-600">
            {error}
          </HeroText>
          {token ? (
            <AppButton
              className="mt-4"
              label="Retry"
              variant="outline"
              onPress={() => setLoadAttempt((current) => current + 1)}
            />
          ) : null}
        </AppCard>
      ) : null}

      {!isLoading && !error && queue ? (
        <AppCard variant="subtle" padding="sm">
          <HeroText className="text-xs font-medium text-neutral-500">
            Queue updated {formatDateTime(queue.generated_at)}
          </HeroText>
        </AppCard>
      ) : null}

      {!isLoading && !error && queue && !hasQueueItems ? (
        <AppCard variant="subtle" padding="lg">
          <HeroText className="text-base font-semibold text-neutral-900">
            No active service jobs
          </HeroText>
          <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
            New drop-offs and active stringing jobs will appear here in backend order.
          </HeroText>
        </AppCard>
      ) : null}

      {!isLoading && !error && hasQueueItems
        ? queue?.lanes.map((lane) => (
            <AppSection key={lane.title} eyebrow="Queue lane" title={lane.title}>
              <View className="gap-3">
                {lane.items.length > 0 ? (
                  lane.items.map((item) => {
                    const { booking } = item;
                    const customer =
                      booking.customer_username ||
                      booking.customer_phone_number ||
                      'Customer unavailable';
                    const racket =
                      [booking.racket_brand, booking.racket_model]
                        .filter(Boolean)
                        .join(' ') || 'Racket details pending';

                    return (
                      <AppCard
                        key={booking.id}
                        variant="elevated"
                        padding="md"
                        onPress={() => router.push(`/admin/bookings/${booking.id}`)}
                      >
                        <View className="gap-3">
                          <View className="flex-row items-start justify-between gap-3">
                            <View className="flex-1">
                              <HeroText className="text-xs font-semibold uppercase tracking-wider text-neutral-400">
                                {booking.order_code || booking.id}
                              </HeroText>
                              <HeroText className="mt-1 text-base font-bold text-neutral-900">
                                {customer}
                              </HeroText>
                              {booking.customer_phone_number &&
                              booking.customer_phone_number !== customer ? (
                                <HeroText className="mt-1 text-xs text-neutral-500">
                                  {booking.customer_phone_number}
                                </HeroText>
                              ) : null}
                            </View>
                            <ArrowRight size={18} color="#94A3B8" />
                          </View>

                          <View className="flex-row flex-wrap gap-2">
                            <AppChip
                              label={`Queue #${item.queue_position}`}
                              variant="primary"
                              size="sm"
                            />
                            <AppChip
                              label={formatLabel(booking.status)}
                              variant="neutral"
                              size="sm"
                            />
                          </View>

                          <View className="gap-1">
                            <HeroText className="text-sm font-semibold text-neutral-800">
                              {racket}
                            </HeroText>
                            <HeroText className="text-sm text-neutral-600">
                              {booking.string_name} ·{' '}
                              {booking.requested_tension != null
                                ? `${booking.requested_tension} lbs`
                                : 'Tension not set'}
                            </HeroText>
                            <HeroText className="text-xs leading-5 text-neutral-500">
                              Drop-off:{' '}
                              {booking.drop_off_datetime
                                ? formatDateTime(booking.drop_off_datetime)
                                : 'Not scheduled'}
                            </HeroText>
                            <HeroText className="text-xs leading-5 text-neutral-500">
                              Expected:{' '}
                              {booking.expected_completion_datetime
                                ? formatDateTime(booking.expected_completion_datetime)
                                : 'Not set'}
                            </HeroText>
                          </View>
                        </View>
                      </AppCard>
                    );
                  })
                ) : (
                  <AppCard variant="subtle" padding="md">
                    <HeroText className="text-sm leading-6 text-neutral-500">
                      No rackets are sitting in this lane right now.
                    </HeroText>
                  </AppCard>
                )}
              </View>
            </AppSection>
          ))
        : null}
    </AppScreen>
  );
}
