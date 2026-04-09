import React from 'react';
import { ScrollView, View, Pressable } from 'react-native';
import { useRouter } from 'expo-router';
import { HeroText } from '../ui/heroui';
import { MOCK_STRINGS } from '../../mocks/strings';

export function TrendingStrings() {
  const router = useRouter();
  
  // Use a subset or all mock strings for trending
  const trending = MOCK_STRINGS.slice(0, 5);

  return (
    <View className="mt-2">
      <ScrollView 
        horizontal 
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={{ 
          paddingHorizontal: 20, 
          paddingRight: 60, // Extra padding for better scroll feel
          gap: 12 
        }}
      >
        {trending.map((item) => (
          <Pressable 
            key={item.id}
            onPress={() => router.push(`/player/strings/${item.id}`)}
            className="w-32"
          >
            <View className="aspect-square w-full items-center justify-center rounded-[24px] bg-neutral-100 p-4 border border-neutral-200/50">
              <View className="h-16 w-16 items-center justify-center rounded-full bg-white shadow-sm">
                <HeroText className="text-xl font-bold text-primary-600">
                  {item.brand[0]}
                </HeroText>
              </View>
            </View>
            <HeroText className="mt-2 text-center text-sm font-semibold text-neutral-900" numberOfLines={1}>
              {item.model}
            </HeroText>
            <HeroText className="text-center text-[10px] uppercase tracking-wider text-neutral-400">
              {item.brand}
            </HeroText>
          </Pressable>
        ))}
      </ScrollView>
    </View>
  );
}
