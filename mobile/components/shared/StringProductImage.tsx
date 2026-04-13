import React, { useEffect, useState } from 'react';
import { Image, View } from 'react-native';
import { Zap } from 'lucide-react-native';
import { HeroText, cn } from '../ui/heroui';

interface StringProductImageProps {
  imageUrl?: string | null;
  brand: string;
  model: string;
  gauge: string;
  accessibilityLabel?: string;
  className?: string;
  imageClassName?: string;
  fallbackClassName?: string;
  fallbackTextClassName?: string;
  fallbackGaugeClassName?: string;
  resizeMode?: 'contain' | 'cover' | 'stretch' | 'center';
}

export function StringProductImage({
  imageUrl,
  brand,
  model,
  gauge,
  accessibilityLabel,
  className,
  imageClassName,
  fallbackClassName,
  fallbackTextClassName,
  fallbackGaugeClassName,
  resizeMode = 'contain',
}: StringProductImageProps) {
  const normalizedImageUrl = imageUrl?.trim() || null;
  const [hasImageError, setHasImageError] = useState(false);

  useEffect(() => {
    setHasImageError(false);
  }, [normalizedImageUrl, model]);

  if (normalizedImageUrl && !hasImageError) {
    return (
      <Image
        source={{ uri: normalizedImageUrl }}
        className={cn('h-full w-full', className, imageClassName)}
        resizeMode={resizeMode}
        accessibilityLabel={accessibilityLabel ?? `${brand} ${model} product photo`}
        onError={() => setHasImageError(true)}
      />
    );
  }

  return (
    <View className={cn('items-center justify-center', className)}>
      <View
        className={cn(
          'items-center justify-center rounded-2xl border-[6px] border-white/5 bg-neutral-900 shadow-2xl',
          fallbackClassName,
        )}
        style={{ transform: [{ rotate: '-5deg' }] }}
      >
        <Zap size={72} color="rgba(255,255,255,0.15)" className="absolute top-6 left-6" />
        <HeroText
          className={cn(
            'px-6 text-center text-3xl font-black uppercase leading-tight tracking-tighter text-white',
            fallbackTextClassName,
          )}
        >
          {model.split(' ').join('\n')}
        </HeroText>
        <View
          className={cn(
            'mt-6 rounded-full border border-white/10 bg-white/10 px-4 py-1.5',
            fallbackGaugeClassName,
          )}
        >
          <HeroText className="text-[10px] font-black uppercase tracking-[0.2em] text-white">
            {gauge}
          </HeroText>
        </View>
      </View>
    </View>
  );
}
