import React from 'react';
import { ScrollView, View, Pressable } from 'react-native';
import { useRouter } from 'expo-router';
import { HeroText } from '../ui/heroui';
import { MOCK_STRINGS } from '../../mocks/strings';

const categoryLabels = {
  repulsion: 'Repulsion',
  balanced: 'All-round',
  control: 'Control',
  durable: 'Durable',
} as const;

const brandThemes: Record<string, { shell: string; badge: string; accent: string }> = {
  Yonex: {
    shell: 'bg-[#F5F9FF] border-[#D6E5FF]',
    badge: 'bg-[#E7F0FF]',
    accent: '#2F64B6',
  },
  Victor: {
    shell: 'bg-[#F5FBFA] border-[#D8EEE8]',
    badge: 'bg-[#E9F7F3]',
    accent: '#237B68',
  },
  'Li-Ning': {
    shell: 'bg-[#FFF7F4] border-[#F4DFD6]',
    badge: 'bg-[#FFF0E8]',
    accent: '#C96B3C',
  },
  Gosen: {
    shell: 'bg-[#F9F6FF] border-[#E6DDF7]',
    badge: 'bg-[#F0EAFF]',
    accent: '#7A5FC4',
  },
  Ashaway: {
    shell: 'bg-[#F5FAF5] border-[#DDEEDD]',
    badge: 'bg-[#EAF6EA]',
    accent: '#4D8B57',
  },
};

export function TrendingStrings() {
  const router = useRouter();
  const trending = MOCK_STRINGS.slice(0, 5);

  return (
    <View className="mt-1">
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={{
          paddingHorizontal: 20,
          paddingRight: 44,
          gap: 12,
        }}
      >
        {trending.map((item) => {
          const theme = brandThemes[item.brand] ?? {
            shell: 'bg-[#F6F7F9] border-[#E5E7EB]',
            badge: 'bg-white/80',
            accent: '#2F64B6',
          };

          return (
            <Pressable
              key={item.id}
              onPress={() => router.push(`/player/strings/${item.id}`)}
              className="w-[156px] active:opacity-80"
            >
              <View className="overflow-hidden rounded-[24px] border border-[#E6EDF5] bg-white px-3.5 py-3.5 shadow-sm">
                <View className={`rounded-[20px] border px-3 py-3 ${theme.shell}`}>
                  <View className="flex-row items-start justify-between">
                    <View className={`rounded-full px-2.5 py-1 ${theme.badge}`}>
                      <HeroText className="text-[10px] font-semibold uppercase tracking-[0.18em] text-neutral-500">
                        {item.brand}
                      </HeroText>
                    </View>
                    <View className="rounded-full bg-white/70 px-2 py-1">
                      <HeroText className="text-[10px] font-semibold text-neutral-500">
                        {item.gauge}
                      </HeroText>
                    </View>
                  </View>

                  <View className="mt-4 h-[72px] items-center justify-center rounded-[18px] bg-white/85">
                    <View
                      className="h-11 w-11 items-center justify-center rounded-full"
                      style={{ backgroundColor: `${theme.accent}16` }}
                    >
                      <HeroText
                        className="text-[17px] font-bold tracking-[-0.03em]"
                        style={{ color: theme.accent }}
                      >
                        {item.brand[0]}
                      </HeroText>
                    </View>
                    <View
                      className="mt-2 h-1.5 w-16 rounded-full"
                      style={{ backgroundColor: `${theme.accent}30` }}
                    />
                    <View
                      className="mt-1 h-1.5 w-10 rounded-full"
                      style={{ backgroundColor: `${theme.accent}1A` }}
                    />
                  </View>
                </View>

                <View className="mt-3 gap-1">
                  <HeroText
                    className="text-[14px] font-semibold leading-[18px] tracking-[-0.02em] text-neutral-950"
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
