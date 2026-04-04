import React from 'react';
import { Pressable, ScrollView, View } from 'react-native';
import { useRouter } from 'expo-router';
import { ChevronLeft, Scale } from 'lucide-react-native';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { HeroText } from '../../../components/ui/heroui';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { useAppStore } from '../../../store/appStore';
import { getStringById } from '../../../services/mockAppService';
import { formatCurrency } from '../../../lib/formatters';
import type { StringItem } from '../../../types/domain';

export default function CompareStringsScreen() {
  const router = useRouter();
  const compareSelection = useAppStore((state) => state.compareSelection);
  const clearCompareSelection = useAppStore((state) => state.clearCompareSelection);
  const strings: StringItem[] = compareSelection
    .map((id) => getStringById(id))
    .filter((item): item is StringItem => Boolean(item));

  if (strings.length < 2) {
    return (
      <AppScreen title="Compare strings">
        <AppCard variant="subtle" className="mt-10" padding="lg">
          <HeroText className="text-lg font-bold text-neutral-900">
            Select at least two strings to compare.
          </HeroText>
          <HeroText className="mt-2 text-sm leading-6 text-neutral-500">
            Add strings from the catalog or recommendation results, then open this side-by-side view again.
          </HeroText>
          <AppButton label="Back to catalog" className="mt-6" onPress={() => router.replace('/player/strings')} />
        </AppCard>
      </AppScreen>
    );
  }

  return (
    <AppScreen
      title="Compare strings"
      subtitle="Review specs, ratings, strengths, and booking fit in one place."
      headerLeft={
        <Pressable onPress={() => router.back()}>
          <ChevronLeft size={24} color="#111827" />
        </Pressable>
      }
    >
      <AppCard variant="dark" className="rounded-[32px]" padding="lg">
        <View className="flex-row items-start justify-between gap-4">
          <View className="flex-1">
            <HeroText className="text-[11px] font-semibold uppercase tracking-[0.24em] text-primary-100">
              Side-by-side
            </HeroText>
            <HeroText className="mt-2 text-[28px] font-bold tracking-tight text-white">
              Compare your current shortlist before you commit.
            </HeroText>
          </View>
          <View className="h-12 w-12 items-center justify-center rounded-2xl bg-white/12">
            <Scale size={22} color="white" />
          </View>
        </View>
      </AppCard>

      <ScrollView horizontal showsHorizontalScrollIndicator={false} className="mt-8">
        {strings.map((stringItem) => (
          <AppCard key={stringItem.id} variant="elevated" className="mr-4 w-[320px]" padding="lg">
            <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary-700">
              {stringItem.brand}
            </HeroText>
            <HeroText className="mt-2 text-2xl font-bold tracking-tight text-neutral-950">
              {stringItem.model}
            </HeroText>
            <HeroText className="mt-2 text-sm text-neutral-500">
              {formatCurrency(stringItem.price)} • {stringItem.gauge}
            </HeroText>

            <View className="mt-4 flex-row flex-wrap gap-2">
              <AppChip label={`${stringItem.ratings.power}/10 power`} variant="secondary" />
              <AppChip label={`${stringItem.ratings.control}/10 control`} variant="info" />
              <AppChip label={`${stringItem.ratings.durability}/10 durability`} variant="success" />
            </View>

            <AppSection eyebrow="Best for" title="Player fit" variant="compact">
              <View className="flex-row flex-wrap gap-2">
                {stringItem.bestFor.map((item) => (
                  <AppChip key={item} label={item} variant="primary" />
                ))}
              </View>
            </AppSection>

            <AppSection eyebrow="Strengths" title="Why you might choose it" variant="compact">
              <View className="gap-2">
                {stringItem.strengths.map((item) => (
                  <AppCard key={item} variant="highlighted" padding="sm">
                    <HeroText className="text-sm text-neutral-700">{item}</HeroText>
                  </AppCard>
                ))}
              </View>
            </AppSection>

            <AppSection eyebrow="Trade-offs" title="Watch-outs" variant="compact">
              <View className="gap-2">
                {stringItem.tradeOffs.map((item) => (
                  <AppCard key={item} variant="subtle" padding="sm">
                    <HeroText className="text-sm text-neutral-600">{item}</HeroText>
                  </AppCard>
                ))}
              </View>
            </AppSection>

            <AppButton label="Book this setup" className="mt-6" onPress={() => router.push(`/player/bookings/new?stringId=${stringItem.id}`)} />
          </AppCard>
        ))}
      </ScrollView>

      <View className="mt-8 gap-3">
        <AppButton label="Back to catalog" variant="outline" size="lg" onPress={() => router.push('/player/strings')} />
        <AppButton label="Clear compare list" variant="ghost" size="lg" onPress={clearCompareSelection} />
      </View>
    </AppScreen>
  );
}
