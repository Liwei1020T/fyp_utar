import type {
  BackendCommunityFeatureSummary,
  BackendCommunityStringSummary,
} from '../types/backend';

const FEATURE_ORDER = ['comfort', 'control', 'repulsion'];

export function communityEvidenceLabel(distinctUsers: number) {
  if (distinctUsers >= 10) return 'Established';
  if (distinctUsers >= 3) return 'Developing';
  if (distinctUsers > 0) return 'Limited';
  return 'No evidence';
}

export function formatCommunityScore(score: number) {
  const normalized = Math.min(1, Math.max(0, score));
  return `${(1 + normalized * 4).toFixed(1)}/5`;
}

export function formatCommunityWeight(weight: number) {
  return `${(Math.max(0, weight) * 100).toFixed(1)}%`;
}

export function communityFeatureEntries(
  features: BackendCommunityStringSummary['features'],
): [string, BackendCommunityFeatureSummary][] {
  return Object.entries(features).sort(([left], [right]) => {
    const leftIndex = FEATURE_ORDER.indexOf(left);
    const rightIndex = FEATURE_ORDER.indexOf(right);
    return (leftIndex === -1 ? FEATURE_ORDER.length : leftIndex)
      - (rightIndex === -1 ? FEATURE_ORDER.length : rightIndex)
      || left.localeCompare(right);
  });
}
