import React from 'react';
import { Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import { X } from 'lucide-react-native';
import { HeroText } from '../ui/heroui';
import { AppButton } from '../ui/AppButton';
import { useAppStore } from '../../store/appStore';
import { useBottomContentInset } from './AppScreen';

export function FloatingCompareTray() {
  const router = useRouter();
  const bottomContentInset = useBottomContentInset(-4);
  const compareSelection = useAppStore((state) => state.compareSelection);
  const clearCompareSelection = useAppStore((state) => state.clearCompareSelection);

  if (compareSelection.length < 2) return null;

  return (
    <View 
      className="absolute left-3 right-3 z-50 flex-row items-center justify-between rounded-[20px] border border-white/10 bg-[#0F172A] px-3 py-2 shadow-2xl"
      style={{ bottom: bottomContentInset }}
    >
      <View className="min-w-0 flex-1 flex-row items-center gap-2">
        {/* Count Badge */}
        <View className="h-8 w-8 items-center justify-center rounded-full bg-primary-600">
          <HeroText className="text-[12px] font-bold text-white leading-none">
            {compareSelection.length}
          </HeroText>
        </View>
        
        {/* Text Area */}
        <View className="min-w-0 flex-1">
          <HeroText className="text-[13px] font-bold leading-4 text-white" numberOfLines={1}>
            Compare shortlist
          </HeroText>
          <HeroText className="mt-0.5 text-[10px] font-medium leading-4 text-slate-400" numberOfLines={1}>
            {compareSelection.length} strings ready to compare
          </HeroText>
        </View>
      </View>

      <View className="ml-2 flex-row items-center gap-1.5">
        {/* Close Button */}
        <Pressable 
          accessibilityRole="button"
          accessibilityLabel="Clear comparison shortlist"
          accessibilityHint="Remove all selected strings"
          onPress={clearCompareSelection}
          className="h-10 w-10 items-center justify-center rounded-full border border-white/10 bg-white/10"
          hitSlop={6}
        >
          <X size={18} color="white" strokeWidth={2.5} />
        </Pressable>

        {/* Compare Action */}
        <AppButton 
          label="Compare" 
          size="sm" 
          variant="primary" 
          textClassName="text-[13px]"
          className="h-10 min-w-[84px] rounded-[10px] bg-primary-600 px-3"
          onPress={() => router.push('/player/strings/compare')}
        />
      </View>
    </View>
  );
}
