import React from 'react';
import { ScrollView, View, Pressable } from 'react-native';
import { useRouter } from 'expo-router';
import { HeroText } from '../ui/heroui';
import { MOCK_STRINGS } from '../../mocks/strings';
import { useAppStore, useCurrentUser, useStrings } from '../../store/appStore';

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
  const adminSettings = useAppStore((state) => state.adminSettings);
  const targetAdminId =
    user?.role === 'player'
      ? user.preferredAdminId
      : user?.role === 'admin'
        ? user.id
        : null;
  const configuredTrendingIds = targetAdminId
    ? adminSettings.find((item) => item.adminId === targetAdminId)?.trendingStringIds ?? []
    : [];
  const configuredTrending = configuredTrendingIds
    .map((id) => strings.find((item) => item.id === id))
    .filter((item): item is NonNullable<typeof item> => Boolean(item));
  const fallbackPool = strings.length > 0 ? strings : MOCK_STRINGS;
  const fallbackTrending = fallbackPool
    .filter((item) => !configuredTrendingIds.includes(item.id))
    .slice(0, Math.max(0, 5 - configuredTrending.length));
  const trending = [...configuredTrending, ...fallbackTrending].slice(0, 5);

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

          return (
            <Pressable
              key={item.id}
              onPress={() => router.push(`/player/strings/${item.id}`)}
              className="w-[152px] active:opacity-80"
            >
              <View className="overflow-hidden rounded-lg border border-[#D2D2D7] bg-white px-3 py-3 shadow-sm">
                <View className={`rounded-lg border px-3 py-3 ${isTopPick ? 'border-primary-100 bg-primary-50' : 'border-[#E5E5EA] bg-[#F5F5F7]'}`}>
                  <View className="flex-row items-start justify-between">
                    <View className={`rounded-full px-2.5 py-1 ${isTopPick ? 'bg-accent-100/80' : 'bg-white/85'}`}>
                      <HeroText className="text-[10px] font-semibold uppercase tracking-normal text-neutral-500">
                        {item.brand}
                      </HeroText>
                    </View>
                    <View className="rounded-full bg-white/70 px-2 py-1">
                      <HeroText className="text-[10px] font-semibold text-neutral-500">
                        {item.gauge}
                      </HeroText>
                    </View>
                  </View>

                  <View className="mt-4 h-[72px] items-center justify-center rounded-lg bg-white/85">
                    <View
                      className="h-11 w-11 items-center justify-center rounded-full"
                      style={{ backgroundColor: isTopPick ? '#0071E316' : '#1D1D1F10' }}
                    >
                      <HeroText
                        className="text-[17px] font-bold tracking-normal"
                        style={{ color: isTopPick ? '#0071E3' : '#1D1D1F' }}
                      >
                        {item.brand[0]}
                      </HeroText>
                    </View>
                    <View
                      className="mt-2 h-1.5 w-16 rounded-full"
                      style={{ backgroundColor: isTopPick ? '#0071E330' : '#1D1D1F18' }}
                    />
                    <View
                      className="mt-1 h-1.5 w-10 rounded-full"
                      style={{ backgroundColor: isTopPick ? '#0071E31A' : '#1D1D1F10' }}
                    />
                  </View>
                </View>

                <View className="mt-3 gap-1">
                  <HeroText
                    className="text-[14px] font-semibold leading-[18px] tracking-normal text-neutral-950"
                    numberOfLines={2}
                  >
                    {item.model}
                  </HeroText>
                  <HeroText className="text-[12px] font-medium text-neutral-500" numberOfLines={1}>
                    {item.brand}
                  </HeroText>
                  <HeroText className="text-[12px] font-medium text-primary-700" numberOfLines={1}>
                    {categoryLabels[item.category]}
                  </HeroText>
                </View>
              </View>
            </Pressable>
          );
        })}
      </ScrollView>
    </View>
  );
}
