import React from 'react';
import { ScrollView, View, Pressable } from 'react-native';
import { useRouter } from 'expo-router';
import { HeroText } from '../ui/heroui';
import { AppButton } from '../ui/AppButton';
import { StringProductImage } from '../shared/StringProductImage';
import { formatCurrency } from '../../lib/formatters';
import {
  useAppStore,
  useCurrentUser,
  useStrings,
} from '../../store/appStore';

const categoryLabels = {
  repulsion: 'Repulsion',
  balanced: 'All-round',
  control: 'Control',
  durable: 'Durable',
} as const;

export function TrendingStrings() {
  const router = useRouter();
  const user = useCurrentUser();
  const strings = useStrings();
  const hasHydrated = useAppStore((state) => state.hasHydrated);
  const storeSettings = useAppStore((state) => state.storeSettings);
  const configuredTrendingIds = storeSettings?.trendingStringIds ?? [];
  const configuredTrending = configuredTrendingIds
    .map((id) => strings.find((item) => item.id === id))
    .filter((item): item is NonNullable<typeof item> => Boolean(item));
  const trending = configuredTrending.slice(0, 5);
  const isHydratingConfiguredTrending =
    hasHydrated &&
    user?.role === 'player' &&
    configuredTrendingIds.length > 0 &&
    strings.length === 0;

  if (isHydratingConfiguredTrending) {
    return (
      <View className="mt-1 px-4">
        <View className="rounded-[14px] border border-[#DCE6F7] bg-[#F8FBFF] px-4 py-4">
          <HeroText className="text-[14px] font-semibold text-slate-900">
            Loading featured strings...
          </HeroText>
          <HeroText className="mt-1 text-[13px] leading-5 text-slate-600">
            Syncing the latest admin-picked strings for your home feed.
          </HeroText>
        </View>
      </View>
    );
  }

  if (trending.length === 0) {
    return (
      <View className="mt-1 px-4">
        <View className="rounded-[14px] border border-[#DCE6F7] bg-[#F8FBFF] px-4 py-4">
          <HeroText className="text-[14px] font-semibold text-slate-900">
            Featured strings are being refreshed
          </HeroText>
          <HeroText className="mt-1 text-[13px] leading-5 text-slate-600">
            Browse the full catalog to explore the strings currently available in the shop.
          </HeroText>
          <AppButton
            label="Browse catalog"
            variant="outline"
            size="sm"
            className="mt-3 self-start"
            onPress={() => router.push('/player/strings')}
          />
        </View>
      </View>
    );
  }

  return (
    <View className="mt-1">
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={{
          paddingHorizontal: 16,
          paddingRight: 36,
          gap: 10,
        }}
      >
        {trending.map((item) => {
          const isTopPick = item.id === trending[0]?.id;
          const shouldShowPrice = item.priceStatus === 'priced' && item.price > 0;

          return (
            <Pressable
              key={item.id}
              accessibilityRole="button"
              accessibilityLabel={`${item.brand} ${item.model}, ${item.gauge}`}
              accessibilityHint="Open string details"
              onPress={() => router.push(`/player/strings/${item.id}`)}
              className="w-[152px] active:opacity-80"
            >
              <View className="overflow-hidden rounded-[14px] border border-[#DCE6F7] bg-white px-3 py-3 shadow-sm">
                <View className={`rounded-[12px] border px-3 py-3 ${isTopPick ? 'border-primary-100 bg-primary-50' : 'border-[#E8EEF8] bg-[#F8FBFF]'}`}>
                  <View className="flex-row items-start justify-between">
                    <View className={`rounded-full px-2.5 py-1 ${isTopPick ? 'bg-accent-100/80' : 'bg-white/85'}`}>
                      <HeroText className="text-[10px] font-semibold uppercase tracking-[0.08em] text-slate-500">
                        {item.brand}
                      </HeroText>
                    </View>
                    <View className="rounded-full bg-white/70 px-2 py-1">
                      <HeroText className="text-[10px] font-semibold text-slate-500">
                        {item.gauge}
                      </HeroText>
                    </View>
                  </View>

                  <View className="mt-4 h-[92px] overflow-hidden rounded-[14px] bg-white">
                    <StringProductImage
                      imageUrl={item.imageUrl}
                      brand={item.brand}
                      model={item.model}
                      gauge={item.gauge}
                      className="h-full w-full"
                      fallbackClassName="h-full w-full rounded-[14px] border-0 bg-primary-50 shadow-none"
                      fallbackTextClassName="text-[18px] text-primary-700"
                      fallbackGaugeClassName="mt-2 border-primary-100 bg-white/80"
                    />
                  </View>
                </View>

                <View className="mt-3 min-h-[70px] gap-1">
                  <HeroText
                    className="text-[14px] font-semibold leading-[18px] tracking-normal text-slate-900"
                    numberOfLines={2}
                  >
                    {item.model}
                  </HeroText>
                  <HeroText className="text-[12px] font-medium text-slate-500" numberOfLines={1}>
                    {item.brand}
                  </HeroText>
                  <View className="mt-auto flex-row items-end justify-between gap-2">
                    <HeroText className="min-w-0 flex-1 text-[12px] font-medium text-primary-700" numberOfLines={1}>
                      {categoryLabels[item.category]}
                    </HeroText>
                    {shouldShowPrice ? (
                      <HeroText className="text-[12px] font-bold text-slate-900">
                        {formatCurrency(item.price)}
                      </HeroText>
                    ) : null}
                  </View>
                </View>
              </View>
            </Pressable>
          );
        })}
      </ScrollView>
    </View>
  );
}
