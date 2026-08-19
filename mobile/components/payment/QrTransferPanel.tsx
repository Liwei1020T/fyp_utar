import React, { useState } from 'react';
import { Image, Linking, Modal, Pressable, View } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { AppButton } from '../ui/AppButton';
import { AppCard } from '../ui/AppCard';
import { HeroText } from '../ui/heroui';
import type { BackendUploadFile } from '../../services/backendApi';

interface QrTransferPanelProps {
  qrUrl?: string;
  proof: BackendUploadFile | null;
  onProofChange: (proof: BackendUploadFile | null) => void;
}

function withDownloadQuery(url: string) {
  return `${url}${url.includes('?') ? '&' : '?'}download=1`;
}

export function QrTransferPanel({
  qrUrl,
  proof,
  onProofChange,
}: QrTransferPanelProps) {
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [isPicking, setIsPicking] = useState(false);

  const pickProof = async () => {
    setIsPicking(true);
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ['images'],
        quality: 0.85,
        allowsEditing: false,
      });
      if (result.canceled || !result.assets[0]) {
        return;
      }
      const asset = result.assets[0];
      onProofChange({
        uri: asset.uri,
        name: asset.fileName ?? `payment-proof-${Date.now()}.jpg`,
        type: asset.mimeType ?? 'image/jpeg',
      });
    } finally {
      setIsPicking(false);
    }
  };

  return (
    <>
      <AppCard variant="highlighted" padding="md">
        <HeroText className="text-base font-bold text-neutral-950">
          Pay by QR transfer
        </HeroText>
        <HeroText className="mt-1 text-sm leading-6 text-neutral-600">
          Scan the shop QR, complete the transfer in your banking app, then attach the payment screenshot for admin review.
        </HeroText>
        {qrUrl ? (
          <>
            <Pressable
              className="mt-4 items-center rounded-[20px] bg-white p-4"
              onPress={() => setIsPreviewOpen(true)}
              accessibilityRole="button"
              accessibilityLabel="Preview payment QR"
            >
              <Image source={{ uri: qrUrl }} className="h-56 w-56" resizeMode="contain" />
              <HeroText className="mt-2 text-xs font-semibold text-primary-700">
                Tap to preview
              </HeroText>
            </Pressable>
            <AppButton
              label="Download QR"
              variant="outline"
              size="sm"
              className="mt-3"
              onPress={() => void Linking.openURL(withDownloadQuery(qrUrl))}
            />
          </>
        ) : (
          <View className="mt-4 rounded-[16px] border border-warning-100 bg-warning-50 px-3 py-3">
            <HeroText className="text-sm font-semibold text-warning-700">
              Shop QR is not configured yet.
            </HeroText>
            <HeroText className="mt-1 text-xs leading-5 text-warning-700">
              Ask the shop admin to upload a payment QR before submitting this request.
            </HeroText>
          </View>
        )}

        <View className="mt-4 border-t border-primary-200 pt-4">
          <HeroText className="text-sm font-bold text-neutral-900">
            Payment screenshot
          </HeroText>
          {proof ? (
            <View className="mt-3 rounded-[16px] bg-white p-3">
              <Image source={{ uri: proof.uri }} className="h-40 w-full" resizeMode="contain" />
              <View className="mt-3 flex-row gap-2">
                <AppButton
                  label="Replace"
                  size="sm"
                  variant="outline"
                  className="flex-1"
                  isLoading={isPicking}
                  onPress={() => void pickProof()}
                />
                <AppButton
                  label="Remove"
                  size="sm"
                  variant="ghost"
                  className="flex-1"
                  onPress={() => onProofChange(null)}
                />
              </View>
            </View>
          ) : (
            <AppButton
              label="Choose screenshot"
              variant="outline"
              className="mt-3"
              isLoading={isPicking}
              onPress={() => void pickProof()}
            />
          )}
        </View>
      </AppCard>

      <Modal
        visible={isPreviewOpen}
        transparent
        animationType="fade"
        onRequestClose={() => setIsPreviewOpen(false)}
      >
        <View className="flex-1 items-center justify-center bg-black/80 p-6">
          <Pressable
            className="absolute inset-0"
            onPress={() => setIsPreviewOpen(false)}
            accessibilityRole="button"
            accessibilityLabel="Close QR preview"
          />
          {qrUrl ? <Image source={{ uri: qrUrl }} className="h-[80%] w-full" resizeMode="contain" /> : null}
          <AppButton
            label="Close preview"
            variant="secondary"
            className="mt-5"
            onPress={() => setIsPreviewOpen(false)}
          />
        </View>
      </Modal>
    </>
  );
}
