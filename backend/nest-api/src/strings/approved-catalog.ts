import fs from 'node:fs';
import path from 'node:path';
import { UpsertStringDto } from './dto/upsert-string.dto';

type ApprovedSourceRow = Record<string, unknown>;

type AspectKey =
  | 'attack'
  | 'comfort'
  | 'control'
  | 'durability'
  | 'elasticity'
  | 'sound'
  | 'string_movement'
  | 'tension_retention'
  | 'value_for_money'
  | 'beginner_fit_score'
  | 'stability_score'
  | 'all_round_score';

const TAG_EFFECTS: Record<string, Partial<Record<AspectKey, number>>> = {
  弹性好: { attack: 0.18, elasticity: 0.22, sound: 0.12 },
  耐打: { durability: 0.25, stability_score: 0.16, tension_retention: 0.12 },
  控球好: { control: 0.24, beginner_fit_score: 0.06 },
  声音清脆: { sound: 0.26, attack: 0.08 },
  性价比高: { value_for_money: 0.28, beginner_fit_score: 0.08 },
  性价比低: { value_for_money: -0.24 },
  掉磅快: { tension_retention: -0.26, stability_score: -0.1 },
  手感好: { comfort: 0.2, control: 0.08 },
  震手: { comfort: -0.2 },
  粘手: { string_movement: 0.14, control: 0.08 },
};

export function normalizeCatalogName(brand: string, modelName: string): string {
  return `${brand} ${modelName}`
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

export function loadApprovedCatalogRows(sourcePath: string): ApprovedSourceRow[] {
  const resolvedPath = path.resolve(sourcePath);
  const text = fs.readFileSync(resolvedPath, 'utf-8');
  const extension = path.extname(resolvedPath).toLowerCase();
  if (extension === '.jsonl') {
    return text
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => JSON.parse(line) as ApprovedSourceRow);
  }

  if (extension === '.json') {
    const parsed = JSON.parse(text) as unknown;
    if (Array.isArray(parsed)) {
      return parsed as ApprovedSourceRow[];
    }
    if (parsed && typeof parsed === 'object' && Array.isArray((parsed as { items?: unknown[] }).items)) {
      return (parsed as { items: ApprovedSourceRow[] }).items;
    }
  }

  throw new Error(`Unsupported approved catalog source: ${resolvedPath}`);
}

export function approvedRowsToDtos(sourcePath: string): UpsertStringDto[] {
  return loadApprovedCatalogRows(sourcePath).map((row) => approvedRowToDto(row));
}

export function approvedNormalizedNames(sourcePath: string): Set<string> {
  return new Set(approvedRowsToDtos(sourcePath).map((item) => item.normalized_name!));
}

export function approvedRowToDto(row: ApprovedSourceRow): UpsertStringDto {
  const brand = asString(row.brand) ?? 'Unknown';
  const modelName =
    asString(row.name) ?? asString(row.model_name) ?? asString(row.id) ?? 'Unknown';
  const normalizedName = normalizeCatalogName(brand, modelName);
  const gaugeMm = parseGaugeMm(asString(row.gauge));
  const tags = [
    ...parseTagList(row.top_tags),
    ...parseStructuredTags(row.tags).map((tag) => tag.name),
  ];

  const aspectScores = deriveAspectScores(tags, gaugeMm);

  return {
    brand,
    model_name: modelName,
    normalized_name: normalizedName,
    price_rm: positiveNumber(row.price),
    attack: aspectScores.attack,
    comfort: aspectScores.comfort,
    control: aspectScores.control,
    durability: aspectScores.durability,
    elasticity: aspectScores.elasticity,
    sound: aspectScores.sound,
    string_movement: aspectScores.string_movement,
    tension_retention: aspectScores.tension_retention,
    value_for_money: aspectScores.value_for_money,
    beginner_fit_score: aspectScores.beginner_fit_score,
    stability_score: aspectScores.stability_score,
    all_round_score: aspectScores.all_round_score,
    source_item_id: asString(row.eid) ?? asString(row.id),
    source_url: asString(row.source_url),
    is_active: true,
  };
}

