import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Modal,
  Pressable,
  ScrollView,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { RefreshCw, Search, ShieldCheck, UserRound, Users, X } from 'lucide-react-native';
import { AppScreen } from '../../components/shared/AppScreen';
import { AppSection } from '../../components/shared/AppSection';
import { AppButton } from '../../components/ui/AppButton';
import { AppCard } from '../../components/ui/AppCard';
import { AppChip } from '../../components/ui/AppChip';
import { AppIconButton } from '../../components/ui/AppIconButton';
import { AppInput } from '../../components/ui/AppInput';
import { HeroText } from '../../components/ui/heroui';
import { appChromeColors } from '../../components/ui/theme';
import { formatDateTime, formatLabel } from '../../lib/formatters';
import { BackendApiError, backendApi } from '../../services/backendApi';
import { useBackendAccessToken, useCurrentUser } from '../../store/appStore';
import type {
  BackendAdminUser,
  BackendAdminUserDetail,
  BackendAdminUsersOverview,
} from '../../types/backend';

function roleLabel(role: string) {
  return role === 'customer' ? 'Player' : formatLabel(role);
}

function joinedLabel(createdAt: string | null) {
  return createdAt ? `Joined ${formatDateTime(createdAt)}` : 'Join date unavailable';
}

function requestErrorMessage(error: unknown, subject: 'users' | 'profile') {
  const statusCode = error instanceof BackendApiError ? error.statusCode : undefined;
  if (statusCode === 401) {
    return `Your admin session has expired. Sign in again to view ${subject}.`;
  }
  if (statusCode !== undefined && statusCode >= 500) {
    return `${subject === 'users' ? 'User overview' : 'User profile'} is temporarily unavailable. Try again in a moment.`;
  }
  return `We could not load ${subject} right now. Check your connection and try again.`;
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

function UserRow({ item, onPress }: { item: BackendAdminUser; onPress: () => void }) {
  const isAdmin = item.role === 'admin';

  return (
    <AppCard
      variant="elevated"
      padding="sm"
      onPress={onPress}
      accessibilityLabel={`Open ${item.username} profile`}
      accessibilityHint="Show profile and recent orders"
    >
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

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <View className="flex-row items-center justify-between gap-4 border-b border-slate-100 py-3">
      <HeroText className="text-sm text-slate-600">{label}</HeroText>
      <HeroText className="max-w-[62%] text-right text-sm font-semibold text-slate-900">
        {value}
      </HeroText>
    </View>
  );
}

function profileValue(value: string | null | undefined) {
  return value ? formatLabel(value) : 'Not set';
}

function orderStatusVariant(status: string) {
  if (status === 'completed') {
    return 'complete' as const;
  }
  if (status === 'cancelled' || status === 'rejected') {
    return 'danger' as const;
  }
  return 'info' as const;
}

function UserDetailModal({
  user,
  token,
  onClose,
}: {
  user: BackendAdminUser | null;
  token: string | null;
  onClose: () => void;
}) {
  const [detail, setDetail] = useState<BackendAdminUserDetail | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadAttempt, setLoadAttempt] = useState(0);
  const visible = user !== null;
  const userId = user?.id;

  useEffect(() => {
    if (!visible || !userId || !token) {
      return;
    }

    let cancelled = false;
    setDetail(null);
    setIsLoading(true);
    setError(null);

    const load = async () => {
      try {
        const response = await backendApi.adminFetchUserDetail(token, userId);
        if (!cancelled) {
          setDetail(response);
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(requestErrorMessage(loadError, 'profile'));
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
  }, [loadAttempt, token, userId, visible]);

  return (
    <Modal
      visible={visible}
      transparent
      animationType="slide"
      onRequestClose={onClose}
      statusBarTranslucent
    >
      <View className="flex-1 justify-end bg-black/40">
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Close user profile"
          onPress={onClose}
          className="absolute inset-0"
        />
        <View className="max-h-[88%] rounded-t-[24px] bg-white px-4 pb-5 pt-4">
          <View className="flex-row items-start justify-between gap-4">
            <View className="min-w-0 flex-1">
              <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary-700">
                User profile
              </HeroText>
              <HeroText className="mt-1 text-xl font-bold tracking-tight text-neutral-950">
                {user?.username ?? 'User'}
              </HeroText>
              {user ? (
                <HeroText className="mt-1 text-sm text-neutral-600">
                  {roleLabel(user.role)} · {user.is_active ? 'Active' : 'Inactive'}
                </HeroText>
              ) : null}
            </View>
            <AppIconButton
              icon={<X size={18} color={appChromeColors.textSecondary} />}
              accessibilityLabel="Close user profile"
              onPress={onClose}
            />
          </View>

          <ScrollView
            className="mt-4"
            keyboardShouldPersistTaps="handled"
            showsVerticalScrollIndicator={false}
            contentContainerStyle={{ paddingBottom: 12 }}
          >
            {isLoading ? (
              <AppCard variant="subtle" padding="lg">
                <View className="items-center gap-2">
                  <ActivityIndicator color={appChromeColors.primary} />
                  <HeroText className="text-sm text-slate-600">Loading user details...</HeroText>
                </View>
              </AppCard>
            ) : error ? (
              <AppCard variant="subtle" padding="md">
                <HeroText className="text-sm leading-5 text-red-700">{error}</HeroText>
                <AppButton
                  className="mt-3 self-start"
                  size="sm"
                  variant="outline"
                  label="Try again"
                  leadingIcon={<RefreshCw size={16} color={appChromeColors.primary} />}
                  onPress={() => setLoadAttempt((attempt) => attempt + 1)}
                />
              </AppCard>
            ) : detail ? (
              <>
                <AppCard variant="subtle" padding="md">
                  <HeroText className="text-[11px] font-semibold uppercase tracking-[0.16em] text-primary-700">
                    Account details
                  </HeroText>
                  <View className="mt-1">
                    <DetailRow label="Phone number" value={detail.phone_number} />
                    <DetailRow
                      label="Joined"
                      value={detail.created_at ? formatDateTime(detail.created_at) : 'Not available'}
                    />
                  </View>
                  {detail.profile ? (
                    <View>
                      <DetailRow label="Skill level" value={profileValue(detail.profile.skill_level)} />
                      <DetailRow label="Playing style" value={profileValue(detail.profile.playing_style)} />
                      <DetailRow
                        label="Preferred tension"
                        value={detail.profile.preferred_tension === null
                          ? 'Not set'
                          : `${detail.profile.preferred_tension} lbs`}
                      />
                      <DetailRow
                        label="Playing frequency"
                        value={detail.profile.frequency_per_week === null
                          ? 'Not set'
                          : `${detail.profile.frequency_per_week} days / week`}
                      />
                      <DetailRow label="Preferred feel" value={profileValue(detail.profile.preferred_feel)} />
                      <DetailRow label="Preferred gauge" value={profileValue(detail.profile.preferred_gauge)} />
                      <DetailRow label="Recent goal" value={profileValue(detail.profile.recent_goal)} />
                    </View>
                  ) : (
                    <HeroText className="mt-2 text-sm leading-5 text-slate-600">
                      This player has not completed a profile yet.
                    </HeroText>
                  )}
                </AppCard>

                <View className="mt-5">
                  <View className="flex-row items-center justify-between gap-3">
                    <View>
                      <HeroText className="text-lg font-bold tracking-tight text-neutral-950">
                        Recent orders
                      </HeroText>
                      <HeroText className="mt-1 text-sm text-slate-600">
                        Latest bookings for this account.
                      </HeroText>
                    </View>
                    <AppChip label={String(detail.recent_orders.length)} variant="info" />
                  </View>
                  <View className="mt-2.5 gap-2.5">
                    {detail.recent_orders.map((order) => (
                      <AppCard key={order.id} variant="elevated" padding="md">
                        <View className="flex-row items-start justify-between gap-3">
                          <View className="min-w-0 flex-1">
                            <HeroText className="text-sm font-bold text-slate-900">
                              {order.order_code}
                            </HeroText>
                            <HeroText className="mt-1 text-sm font-semibold text-slate-800" numberOfLines={2}>
                              {order.string_name}
                            </HeroText>
                          </View>
                          <AppChip
                            label={formatLabel(order.status)}
                            variant={orderStatusVariant(order.status)}
                          />
                        </View>
                        <HeroText className="mt-2 text-[12px] leading-[17px] text-slate-600">
                          {[
                            order.racket_model,
                            order.requested_tension === null
                              ? null
                              : `${order.requested_tension} lbs`,
                          ].filter(Boolean).join(' · ') || 'Racket details not provided'}
                        </HeroText>
                        <HeroText className="mt-1 text-[12px] leading-[17px] text-slate-600">
                          {order.drop_off_datetime
                            ? `Drop-off ${formatDateTime(order.drop_off_datetime)}`
                            : order.created_at
                              ? `Created ${formatDateTime(order.created_at)}`
                              : 'Date unavailable'}
                        </HeroText>
                      </AppCard>
                    ))}
                    {detail.recent_orders.length === 0 ? (
                      <AppCard variant="subtle" padding="md">
                        <HeroText className="text-sm font-semibold text-slate-900">
                          No orders yet
                        </HeroText>
                        <HeroText className="mt-1 text-sm leading-5 text-slate-600">
                          This account has no booking history.
                        </HeroText>
                      </AppCard>
                    ) : null}
                  </View>
                </View>
              </>
            ) : null}
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
}

export default function AdminUsersScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const token = useBackendAccessToken();
  const [overview, setOverview] = useState<BackendAdminUsersOverview | null>(null);
  const [search, setSearch] = useState('');
  const [selectedUser, setSelectedUser] = useState<BackendAdminUser | null>(null);
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
    const searchTerm = search.trim();
    const load = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await backendApi.adminFetchUsersOverview(token, 20, searchTerm);
        if (!cancelled) {
          setOverview(response);
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(requestErrorMessage(loadError, 'users'));
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    const timeout = setTimeout(() => void load(), searchTerm ? 250 : 0);

    return () => {
      cancelled = true;
      clearTimeout(timeout);
    };
  }, [isAdmin, loadAttempt, search, token]);

  if (!user || !isAdmin) {
    return null;
  }

  return (
    <>
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
                subtitle="Counts cover all registered accounts; search only filters the list."
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
                subtitle={search.trim()
                  ? `${overview.users.length} matching account${overview.users.length === 1 ? '' : 's'} found.`
                  : `${overview.users.length} of ${overview.total_users} accounts shown, newest first.`}
              >
                <AppInput
                  variant="minimal"
                  className="mb-1"
                  value={search}
                  onChangeText={setSearch}
                  placeholder="Search by username"
                  accessibilityLabel="Search users by username"
                  autoCapitalize="none"
                  autoCorrect={false}
                  returnKeyType="search"
                  leftAdornment={<Search size={18} color={appChromeColors.textMuted} />}
                />
                {isLoading ? (
                  <View className="mb-2 flex-row items-center gap-2">
                    <ActivityIndicator size="small" color={appChromeColors.primary} />
                    <HeroText className="text-xs text-slate-600">Updating results...</HeroText>
                  </View>
                ) : null}
                <View className="gap-2.5">
                  {overview.users.map((item) => (
                    <UserRow key={item.id} item={item} onPress={() => setSelectedUser(item)} />
                  ))}
                  {overview.users.length === 0 ? (
                    <AppCard variant="subtle" padding="md">
                      <HeroText className="text-sm font-semibold text-slate-900">
                        {search.trim() ? 'No users match this search' : 'No registered users yet'}
                      </HeroText>
                      <HeroText className="mt-1 text-sm leading-5 text-slate-600">
                        {search.trim()
                          ? 'Try a different username.'
                          : 'New accounts will appear here after registration.'}
                      </HeroText>
                    </AppCard>
                  ) : null}
                </View>
              </AppSection>
            </>
          ) : null}
        </View>
      </AppScreen>

      <UserDetailModal
        user={selectedUser}
        token={token}
        onClose={() => setSelectedUser(null)}
      />
    </>
  );
}
