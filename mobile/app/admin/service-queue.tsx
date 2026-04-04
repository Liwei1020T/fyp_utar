import React from 'react';
import { Pressable, View } from 'react-native';
import { useRouter } from 'expo-router';
import { ChevronLeft } from 'lucide-react-native';
import { AppCard } from '../../components/ui/AppCard';
import { AppIconButton } from '../../components/ui/AppIconButton';
import { HeroText } from '../../components/ui/heroui';
import { AppScreen } from '../../components/shared/AppScreen';
import { AppSection } from '../../components/shared/AppSection';
import { useBookings, useCurrentUser } from '../../store/appStore';

export default function AdminServiceQueueScreen() {
  const router = useRouter();
  const user = useCurrentUser();
  const bookings = useBookings();

  if (!user || user.role !== 'admin') {
    return null;
  }

  const adminBookings = bookings.filter((item) => item.adminId === user.id);
  const lanes = [
    { title: 'Awaiting drop-off', items: adminBookings.filter((item) => item.status === 'awaiting_dropoff') },
    { title: 'In progress', items: adminBookings.filter((item) => item.status === 'in_progress') },
    { title: 'Ready collection', items: adminBookings.filter((item) => item.status === 'ready_for_collection') },
  ];

  return (
    <AppScreen
      tone="admin"
      title="Service queue"
      subtitle="Visual board of active service jobs."
      headerLeft={
        <AppIconButton
          icon={<ChevronLeft size={20} color="#111827" />}
          accessibilityLabel="Go back"
          onPress={() => router.back()}
        />
      }
    >
      {lanes.map((lane) => (
        <AppSection key={lane.title} eyebrow="Queue lane" title={lane.title}>
          <View className="gap-3">
            {lane.items.map((item) => (
              <AppCard key={item.id} variant="elevated" padding="sm">
                <HeroText className="text-sm font-semibold text-neutral-900">
                  {item.id} • {item.racketBrand} {item.racketModel}
                </HeroText>
              </AppCard>
            ))}
          </View>
        </AppSection>
      ))}
    </AppScreen>
  );
}