function deriveAspectScores(
  tags: string[],
  gaugeMm?: number,
): Record<AspectKey, number> {
  const scores: Record<AspectKey, number> = {
    attack: 0.45,
    comfort: 0.45,
    control: 0.45,
    durability: 0.45,
    elasticity: 0.45,
    sound: 0.45,
    string_movement: 0.45,
    tension_retention: 0.45,
    value_for_money: 0.45,
    beginner_fit_score: 0.45,
    stability_score: 0.45,
    all_round_score: 0.45,
  };

  for (const tag of tags) {
    const effect = TAG_EFFECTS[tag];
    if (!effect) {
      continue;
    }

    for (const [aspect, delta] of Object.entries(effect) as Array<[AspectKey, number]>) {
      scores[aspect] = clamp01(scores[aspect] + delta);
    }
  }

  if (gaugeMm !== undefined) {
    if (gaugeMm <= 0.65) {
      scores.attack = clamp01(scores.attack + 0.16);
      scores.elasticity = clamp01(scores.elasticity + 0.18);
      scores.sound = clamp01(scores.sound + 0.08);
      scores.durability = clamp01(scores.durability - 0.08);
      scores.comfort = clamp01(scores.comfort - 0.05);
    } else if (gaugeMm >= 0.69) {
      scores.durability = clamp01(scores.durability + 0.2);
      scores.stability_score = clamp01(scores.stability_score + 0.16);
      scores.tension_retention = clamp01(scores.tension_retention + 0.08);
      scores.comfort = clamp01(scores.comfort + 0.08);
      scores.attack = clamp01(scores.attack - 0.06);
    } else {
      scores.control = clamp01(scores.control + 0.08);
      scores.all_round_score = clamp01(scores.all_round_score + 0.12);
    }
  }

  scores.beginner_fit_score = clamp01(
    (scores.comfort + scores.control + scores.durability + scores.value_for_money) / 4,
  );
  scores.stability_score = clamp01(
    (scores.durability + scores.tension_retention + (1 - scores.string_movement)) / 3,
  );
  scores.all_round_score = clamp01(
    (scores.attack +
      scores.comfort +
      scores.control +
      scores.durability +
      scores.elasticity +
      scores.sound +
      scores.tension_retention +
      scores.value_for_money) /
      8,
  );

  return roundScores(scores);
}

function roundScores(scores: Record<AspectKey, number>): Record<AspectKey, number> {
  return Object.fromEntries(
    Object.entries(scores).map(([key, value]) => [key, Number(value.toFixed(2))]),
  ) as Record<AspectKey, number>;
}

function parseTagList(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value.filter((item): item is string => typeof item === 'string' && item.length > 0);
  }

  return [];
}

function parseStructuredTags(value: unknown): Array<{ name: string; votes: number }> {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .map((item) => {
      if (typeof item === 'string') {
        return { name: item, votes: 1 };
      }
      if (item && typeof item === 'object') {
        const candidate = item as { name?: unknown; votes?: unknown };
        if (typeof candidate.name === 'string') {
          return {
            name: candidate.name,
            votes: typeof candidate.votes === 'number' ? candidate.votes : 1,
          };
        }
      }
      return null;
    })
    .filter((item): item is { name: string; votes: number } => item !== null);
}

function parseGaugeMm(value?: string): number | undefined {
  if (!value) {
    return undefined;
  }

  const match = value.match(/([0-9]+(?:\.[0-9]+)?)/);
  if (!match) {
    return undefined;
  }

  const gauge = Number(match[1]);
  if (Number.isNaN(gauge)) {
    return undefined;
  }

  return gauge > 10 ? gauge / 100 : gauge;
}

function positiveNumber(value: unknown): number | undefined {
  if (typeof value === 'number' && Number.isFinite(value) && value > 0) {
    return value;
  }

  if (typeof value === 'string' && value.trim().length > 0) {
    const parsed = Number(value);
    if (Number.isFinite(parsed) && parsed > 0) {
      return parsed;
    }
  }

  return undefined;
}

function asString(value: unknown): string | undefined {
  if (typeof value === 'string' && value.trim().length > 0) {
    return value.trim();
  }
  if (typeof value === 'number' && Number.isFinite(value)) {
    return String(value);
  }
  return undefined;
}

function clamp01(value: number): number {
  return Math.min(1, Math.max(0, value));
}
