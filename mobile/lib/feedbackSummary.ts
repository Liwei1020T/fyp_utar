import type {
  BackendFeedbackFeatureSummary,
  BackendFeedbackStringSummary,
} from '../types/backend';

const FEATURE_ORDER = ['comfort', 'control', 'repulsion'];

export function feedbackEvidenceLabel(distinctUsers: number) {
  if (distinctUsers >= 10) return 'Established';
  if (distinctUsers >= 3) return 'Developing';
  if (distinctUsers > 0) return 'Limited';
  return 'No evidence';
}

export function formatFeedbackScore(score: number) {
  const normalized = Math.min(1, Math.max(0, score));
  return `${(1 + normalized * 4).toFixed(1)}/5`;
}

export function formatFeedbackWeight(weight: number) {
  return `${(Math.max(0, weight) * 100).toFixed(1)}%`;
}

export function feedbackFeatureEntries(
  features: BackendFeedbackStringSummary['features'],
): [string, BackendFeedbackFeatureSummary][] {
  return Object.entries(features).sort(([left], [right]) => {
    const leftIndex = FEATURE_ORDER.indexOf(left);
    const rightIndex = FEATURE_ORDER.indexOf(right);
    return (leftIndex === -1 ? FEATURE_ORDER.length : leftIndex)
      - (rightIndex === -1 ? FEATURE_ORDER.length : rightIndex)
      || left.localeCompare(right);
  });
}
