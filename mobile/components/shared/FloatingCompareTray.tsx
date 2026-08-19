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
  const bottomContentInset = useBottomContentInset(-8);
  const compareSelection = useAppStore((state) => state.compareSelection);
  const clearCompareSelection = useAppStore((state) => state.clearCompareSelection);

  if (compareSelection.length < 2) return null;

  return (
    <View 
      className="absolute left-4 right-4 z-50 bg-[#0F172A] rounded-[28px] shadow-2xl px-4 py-3 flex-row items-center justify-between border border-white/5"
      style={{ bottom: bottomContentInset }}
    >
      <View className="flex-row items-center gap-3">
        {/* Count Badge */}
        <View className="h-8 w-8 rounded-full bg-primary-600 items-center justify-center">
          <HeroText className="text-[12px] font-bold text-white leading-none">
            {compareSelection.length}
          </HeroText>
        </View>
        
        {/* Text Area */}
        <View>
          <HeroText className="text-[14px] font-bold text-white leading-tight">
            Shortlist Ready
          </HeroText>
          <HeroText className="text-[10px] text-slate-400 font-medium mt-0.5">
            Open side-by-side compare
          </HeroText>
        </View>
      </View>

      <View className="flex-row items-center gap-2">
        {/* Close Button */}
        <Pressable 
          accessibilityRole="button"
          accessibilityLabel="Clear comparison shortlist"
          accessibilityHint="Remove all selected strings"
          onPress={clearCompareSelection}
          className="h-11 w-11 items-center justify-center rounded-full bg-white/12 border border-white/5"
          hitSlop={6}
        >
          <X size={18} color="white" strokeWidth={2.5} />
        </Pressable>

        {/* Compare Action */}
        <AppButton 
          label="Compare" 
          size="sm" 
          variant="primary" 
          className="h-11 px-5 rounded-full bg-primary-600"
          onPress={() => router.push('/player/strings/compare')}
        />
      </View>
    </View>
  );
}
