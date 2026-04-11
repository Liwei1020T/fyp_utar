import React from 'react';
import { Image, Modal, View } from 'react-native';
import { X } from 'lucide-react-native';
import { AppIconButton } from '../ui/AppIconButton';
import { HeroText } from '../ui/heroui';

interface PhotoPreviewModalProps {
  visible: boolean;
  imageUrl?: string;
  title?: string;
  subtitle?: string;
  note?: string;
  accessibilityLabel?: string;
  onClose: () => void;
}

export function PhotoPreviewModal({
  visible,
  imageUrl,
  title = 'Uploaded photo',
  subtitle = 'Photo preview',
  note,
  accessibilityLabel = 'Photo preview',
  onClose,
}: PhotoPreviewModalProps) {
  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onClose}
    >
      <View className="flex-1 justify-center bg-black/80 px-5">
        <View className="gap-4 rounded-[28px] bg-white p-4">
          <View className="flex-row items-start justify-between gap-4">
            <View className="flex-1">
              <HeroText className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary-700">
                {title}
              </HeroText>
              <HeroText className="mt-1 text-[17px] font-bold tracking-tight text-neutral-950">
                {subtitle}
              </HeroText>
            </View>
            <AppIconButton
              icon={<X size={18} color="#475569" />}
              accessibilityLabel="Close photo preview"
              onPress={onClose}
            />
          </View>
          {imageUrl ? (
            <Image
              source={{ uri: imageUrl }}
              className="h-[420px] w-full rounded-[24px] bg-neutral-100"
              resizeMode="contain"
              accessibilityLabel={accessibilityLabel}
            />
          ) : null}
          {note ? (
            <HeroText className="text-sm leading-6 text-neutral-600">
              {note}
            </HeroText>
          ) : null}
        </View>
      </View>
    </Modal>
  );
}
