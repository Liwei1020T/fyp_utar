import React, { useEffect, useState } from 'react';
import { ActivityIndicator, View } from 'react-native';
import { useRouter } from 'expo-router';
import { RefreshCw, ShieldCheck, UserRound, Users } from 'lucide-react-native';
import { AppScreen } from '../../components/shared/AppScreen';
import { AppSection } from '../../components/shared/AppSection';
import { AppButton } from '../../components/ui/AppButton';
import { AppCard } from '../../components/ui/AppCard';
import { AppChip } from '../../components/ui/AppChip';
import { HeroText } from '../../components/ui/heroui';
import { appChromeColors } from '../../components/ui/theme';
import { formatDateTime, formatLabel } from '../../lib/formatters';
import { BackendApiError, backendApi } from '../../services/backendApi';
import { useBackendAccessToken, useCurrentUser } from '../../store/appStore';
import type { BackendAdminUser, BackendAdminUsersOverview } from '../../types/backend';

function roleLabel(role: string) {
  return role === 'customer' ? 'Player' : formatLabel(role);
}

function joinedLabel(createdAt: string | null) {
  return createdAt ? `Joined ${formatDateTime(createdAt)}` : 'Join date unavailable';
}

function SummaryMetric({ label, value }: { label: string; value: number }) {
  return (
    <View className="flex-1 rounded-[12px] bg-white/10 px-3 py-2">
      <HeroText className="text-[10px] font-semibold uppercase tracking-[0.12em] text-secondary-100">
        {label}
      </HeroText>
      <HeroText className="mt-1 text-[18px] font-bold text-white">
        {value}
      </HeroText>
    </View>
  );
}

function UserRow({ item }: { item: BackendAdminUser }) {
  const isAdmin = item.role === 'admin';

  return (
    <AppCard variant="elevated" padding="sm">
      <View className="flex-row items-center gap-3">
        <View className="h-10 w-10 items-center justify-center rounded-[12px] border border-primary-200 bg-primary-50">
          {isAdmin ? (
            <ShieldCheck size={19} color={appChromeColors.primary} />
          ) : (
            <UserRound size={19} color={appChromeColors.primary} />
          )}
        </View>
        <View className="min-w-0 flex-1">
          <HeroText className="text-sm font-semibold text-slate-900" numberOfLines={1}>
            {item.username}
          </HeroText>
          <HeroText className="mt-1 text-[12px] leading-[17px] text-slate-600">
            {roleLabel(item.role)} · {joinedLabel(item.created_at)}
          </HeroText>
        </View>
        <AppChip
          label={item.is_active ? 'Active' : 'Inactive'}
          variant={item.is_active ? 'success' : 'neutral'}
        />
      </View>
    </AppCard>
  );
}

export default function AdminUsersScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const [overview, setOverview] = useState<BackendAdminUsersOverview | null>(null);
  const [isLoading, setIsLoading] = useState(Boolean(token));
  const [error, setError] = useState<string | null>(null);
  const [loadAttempt, setLoadAttempt] = useState(0);
  const isAdmin = user?.role === 'admin';

  useEffect(() => {
    if (!isAdmin) {
      setOverview(null);
      setIsLoading(false);
      setError(null);
      return;
    }

    if (!token) {
      setOverview(null);
      setIsLoading(false);
      setError('Backend login is required to view live users.');
      return;
    }

    let cancelled = false;

    const load = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await backendApi.adminFetchUsersOverview(token, 20);
        if (!cancelled) {
          setOverview(response);
        }
      } catch (loadError) {
        if (!cancelled) {
          const statusCode = loadError instanceof BackendApiError
            ? loadError.statusCode
            : undefined;
          setError(
            statusCode === 401
              ? 'Your admin session has expired. Sign in again to view users.'
              : statusCode !== undefined && statusCode >= 500
                ? 'User overview is temporarily unavailable. Try again in a moment.'
                : 'We could not load users right now. Check your connection and try again.',
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    void load();

    return () => {
      cancelled = true;
    };
  }, [isAdmin, loadAttempt, token]);

  if (!user || !isAdmin) {
    return null;
  }

  return (
    <AppScreen
      tone="admin"
      headerVariant="flow"
      title="User overview"
      subtitle="See who is using StringSence and when they joined."
      showBackButton
      onBackPress={() => router.back()}
    >
      <View className="gap-1">
        {error ? (
          <AppCard variant="subtle" padding="md">
            <HeroText className="text-sm leading-5 text-neutral-700">{error}</HeroText>
            <AppButton
              className="mt-3 self-start"
              size="sm"
              variant="outline"
              label="Try again"
              leadingIcon={<RefreshCw size={16} color={appChromeColors.primary} />}
              onPress={() => setLoadAttempt((attempt) => attempt + 1)}
              isLoading={isLoading}
            />
          </AppCard>
        ) : null}

        {isLoading && !overview ? (
          <AppCard variant="subtle" padding="lg">
            <View className="items-center gap-2">
              <ActivityIndicator color={appChromeColors.primary} />
              <HeroText className="text-sm text-slate-600">Loading live user overview...</HeroText>
            </View>
          </AppCard>
        ) : null}

        {overview ? (
          <>
            <AppSection
              eyebrow="USER OVERVIEW"
              title={`${overview.total_users} registered ${overview.total_users === 1 ? 'user' : 'users'}`}
              subtitle="Counts come directly from active accounts in the backend."
              rightAction={<AppChip label="Live data" variant="info" className="mt-1" />}
            >
              <AppCard variant="dark" padding="lg" className="rounded-[22px]">
                <View className="flex-row items-start justify-between gap-4">
                  <View className="flex-1">
                    <HeroText className="text-[11px] font-semibold uppercase tracking-[0.16em] text-secondary-100">
                      People using StringSence
                    </HeroText>
                    <HeroText className="mt-2 text-[42px] font-bold leading-[46px] tracking-tight text-white">
                      {overview.total_users}
                    </HeroText>
                    <HeroText className="mt-1 text-[13px] leading-[18px] text-secondary-100">
                      {overview.active_users} currently active
                    </HeroText>
                  </View>
                  <View className="h-11 w-11 items-center justify-center rounded-[16px] bg-white/10">
                    <Users size={21} color="#FFFFFF" />
                  </View>
                </View>
                <View className="mt-5 flex-row gap-2">
                  <SummaryMetric label="Active" value={overview.active_users} />
                  <SummaryMetric label="Players" value={overview.player_count} />
                  <SummaryMetric label="Admins" value={overview.admin_count} />
                </View>
              </AppCard>
            </AppSection>

            <AppSection
              eyebrow="LATEST ACCOUNTS"
              title="Recent users"
              subtitle={`${overview.users.length} of ${overview.total_users} accounts shown, newest first.`}
            >
              <View className="gap-2.5">
                {overview.users.map((item) => (
                  <UserRow key={item.id} item={item} />
                ))}
                {overview.users.length === 0 ? (
                  <AppCard variant="subtle" padding="md">
                    <HeroText className="text-sm font-semibold text-slate-900">
                      No registered users yet
                    </HeroText>
                    <HeroText className="mt-1 text-sm leading-5 text-slate-600">
                      New accounts will appear here after registration.
                    </HeroText>
                  </AppCard>
                ) : null}
              </View>
            </AppSection>

          </>
        ) : null}
      </View>
    </AppScreen>
  );
}
