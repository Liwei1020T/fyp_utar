import React, { useState } from 'react';
import { Pressable, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { ChevronLeft, Star } from 'lucide-react-native';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppInput } from '../../../components/ui/AppInput';
import { HeroText } from '../../../components/ui/heroui';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';

export default function FeedbackScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ bookingId?: string }>();
  const [rating, setRating] = useState(5);
  const [stringFeedback, setStringFeedback] = useState('Crisp and lively with strong front-court response.');
  const [serviceFeedback, setServiceFeedback] = useState('Smooth check-in and clear service updates throughout the flow.');

  return (
    <AppScreen
      title="Rate your service"
      subtitle="Collect post-service and post-string feedback in a demo-ready way."
      headerLeft={
        <Pressable onPress={() => router.back()}>
          <ChevronLeft size={24} color="#111827" />
        </Pressable>
      }
    >
      <AppSection eyebrow="Booking" title={`Feedback for ${params.bookingId ?? 'recent booking'}`}>
        <AppCard variant="highlighted" padding="lg">
          <View className="flex-row gap-2">
            {[1, 2, 3, 4, 5].map((value) => (
              <Pressable key={value} onPress={() => setRating(value)}>
                <View className="h-12 w-12 items-center justify-center rounded-full bg-white/70">
                  <Star size={22} color={value <= rating ? '#FBBF24' : '#CBD5E1'} fill={value <= rating ? '#FBBF24' : 'transparent'} />
                </View>
              </Pressable>
            ))}
          </View>
          <HeroText className="mt-4 text-base font-semibold text-neutral-900">
            Overall rating: {rating}/5
          </HeroText>
        </AppCard>
      </AppSection>

      <AppSection eyebrow="String feedback" title="How did the setup feel?">
        <AppInput value={stringFeedback} onChangeText={setStringFeedback} multiline inputClassName="min-h-24" />
      </AppSection>

      <AppSection eyebrow="Service feedback" title="How was the experience?">
        <AppInput value={serviceFeedback} onChangeText={setServiceFeedback} multiline inputClassName="min-h-24" />
      </AppSection>

      <AppSection eyebrow="Tags" title="Quick sentiment">
        <View className="flex-row flex-wrap gap-2">
          {['Crisp feel', 'Good communication', 'Fast turnaround', 'Would book again'].map((item) => (
            <AppChip key={item} label={item} variant="primary" />
          ))}
        </View>
      </AppSection>

      <AppButton label="Submit feedback" size="lg" className="mt-8" onPress={() => router.replace('/player/bookings')} />
    </AppScreen>
  );
}
