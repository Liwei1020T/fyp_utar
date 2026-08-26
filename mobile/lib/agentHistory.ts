import type { BackendAgentResponse } from '../types/backend';

const MAX_AGENT_HISTORY_CONTENT_LENGTH = 2000;

export function agentResponseToHistoryContent(
  response: Pick<BackendAgentResponse, 'summary' | 'answer' | 'evidence'>,
): string {
  return JSON.stringify({
    summary: response.summary,
    answer: response.answer,
    evidence: response.evidence,
  }).slice(0, MAX_AGENT_HISTORY_CONTENT_LENGTH);
}
