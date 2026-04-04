import React from 'react';
import { Alert, Share, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { ChevronLeft, MessageSquareText, Scale, Share2, Sparkles, Star } from 'lucide-react-native';
import { HeroText } from '../../../components/ui/heroui';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppIconButton } from '../../../components/ui/AppIconButton';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { useAppStore } from '../../../store/appStore';
import { getStringById } from '../../../services/mockAppService';
import { formatCurrency, formatLabel } from '../../../lib/formatters';

export default function StringDetailScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ id?: string }>();
  const selectedString = getStringById(params.id);
  const compareSelection = useAppStore((state) => state.compareSelection);
  const toggleCompareSelection = useAppStore((state) => state.toggleCompareSelection);

  if (!selectedString) {
    return (
      <AppScreen title="String not found">
        <AppCard variant="subtle" className="mt-10" padding="lg">
          <HeroText className="text-lg font-bold text-neutral-900">
            This string is no longer available.
          </HeroText>
          <AppButton label="Back to catalog" className="mt-6" onPress={() => router.replace('/player/strings')} />
        </AppCard>
      </AppScreen>
    );
  }

  const isSelected = compareSelection.includes(selectedString.id);
  const performanceMetrics = Object.entries(selectedString.ratings);
  const leadingMetrics = performanceMetrics.slice(0, 4);
  const trailingMetric = performanceMetrics[4];

  const handleShare = async () => {
    try {
      await Share.share({
        message: [
          `${selectedString.brand} ${selectedString.model}`,
          `${formatCurrency(selectedString.price)} • ${selectedString.gauge} • ${formatLabel(selectedString.category)}`,
          `Recommended tension ${selectedString.recommendedTension[0]}-${selectedString.recommendedTension[1]} lbs`,
          selectedString.description,
        ].join('\n'),
      });
    } catch {
      Alert.alert('Share unavailable', 'This device could not open the share sheet for this item.');
    }
  };

  return (
    <AppScreen
      headerLeft={
        <AppIconButton
          icon={<ChevronLeft size={20} color="#111827" />}
          accessibilityLabel="Go back"
          onPress={() => router.back()}
        />
      }
      headerRight={
        <AppIconButton
          icon={<Share2 size={20} color="#475569" />}
          accessibilityLabel={`Share ${selectedString.brand} ${selectedString.model}`}
          onPress={handleShare}
        />
      }
    >
      <AppCard variant="dark" className="rounded-[32px]" padding="lg">
        <HeroText className="text-[11px] font-semibold uppercase tracking-[0.24em] text-primary-100">
          {selectedString.brand}
        </HeroText>
        <HeroText className="mt-3 text-[32px] font-bold tracking-tight text-white">
          {selectedString.model}
        </HeroText>

        <View className="mt-4 flex-row items-center gap-2">
          <View className="flex-row">
            {[1, 2, 3, 4, 5].map((item) => (
              <Star key={item} size={15} color="#FBBF24" fill="#FBBF24" />
            ))}
          </View>
          <HeroText className="text-sm text-primary-100">{selectedString.reviewHighlight}</HeroText>
        </View>

        <View className="mt-8 flex-row gap-3">
          <AppCard variant="subtle" className="flex-1 bg-white/8 border-white/10" padding="sm">
            <HeroText className="text-[11px] font-semibold uppercase tracking-[0.2em] text-primary-100">
              Price
            </HeroText>
            <HeroText className="mt-2 text-3xl font-bold text-white">
              {formatCurrency(selectedString.price)}
            </HeroText>
          </AppCard>
          <AppCard variant="subtle" className="flex-1 bg-white/8 border-white/10" padding="sm">
            <HeroText className="text-[11px] font-semibold uppercase tracking-[0.2em] text-primary-100">
              Tension fit
            </HeroText>
            <HeroText className="mt-2 text-xl font-bold text-white">
              {selectedString.recommendedTension[0]} - {selectedString.recommendedTension[1]} lbs
            </HeroText>
          </AppCard>
        </View>

        <View className="mt-6 flex-row flex-wrap gap-2">
          <AppChip label={formatLabel(selectedString.category)} variant="secondary" />
          <AppChip label={selectedString.gauge} variant="neutral" className="bg-white/10 border-white/10" />
          <AppChip label="Demo-ready" variant="info" className="bg-white/10 border-white/10" />
        </View>
      </AppCard>

      <AppSection eyebrow="Specs" title="Key setup details">
        <AppCard variant="elevated" padding="none">
          <View className="border-b border-neutral-100 p-4 flex-row justify-between">
            <HeroText className="text-neutral-500">Gauge</HeroText>
            <HeroText className="font-semibold text-neutral-950">{selectedString.gauge}</HeroText>
          </View>
          <View className="border-b border-neutral-100 p-4 flex-row justify-between">
            <HeroText className="text-neutral-500">Material</HeroText>
            <HeroText className="max-w-[12rem] text-right font-semibold text-neutral-950">
              {selectedString.material}
            </HeroText>
          </View>
          <View className="p-4 flex-row justify-between">
            <HeroText className="text-neutral-500">Recommended tension</HeroText>
            <HeroText className="font-semibold text-neutral-950">
              {selectedString.recommendedTension[0]} - {selectedString.recommendedTension[1]} lbs
            </HeroText>
          </View>
        </AppCard>
      </AppSection>

      <AppSection eyebrow="Performance" title="Highlights that matter">
        <View className="flex-row flex-wrap gap-3">
          {leadingMetrics.map(([key, value]) => (
            <AppCard key={key} variant="elevated" className="w-[48%] flex-1" padding="md">
              <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-neutral-400">
                {formatLabel(key)}
              </HeroText>
              <HeroText className="mt-2 text-2xl font-bold tracking-tight text-neutral-950">
                {value}/10
              </HeroText>
            </AppCard>
          ))}
        </View>
        {trailingMetric ? (
          <AppCard key={trailingMetric[0]} variant="elevated" className="mt-3" padding="md">
            <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-neutral-400">
              {formatLabel(trailingMetric[0])}
            </HeroText>
            <HeroText className="mt-2 text-2xl font-bold tracking-tight text-neutral-950">
              {trailingMetric[1]}/10
            </HeroText>
          </AppCard>
        ) : null}
      </AppSection>

      <AppSection eyebrow="Fit guidance" title="Recommended for who?">
        <View className="gap-3">
          <AppCard variant="highlighted" padding="md">
            <HeroText className="text-sm leading-6 text-neutral-700">
              {selectedString.description}
            </HeroText>
          </AppCard>
          <View className="flex-row flex-wrap gap-2">
            {selectedString.bestFor.map((item) => (
              <AppChip key={item} label={item} variant="primary" />
            ))}
          </View>
        </View>
      </AppSection>

      <AppSection eyebrow="Review highlights" title="What players usually say">
        <View className="gap-3">
          {selectedString.strengths.map((strength) => (
            <AppCard key={strength} variant="elevated" padding="sm">
              <HeroText className="text-sm font-semibold text-neutral-900">{strength}</HeroText>
            </AppCard>
          ))}
          {selectedString.tradeOffs.map((tradeOff) => (
            <AppCard key={tradeOff} variant="subtle" padding="sm">
              <HeroText className="text-sm leading-6 text-neutral-600">{tradeOff}</HeroText>
            </AppCard>
          ))}
        </View>
      </AppSection>

      <View className="mb-10 mt-8 gap-3">
        <View className="flex-row flex-wrap gap-3">
          <AppButton
            label="Book this string"
            className="min-w-[150px] flex-1"
            size="lg"
            onPress={() => router.push(`/player/bookings/new?stringId=${selectedString.id}`)}
          />
          <AppButton
            label={isSelected ? 'Selected' : 'Compare'}
            variant={isSelected ? 'secondary' : 'outline'}
            size="lg"
            className="min-w-[150px] flex-1"
            leadingIcon={<Scale size={16} color={isSelected ? '#78350F' : '#475569'} />}
            onPress={() => toggleCompareSelection(selectedString.id)}
          />
        </View>
        <View className="flex-row flex-wrap gap-3">
          <AppButton
            label="Explain fit"
            variant="outline"
            size="lg"
            className="min-w-[150px] flex-1"
            onPress={() => router.push(`/player/recommend/explain/${selectedString.id}`)}
          />
          <AppButton
            label="Ask AI"
            variant="ghost"
            size="lg"
            className="min-w-[150px] flex-1"
            leadingIcon={<MessageSquareText size={16} color="#475569" />}
            onPress={() => router.push('/player/chat/chat-001')}
          />
        </View>
      </View>
    </AppScreen>
  );
}
