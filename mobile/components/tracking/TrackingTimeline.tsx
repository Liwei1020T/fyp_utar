import React from 'react';
import { View } from 'react-native';
import { Check, CircleDot, Clock3 } from 'lucide-react-native';
import { AppChip } from '../ui/AppChip';
import { HeroText } from '../ui/heroui';
import type { BookingStatus, BookingStatusEntry } from '../../types/domain';

interface TrackingTimelineProps {
  timeline: BookingStatusEntry[];
  currentStatus: BookingStatus;
}

type TimelineVisualState = 'completed' | 'current' | 'future';

interface TimelineStepDefinition {
  status: BookingStatus;
  title: string;
  note: string;
}

interface TimelineStep extends TimelineStepDefinition {
  at?: string;
  visualState: TimelineVisualState;
}

const TRACKING_SEQUENCE: TimelineStepDefinition[] = [
  {
    status: 'confirmed',
    title: 'Booking confirmed',
    note: 'Your slot is secured and the service request is ready for drop-off.',
  },
  {
    status: 'awaiting_dropoff',
    title: 'Awaiting drop-off',
    note: 'Bring your racket to the shop during the selected drop-off window.',
  },
  {
    status: 'in_progress',
    title: 'Stringing started',
    note: 'The stringing team is working on your racket and checking the requested setup.',
  },
  {
    status: 'ready_for_collection',
    title: 'Ready for collection',
    note: 'Final checks are complete and your racket is ready to pick up.',
  },
  {
    status: 'completed',
    title: 'Completed',
    note: 'The racket has been collected and this service journey is now closed.',
  },
];

const NODE_STYLES: Record<TimelineVisualState, { shell: string; core: string; line: string; iconColor: string; accent: string }> = {
  completed: {
    shell: 'border-[#D9E9E1] bg-[#F4FAF6]',
    core: 'bg-[#5E8E78]',
    line: 'bg-[#C6DCCE]',
    iconColor: '#FFFFFF',
    accent: '#5E8E78',
  },
  current: {
    shell: 'border-[#D9E7F9] bg-[#EDF5FF]',
    core: 'bg-[#2F64B6]',
    line: 'bg-[#AFC8EE]',
    iconColor: '#FFFFFF',
    accent: '#2F64B6',
  },
  future: {
    shell: 'border-[#E8E2D2] bg-[#FCF8ED]',
    core: 'bg-[#D7C4A3]',
    line: 'bg-[#E6DCC6]',
    iconColor: '#7A684E',
    accent: '#B8925F',
  },
};

function formatTrackingDateTime(value?: string) {
  if (!value) {
    return 'Pending';
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString('en-MY', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
}

function getStageBadge(visualState: TimelineVisualState) {
  switch (visualState) {
    case 'completed':
      return { label: 'Done', variant: 'neutral' as const };
    case 'current':
      return { label: 'Current', variant: 'primary' as const };
    case 'future':
    default:
      return { label: 'Next', variant: 'warning' as const };
  }
}

function buildTrackingSteps(timeline: BookingStatusEntry[], currentStatus: BookingStatus) {
  const entryByStatus = new Map(timeline.map((entry) => [entry.status, entry]));
  const currentIndex = TRACKING_SEQUENCE.findIndex((step) => step.status === currentStatus);
  const fallbackCurrentIndex = currentIndex === -1 ? 0 : currentIndex;

  return TRACKING_SEQUENCE.map((step, index): TimelineStep => {
    const entry = entryByStatus.get(step.status);
    const visualState: TimelineVisualState =
      index < fallbackCurrentIndex ? 'completed' : index === fallbackCurrentIndex ? 'current' : 'future';

    return {
      status: step.status,
      title: entry?.title && entry.title !== step.title ? step.title : step.title,
      note: entry?.note ?? step.note,
      at: entry?.at,
      visualState,
    };
  });
}

export function TrackingTimeline({ timeline, currentStatus }: TrackingTimelineProps) {
  const steps = React.useMemo(
    () => buildTrackingSteps(timeline, currentStatus),
    [timeline, currentStatus]
  );

  return (
    <View className="rounded-[30px] border border-[#E4EBF5] bg-white/75 px-4 py-4 shadow-soft">
      {steps.map((step, index) => {
        const isLast = index === steps.length - 1;
        const styles = NODE_STYLES[step.visualState];
        const badge = getStageBadge(step.visualState);

        return (
          <View
            key={step.status}
            className={isLast ? 'pb-0' : 'pb-4'}
          >
            <View className="flex-row gap-3">
              <View className="items-center">
                <View className={`h-10 w-10 items-center justify-center rounded-full border ${styles.shell}`}>
                  <View className={`h-6 w-6 items-center justify-center rounded-full ${styles.core}`}>
                    {step.visualState === 'completed' ? (
                      <Check size={14} color={styles.iconColor} />
                    ) : step.visualState === 'current' ? (
                      <CircleDot size={14} color={styles.iconColor} />
                    ) : (
                      <Clock3 size={13} color={styles.iconColor} />
                    )}
                  </View>
                </View>
                {!isLast ? (
                  <View className="my-1 h-[72px] w-[3px] overflow-hidden rounded-full bg-[#EEF3F9]">
                    <View
                      className="w-full rounded-full"
                      style={{
                        height: step.visualState === 'completed' ? '100%' : step.visualState === 'current' ? '52%' : '20%',
                        backgroundColor: styles.line,
                      }}
                    />
                  </View>
                ) : null}
              </View>

              <View className="min-w-0 flex-1 pt-0.5">
                <View
                  className={`rounded-[24px] border px-4 py-3 ${
                    step.visualState === 'current'
                      ? 'border-[#D6E4F8] bg-[#F6FAFF]'
                      : step.visualState === 'completed'
                        ? 'border-[#E1EAE4] bg-[#F9FCFA]'
                        : 'border-[#ECE6DA] bg-[#FCFAF5]'
                  }`}
                >
                  <View className="flex-row items-start justify-between gap-3">
                    <View className="min-w-0 flex-1">
                      <HeroText className="text-[15px] font-bold tracking-tight text-neutral-950">
                        {step.title}
                      </HeroText>
                      <HeroText
                        className="mt-1 text-[12px] font-semibold"
                        style={{ color: styles.accent }}
                      >
                        {formatTrackingDateTime(step.at)}
                      </HeroText>
                    </View>
                    <AppChip
                      label={badge.label}
                      variant={badge.variant}
                      className="self-start"
                    />
                  </View>

                  <HeroText className="mt-2 text-[13px] leading-5 text-neutral-500">
                    {step.note}
                  </HeroText>
                </View>
              </View>
            </View>
          </View>
        );
      })}
    </View>
  );
}
