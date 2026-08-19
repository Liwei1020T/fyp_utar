import React from 'react';
import { View } from 'react-native';
import { AlertTriangle, CheckCircle2, ExternalLink } from 'lucide-react-native';
import { AppButton } from '../ui/AppButton';
import { AppCard } from '../ui/AppCard';
import { AppChip, type AppChipVariant } from '../ui/AppChip';
import { HeroText } from '../ui/heroui';
import type {
  BackendAgentAction,
  BackendAgentResponse,
} from '../../types/backend';

interface AgentAnswerCardProps {
  response: BackendAgentResponse;
  onQuestion?: (question: string) => void;
  onAction?: (action: BackendAgentAction) => void;
}

const plainText = (value: string) => value.replace(/\*\*/g, '');

// Deferred FYP UI: switch these back on when the broader Agent scope returns.
const showEvidenceStatus = false;
const showSources = false;
const showSuggestedQuestions = false;

export function AgentAnswerCard({
  response,
  onQuestion,
  onAction,
}: AgentAnswerCardProps) {
  const statusCopy: Record<
    BackendAgentResponse['evidence_status'],
    { label: string; variant: AppChipVariant }
  > = {
    complete: { label: 'Evidence complete', variant: 'success' },
    partial: { label: 'Partial evidence', variant: 'warning' },
    insufficient_evidence: {
      label: 'Insufficient evidence',
      variant: 'danger',
    },
  };
  const status = statusCopy[response.evidence_status];
  const StatusIcon =
    response.evidence_status === 'complete' ? CheckCircle2 : AlertTriangle;

  return (
    <AppCard variant="default" padding="md" className="rounded-[24px]">
      <View className="flex-row items-start gap-3">
        {showEvidenceStatus ? (
          <View className="mt-0.5 h-9 w-9 items-center justify-center rounded-full bg-primary-50">
            <StatusIcon size={18} color="#2F64B6" strokeWidth={2.3} />
          </View>
        ) : null}
        <View className="flex-1">
          <View className="flex-row flex-wrap items-center gap-2">
            <HeroText className="text-base font-bold text-neutral-950">
              {plainText(response.summary)}
            </HeroText>
            {showEvidenceStatus ? (
              <AppChip label={status.label} variant={status.variant} />
            ) : null}
          </View>
          <HeroText className="mt-2 text-sm leading-6 text-neutral-700">
            {plainText(response.answer)}
          </HeroText>
        </View>
      </View>

      {response.evidence.length > 0 ? (
        <View className="mt-4 gap-2 rounded-[18px] bg-primary-50 px-4 py-3">
          {response.evidence.map((item) => (
            <HeroText key={item} className="text-xs leading-5 text-primary-800">
              • {plainText(item)}
            </HeroText>
          ))}
        </View>
      ) : null}

      {showSources && response.sources.length > 0 ? (
        <View className="mt-4">
          <HeroText className="text-[10px] font-bold uppercase tracking-widest text-neutral-400">
            Sources
          </HeroText>
          <View className="mt-2 flex-row flex-wrap gap-2">
            {response.sources.map((source) => (
              <AppChip
                key={`${source.source_type}:${source.source_id}`}
                label={source.label}
                variant="neutral"
              />
            ))}
          </View>
        </View>
      ) : null}

      {response.suggested_actions.length > 0 ? (
        <View className="mt-4 gap-2">
          {response.suggested_actions.map((action) => (
            <AppButton
              key={`${action.action}:${action.label}`}
              label={plainText(action.label)}
              variant="outline"
              size="sm"
              trailingIcon={<ExternalLink size={14} color="#2F64B6" />}
              onPress={onAction ? () => onAction(action) : undefined}
            />
          ))}
        </View>
      ) : null}

      {showSuggestedQuestions && response.suggested_questions.length > 0 ? (
        <View className="mt-4 flex-row flex-wrap gap-2">
          {response.suggested_questions.map((question) => (
            <AppChip
              key={question}
              label={plainText(question)}
              size="md"
              variant="primary"
              onPress={onQuestion ? () => onQuestion(question) : undefined}
            />
          ))}
        </View>
      ) : null}
    </AppCard>
  );
}
