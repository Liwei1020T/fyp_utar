import React, { useEffect, useMemo, useState } from 'react';
import { View } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { z } from 'zod';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { ImagePlus, Trash2 } from 'lucide-react-native';
import { AdminStringThumbnail } from '../../../components/admin/inventory/AdminInventoryCard';
import { AppScreen } from '../../../components/shared/AppScreen';
import { AppSection } from '../../../components/shared/AppSection';
import { AppButton } from '../../../components/ui/AppButton';
import { AppCard } from '../../../components/ui/AppCard';
import { AppChip } from '../../../components/ui/AppChip';
import { AppInput } from '../../../components/ui/AppInput';
import { HeroText, HeroTextField } from '../../../components/ui/heroui';
import {
  buildStringDisplayName,
  deriveAvailabilityStatus,
  derivePriceStatus,
  formatGaugeRange,
  getInventoryPriceLabel,
  sanitizePerformanceScores,
} from '../../../lib/inventory';
import { formatAvailability, formatLabel } from '../../../lib/formatters';
import { showAlert } from '../../../lib/alerts';
import { BackendApiError, backendApi } from '../../../services/backendApi';
import {
  mapBackendInventoryStringToStringItem,
  mapOfficialPerformanceToPerformanceScores,
} from '../../../services/backendMappers';
import {
  useAppStore,
  useBackendAccessToken,
  useStrings,
} from '../../../store/appStore';
import type {
  InventoryAvailability,
  InventoryPriceStatus,
  StringItem,
  StringPerformanceScores,
} from '../../../types/domain';

type ScoreKey = keyof StringPerformanceScores;
type PricingMode = 'fixed_price' | 'quoted_at_shop' | 'price_pending';

interface InventoryFormState {
  brand: string;
  modelName: string;
  localizedName: string;
  description: string;
  material: string;
  gaugeMm: string;
  tensionMinLbs: string;
  tensionMaxLbs: string;
  mainTrait: string;
  category: StringItem['category'];
  isActive: boolean;
  powerScore: string;
  controlScore: string;
  durabilityScore: string;
  comfortScore: string;
  soundScore: string;
  imageUrl?: string;
  pricingMode: PricingMode;
  priceRm: string;
  stockLevel: string;
  availabilityStatus: InventoryAvailability;
  shopNote: string;
}

type NormalizedFormState = {
  brand: string;
  modelName: string;
  localizedName: string;
  description: string;
  material: string;
  gaugeMm: number | null;
  tensionMinLbs: number | null;
  tensionMaxLbs: number | null;
  mainTrait: string;
  category: StringItem['category'];
  isActive: boolean;
  powerScore: number | null;
  controlScore: number | null;
  durabilityScore: number | null;
  comfortScore: number | null;
  soundScore: number | null;
  imageUrl: string;
  pricingMode: PricingMode;
  priceRm: number | null;
  stockLevel: number | null;
  availabilityStatus: InventoryAvailability;
  shopNote: string;
};

type FormErrors = Partial<Record<keyof InventoryFormState, string>>;

const CATALOG_VISIBILITY_OPTIONS = [
  { id: true, label: 'Visible' },
  { id: false, label: 'Hidden' },
] as const;

const PRICING_MODE_OPTIONS: { id: PricingMode; label: string }[] = [
  { id: 'fixed_price', label: 'Fixed price' },
  { id: 'quoted_at_shop', label: 'Quoted at shop' },
  { id: 'price_pending', label: 'Price pending' },
];

const AVAILABILITY_OPTIONS: { id: InventoryAvailability; label: string }[] = [
  { id: 'in_stock', label: 'In Stock' },
  { id: 'low_stock', label: 'Low Stock' },
  { id: 'out_of_stock', label: 'Out of Stock' },
];

const CATEGORY_OPTIONS: { id: StringItem['category']; label: string }[] = [
  { id: 'repulsion', label: 'Repulsion' },
  { id: 'balanced', label: 'Balanced' },
  { id: 'control', label: 'Control' },
  { id: 'durable', label: 'Durable' },
];

const SCORE_FIELDS: { key: ScoreKey; label: string }[] = [
  { key: 'power', label: 'Power' },
  { key: 'control', label: 'Control' },
  { key: 'durability', label: 'Durability' },
  { key: 'comfort', label: 'Comfort' },
  { key: 'sound', label: 'Sound' },
];

const SCORE_FORM_KEYS: Record<ScoreKey, keyof InventoryFormState> = {
  power: 'powerScore',
  control: 'controlScore',
  durability: 'durabilityScore',
  comfort: 'comfortScore',
  sound: 'soundScore',
};

const inventoryFormSchema = z
  .object({
    brand: z.string().trim().min(1, 'Brand is required.'),
    modelName: z.string().trim().min(1, 'Model name is required.'),
    localizedName: z.string().trim(),
    description: z.string().trim().min(1, 'Description is required.'),
    material: z.string().trim().min(1, 'Material / construction is required.'),
    gaugeMm: z.number({ error: 'Gauge is required.' }).min(0.4).max(1.2),
    tensionMinLbs: z.number().min(15).max(40).nullable(),
    tensionMaxLbs: z.number().min(15).max(40).nullable(),
    mainTrait: z.string().trim().min(1, 'Main trait is required.'),
    category: z.enum(['repulsion', 'balanced', 'control', 'durable']),
    isActive: z.boolean(),
    powerScore: z.number().int().min(1).max(10),
    controlScore: z.number().int().min(1).max(10),
    durabilityScore: z.number().int().min(1).max(10),
    comfortScore: z.number().int().min(1).max(10),
    soundScore: z.number().int().min(1).max(10),
    imageUrl: z.string().trim(),
    pricingMode: z.enum(['fixed_price', 'quoted_at_shop', 'price_pending']),
    priceRm: z.number().min(0).max(999).nullable(),
    stockLevel: z.number().int().min(0).max(9999),
    availabilityStatus: z.enum(['in_stock', 'low_stock', 'out_of_stock']),
    shopNote: z.string().trim(),
  })
  .superRefine((value, context) => {
    if (
      value.tensionMinLbs != null &&
      value.tensionMaxLbs != null &&
      value.tensionMaxLbs < value.tensionMinLbs
    ) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Maximum tension must be greater than or equal to minimum tension.',
        path: ['tensionMaxLbs'],
      });
    }

    if (value.pricingMode === 'fixed_price' && value.priceRm == null) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Price is required when pricing mode is fixed price.',
        path: ['priceRm'],
      });
    }
  });

function parseNumber(value: string, fallback: number | null = null) {
  if (!value.trim()) {
    return fallback;
  }

  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function toGaugeInput(item: StringItem) {
  const primaryGauge = item.catalog.gaugeMinMm ?? item.catalog.gaugeMaxMm;
  return primaryGauge != null ? primaryGauge.toFixed(2) : '';
}

function formatSingleGauge(
  gaugeMm: number | null | undefined,
  fallback?: string,
) {
  if (gaugeMm == null) {
    return fallback ?? 'Gauge pending';
  }

  return `${gaugeMm.toFixed(2)} mm`;
}

function toPricingMode(item: StringItem): PricingMode {
  if (item.inventory.priceStatus === 'quoted_at_shop') {
    return 'quoted_at_shop';
  }
  if (item.inventory.priceStatus === 'priced' && item.inventory.price != null) {
    return 'fixed_price';
  }
  return 'price_pending';
}

function mapPricingModeToPriceStatus(mode: PricingMode): InventoryPriceStatus {
  switch (mode) {
    case 'quoted_at_shop':
      return 'quoted_at_shop';
    case 'fixed_price':
      return 'priced';
    case 'price_pending':
    default:
      return 'pending';
  }
}

function toFormState(item: StringItem): InventoryFormState {
  return {
    brand: item.catalog.brand,
    modelName: item.catalog.modelName,
    localizedName: item.catalog.localizedName ?? '',
    description: item.catalog.description,
    material: item.catalog.material,
    gaugeMm: toGaugeInput(item),
    tensionMinLbs: item.catalog.tensionMinLbs?.toString() ?? '',
    tensionMaxLbs: item.catalog.tensionMaxLbs?.toString() ?? '',
    mainTrait: item.catalog.mainTrait,
    category: item.catalog.category,
    isActive: item.catalog.isActive,
    powerScore: String(item.catalog.performanceScores.power),
    controlScore: String(item.catalog.performanceScores.control),
    durabilityScore: String(item.catalog.performanceScores.durability),
    comfortScore: String(item.catalog.performanceScores.comfort),
    soundScore: String(item.catalog.performanceScores.sound),
    imageUrl: item.catalog.imageUrl ?? item.imageUrl,
    pricingMode: toPricingMode(item),
    priceRm: item.inventory.price != null ? String(item.inventory.price) : '',
    stockLevel: String(item.inventory.stockQty),
    availabilityStatus: item.inventory.availabilityStatus,
    shopNote: item.inventory.shopNote ?? '',
  };
}

function normalizeForm(form: InventoryFormState): NormalizedFormState {
  return {
    brand: form.brand.trim(),
    modelName: form.modelName.trim(),
    localizedName: form.localizedName.trim(),
    description: form.description.trim(),
    material: form.material.trim(),
    gaugeMm: parseNumber(form.gaugeMm),
    tensionMinLbs: parseNumber(form.tensionMinLbs),
    tensionMaxLbs: parseNumber(form.tensionMaxLbs),
    mainTrait: form.mainTrait.trim(),
    category: form.category,
    isActive: form.isActive,
    powerScore: parseNumber(form.powerScore),
    controlScore: parseNumber(form.controlScore),
    durabilityScore: parseNumber(form.durabilityScore),
    comfortScore: parseNumber(form.comfortScore),
    soundScore: parseNumber(form.soundScore),
    imageUrl: form.imageUrl?.trim() ?? '',
    pricingMode: form.pricingMode,
    priceRm: form.pricingMode === 'fixed_price' ? parseNumber(form.priceRm) : null,
    stockLevel: parseNumber(form.stockLevel),
    availabilityStatus: form.availabilityStatus,
    shopNote: form.shopNote.trim(),
  };
}

function validateForm(form: InventoryFormState) {
  const normalized = normalizeForm(form);
  const parsed = inventoryFormSchema.safeParse(normalized);

  if (parsed.success) {
    return { success: true as const, data: parsed.data, errors: {} as FormErrors };
  }

  const fieldErrors: FormErrors = {};
  for (const issue of parsed.error.issues) {
    const field = issue.path[0];
    if (typeof field === 'string' && !(field in fieldErrors)) {
      fieldErrors[field as keyof InventoryFormState] = issue.message;
    }
  }

  return { success: false as const, errors: fieldErrors };
}

function createShortDescription(description: string) {
  const trimmed = description.trim();
  if (!trimmed) {
    return null;
  }

  const firstSentence = trimmed
    .split(/(?<=[.!?])\s+/)
    .find((segment) => segment.trim().length > 0);

  const preferred = (firstSentence ?? trimmed).trim();
  return preferred.length <= 160
    ? preferred
    : `${preferred.slice(0, 157).trimEnd()}...`;
}

function resolveAvailabilityStatus(normalized: NormalizedFormState) {
  const stockQty = Math.max(0, normalized.stockLevel ?? 0);
  return stockQty === 0 ? 'out_of_stock' : normalized.availabilityStatus;
}

function buildLocalPatch(
  stringItem: StringItem,
  normalized: NormalizedFormState,
): Partial<StringItem> {
  const gaugeMm = normalized.gaugeMm ?? stringItem.catalog.gaugeMinMm ?? stringItem.catalog.gaugeMaxMm;
  const crossGaugeMm = stringItem.catalog.isHybrid
    ? stringItem.catalog.gaugeMaxMm ?? gaugeMm
    : gaugeMm;
  const stockQty = Math.max(0, normalized.stockLevel ?? stringItem.inventory.stockQty);
  const inventoryPrice =
    normalized.pricingMode === 'fixed_price'
      ? normalized.priceRm ?? stringItem.inventory.price
      : null;
  const inventoryPriceStatus = derivePriceStatus(
    inventoryPrice,
    mapPricingModeToPriceStatus(normalized.pricingMode),
  );
  const availabilityStatus = resolveAvailabilityStatus(normalized) ?? deriveAvailabilityStatus(stockQty);
  const performanceScores = sanitizePerformanceScores(
    {
      power: normalized.powerScore ?? stringItem.catalog.performanceScores.power,
      control: normalized.controlScore ?? stringItem.catalog.performanceScores.control,
      durability: normalized.durabilityScore ?? stringItem.catalog.performanceScores.durability,
      comfort: normalized.comfortScore ?? stringItem.catalog.performanceScores.comfort,
      sound: normalized.soundScore ?? stringItem.catalog.performanceScores.sound,
    },
    stringItem.catalog.performanceScores,
  );
  const catalog = {
    ...stringItem.catalog,
    brand: normalized.brand,
    modelName: normalized.modelName,
    localizedName: normalized.localizedName || undefined,
    gaugeMinMm: gaugeMm,
    gaugeMaxMm: crossGaugeMm,
    material: normalized.material,
    description: normalized.description,
    mainTrait: normalized.mainTrait,
    category: normalized.category,
    tensionMinLbs: normalized.tensionMinLbs,
    tensionMaxLbs: normalized.tensionMaxLbs,
    performanceScores,
    imageUrl: normalized.imageUrl || undefined,
    isActive: normalized.isActive,
    updatedAt: new Date().toISOString(),
  };
  const inventory = {
    ...stringItem.inventory,
    stockQty,
    price: inventoryPrice,
    priceStatus: inventoryPriceStatus,
    availabilityStatus,
    shopNote: normalized.shopNote || undefined,
    updatedAt: new Date().toISOString(),
  };
  const retainedTags = stringItem.inventoryTags.filter((tag) => {
    const normalizedTag = tag.toLowerCase();
    return (
      normalizedTag !== stringItem.catalog.mainTrait.toLowerCase() &&
      normalizedTag !== formatLabel(stringItem.category).toLowerCase()
    );
  });

  return {
    brand: catalog.brand,
    model: catalog.modelName,
    localizedName: catalog.localizedName,
    category: catalog.category,
    mainTrait: catalog.mainTrait,
    gauge: formatGaugeRange(catalog.gaugeMinMm, catalog.gaugeMaxMm, stringItem.gauge),
    gaugeMinMm: catalog.gaugeMinMm,
    gaugeMaxMm: catalog.gaugeMaxMm,
    material: catalog.material,
    price: inventory.price ?? 0,
    priceStatus: inventory.priceStatus,
    recommendedTension: [
      normalized.tensionMinLbs ?? stringItem.recommendedTension[0],
      normalized.tensionMaxLbs ?? stringItem.recommendedTension[1],
    ],
    tensionMinLbs: catalog.tensionMinLbs,
    tensionMaxLbs: catalog.tensionMaxLbs,
    ratings: performanceScores,
    tensionNote: `Recommended at ${
      normalized.tensionMinLbs ?? stringItem.recommendedTension[0]
    }-${normalized.tensionMaxLbs ?? stringItem.recommendedTension[1]} lbs for the current shop setup.`,
    description: catalog.description,
    imageUrl: catalog.imageUrl,
    isActive: catalog.isActive,
    updatedAt: catalog.updatedAt,
    inventoryUpdatedAt: inventory.updatedAt,
    inventoryTags: [catalog.mainTrait, formatLabel(catalog.category), ...retainedTags].slice(0, 4),
    stockLevel: inventory.stockQty,
    availability: inventory.availabilityStatus,
    adminNote: inventory.shopNote,
    catalog,
    inventory,
  };
}

function buildCatalogPayload(
  normalized: NormalizedFormState,
  stringItem: StringItem,
) {
  const crossGaugeMm = stringItem.catalog.isHybrid
    ? stringItem.catalog.gaugeMaxMm ?? normalized.gaugeMm
    : normalized.gaugeMm;
  return {
    brand: normalized.brand,
    model_name: normalized.modelName,
    display_name: `${normalized.brand} ${normalized.modelName}`.trim(),
    gauge_main_mm: normalized.gaugeMm,
    gauge_cross_mm: crossGaugeMm,
    gauge_label: formatGaugeRange(normalized.gaugeMm, crossGaugeMm),
    category: normalized.category,
    main_trait: normalized.mainTrait || null,
    tension_min_lbs: normalized.tensionMinLbs,
    tension_max_lbs: normalized.tensionMaxLbs,
    material_summary_en: normalized.material || null,
    short_description: createShortDescription(normalized.description),
    full_description: normalized.description,
    original_name: normalized.localizedName || null,
    is_hybrid: stringItem.catalog.isHybrid,
    is_active: normalized.isActive,
  };
}

function buildInventoryPayload(normalized: NormalizedFormState) {
  return {
    price_rm: normalized.pricingMode === 'fixed_price' ? normalized.priceRm : null,
    pricing_mode: normalized.pricingMode,
    stock_level: normalized.stockLevel ?? 0,
    availability_status: resolveAvailabilityStatus(normalized),
    admin_note: normalized.shopNote || null,
  };
}

function buildOfficialPerformancePayload(normalized: NormalizedFormState) {
  return {
    source_type: 'admin_manual',
    source_name: 'Admin editor',
    repulsion_power: normalized.powerScore,
    control: normalized.controlScore,
    durability: normalized.durabilityScore,
    shock_absorption: normalized.comfortScore,
    hitting_sound: normalized.soundScore,
    status: 'manual_reviewed',
  };
}

function serializeComparable(value: unknown) {
  return JSON.stringify(value);
}

function comparableCatalogState(normalized: NormalizedFormState) {
  return {
    brand: normalized.brand,
    modelName: normalized.modelName,
    localizedName: normalized.localizedName,
    description: normalized.description,
    material: normalized.material,
    gaugeMm: normalized.gaugeMm,
    tensionMinLbs: normalized.tensionMinLbs,
    tensionMaxLbs: normalized.tensionMaxLbs,
    mainTrait: normalized.mainTrait,
    category: normalized.category,
    isActive: normalized.isActive,
  };
}

function comparableScoreState(normalized: NormalizedFormState) {
  return {
    powerScore: normalized.powerScore,
    controlScore: normalized.controlScore,
    durabilityScore: normalized.durabilityScore,
    comfortScore: normalized.comfortScore,
    soundScore: normalized.soundScore,
  };
}

function comparableInventoryState(normalized: NormalizedFormState) {
  return {
    pricingMode: normalized.pricingMode,
    priceRm: normalized.pricingMode === 'fixed_price' ? normalized.priceRm : null,
    stockLevel: normalized.stockLevel,
    availabilityStatus: normalized.availabilityStatus,
    shopNote: normalized.shopNote,
  };
}

function isPersistedBackendImage(value: string) {
  return value.startsWith('/media/') || /^https?:\/\//i.test(value);
}

function ChoiceGroup<T extends string | boolean>({
  label,
  helperText,
  value,
  options,
  onChange,
}: {
  label: string;
  helperText?: string;
  value: T;
  options: { id: T; label: string }[];
  onChange: (value: T) => void;
}) {
  return (
    <View className="mb-4">
      <HeroText className="mb-2 ml-1 text-sm font-semibold text-foreground">
        {label}
      </HeroText>
      <View className="flex-row flex-wrap gap-2">
        {options.map((option) => (
          <AppChip
            key={String(option.id)}
            label={option.label}
            variant={value === option.id ? 'primary' : 'neutral'}
            onPress={() => onChange(option.id)}
          />
        ))}
      </View>
      {helperText ? (
        <HeroText className="mt-2 ml-1 text-xs leading-5 text-muted">
          {helperText}
        </HeroText>
      ) : null}
    </View>
  );
}

function ScoreRow({
  label,
  value,
  error,
  onChangeText,
}: {
  label: string;
  value: string;
  error?: string;
  onChangeText: (value: string) => void;
}) {
  return (
    <View className="mb-3 rounded-[18px] border border-[#D8E2EE] bg-white px-4 py-3">
      <View className="flex-row items-center gap-3">
        <View className="flex-1">
          <HeroText className="text-[14px] font-semibold text-neutral-900">
            {label}
          </HeroText>
          <HeroText className="mt-0.5 text-[12px] text-neutral-500">
            Scale 1 to 10
          </HeroText>
        </View>
        <View className="h-12 w-[74px] rounded-[14px] border border-[#D8E2EE] bg-[#F8FBFF] px-3">
          <HeroTextField
            variant="secondary"
            keyboardType="numeric"
            value={value}
            onChangeText={onChangeText}
            className="h-full border-0 bg-transparent px-0 text-center text-[15px] font-semibold text-neutral-900"
            selectionColorClassName="accent-primary-600"
            placeholderColorClassName="field-placeholder"
          />
        </View>
      </View>
      {error ? (
        <HeroText className="mt-2 ml-1 text-xs leading-5 text-danger">
          {error}
        </HeroText>
      ) : null}
    </View>
  );
}

function SummaryDetail({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <View className="min-w-[120px] flex-1 rounded-[18px] border border-[#D8E2EE] bg-white/80 px-3.5 py-3">
      <HeroText className="text-[11px] font-semibold uppercase tracking-[0.16em] text-neutral-400">
        {label}
      </HeroText>
      <HeroText className="mt-1 text-[14px] font-semibold text-neutral-900">
        {value}
      </HeroText>
    </View>
  );
}

function StatusBanner({
  tone,
  message,
}: {
  tone: 'success' | 'error';
  message: string;
}) {
  const toneStyles =
    tone === 'success'
      ? 'border-emerald-100 bg-emerald-50 text-emerald-700'
      : 'border-red-100 bg-red-50 text-red-700';

  return (
    <View className={`mt-4 rounded-[20px] border px-4 py-3 ${toneStyles}`}>
      <HeroText className="text-[13px] font-semibold">{message}</HeroText>
    </View>
  );
}

export default function AdminInventoryDetailScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ id?: string }>();
  const token = useBackendAccessToken();
  const strings = useStrings();
  const updateStringItem = useAppStore((state) => state.updateStringItem);
  const stringItem = strings.find((item) => item.id === params.id);

  const [form, setForm] = useState<InventoryFormState | null>(
    stringItem ? toFormState(stringItem) : null,
  );
  const [initialNormalizedForm, setInitialNormalizedForm] = useState<NormalizedFormState | null>(
    stringItem ? normalizeForm(toFormState(stringItem)) : null,
  );
  const [errors, setErrors] = useState<FormErrors>({});
  const [statusBanner, setStatusBanner] = useState<{
    tone: 'success' | 'error';
    message: string;
  } | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isPickingImage, setIsPickingImage] = useState(false);
  const [isHydrating, setIsHydrating] = useState(false);
  const [pendingImageUpload, setPendingImageUpload] = useState<{
    uri: string;
    name: string;
    type: string;
  } | null>(null);

  useEffect(() => {
    if (!stringItem) {
      return;
    }

    const nextForm = toFormState(stringItem);
    setForm(nextForm);
    setInitialNormalizedForm(normalizeForm(nextForm));
    setErrors({});
    setPendingImageUpload(null);
  }, [stringItem]);

  useEffect(() => {
    if (!token || !params.id) {
      return;
    }

    let cancelled = false;

    const hydrateInventoryItem = async () => {
      setIsHydrating(true);
      try {
        const [inventoryResponse, officialPerformance] = await Promise.all([
          backendApi.adminFetchInventoryString(token, params.id!),
          backendApi.adminFetchOfficialPerformance(token, params.id!).catch((error) => {
            if (error instanceof BackendApiError && error.statusCode === 404) {
              return null;
            }
            throw error;
          }),
        ]);

        if (cancelled) {
          return;
        }

        let mapped = mapBackendInventoryStringToStringItem(inventoryResponse);
        const officialScores = mapOfficialPerformanceToPerformanceScores(
          officialPerformance,
          mapped.ratings,
        );

        if (serializeComparable(officialScores) !== serializeComparable(mapped.ratings)) {
          const scorePatch = buildLocalPatch(
            mapped,
            normalizeForm({
              ...toFormState(mapped),
              powerScore: String(officialScores.power),
              controlScore: String(officialScores.control),
              durabilityScore: String(officialScores.durability),
              comfortScore: String(officialScores.comfort),
              soundScore: String(officialScores.sound),
            }),
          );
          mapped = { ...mapped, ...scorePatch } as StringItem;
        }

        updateStringItem(mapped.id, mapped);
        setStatusBanner(null);
      } catch (loadError) {
        if (!cancelled) {
          setStatusBanner({
            tone: 'error',
            message:
              loadError instanceof BackendApiError
                ? loadError.message
                : 'Failed to load the latest string details.',
          });
        }
      } finally {
        if (!cancelled) {
          setIsHydrating(false);
        }
      }
    };

    void hydrateInventoryItem();

    return () => {
      cancelled = true;
    };
  }, [params.id, token, updateStringItem]);

  const normalizedForm = useMemo(
    () => (form ? normalizeForm(form) : null),
    [form],
  );

  const previewItem = useMemo(() => {
    if (!stringItem || !normalizedForm) {
      return null;
    }
    return { ...stringItem, ...buildLocalPatch(stringItem, normalizedForm) } as StringItem;
  }, [normalizedForm, stringItem]);

  const isDirty = useMemo(() => {
    if (!normalizedForm || !initialNormalizedForm) {
      return false;
    }
    return serializeComparable(normalizedForm) !== serializeComparable(initialNormalizedForm);
  }, [initialNormalizedForm, normalizedForm]);

  const hasCatalogServerChanges = useMemo(() => {
    if (!normalizedForm || !initialNormalizedForm) {
      return false;
    }
    return (
      serializeComparable(comparableCatalogState(normalizedForm)) !==
      serializeComparable(comparableCatalogState(initialNormalizedForm))
    );
  }, [initialNormalizedForm, normalizedForm]);

  const hasScoreServerChanges = useMemo(() => {
    if (!normalizedForm || !initialNormalizedForm) {
      return false;
    }
    return (
      serializeComparable(comparableScoreState(normalizedForm)) !==
      serializeComparable(comparableScoreState(initialNormalizedForm))
    );
  }, [initialNormalizedForm, normalizedForm]);

  const hasInventoryServerChanges = useMemo(() => {
    if (!normalizedForm || !initialNormalizedForm) {
      return false;
    }
    return (
      serializeComparable(comparableInventoryState(normalizedForm)) !==
      serializeComparable(comparableInventoryState(initialNormalizedForm))
    );
  }, [initialNormalizedForm, normalizedForm]);

  const hasImageServerChanges = useMemo(() => {
    if (!normalizedForm || !initialNormalizedForm) {
      return false;
    }
    return normalizedForm.imageUrl !== initialNormalizedForm.imageUrl || pendingImageUpload != null;
  }, [initialNormalizedForm, normalizedForm, pendingImageUpload]);

  if ((isHydrating && !form) || (params.id && !stringItem && Boolean(token))) {
    return (
      <AppScreen
        tone="admin"
        headerVariant="secondary"
        showBackButton
        onBackPress={() => router.back()}
        title="Edit String"
        subtitle="Loading the latest catalog and inventory data."
      >
        <AppCard variant="subtle" padding="md">
          <HeroText className="text-[14px] font-semibold text-neutral-900">
            Fetching current string details...
          </HeroText>
          <HeroText className="mt-1 text-[12px] leading-5 text-neutral-500">
            The editor will appear once the latest backend data is ready.
          </HeroText>
        </AppCard>
      </AppScreen>
    );
  }

  if (!stringItem || !form || !previewItem || !normalizedForm) {
    return (
      <AppScreen
        tone="admin"
        headerVariant="secondary"
        showBackButton
        onBackPress={() => router.back()}
        title="Edit String"
        subtitle="Unable to find this string in the current inventory state."
      >
        <AppCard variant="subtle" padding="md">
          <HeroText className="text-[14px] font-semibold text-neutral-900">
            This inventory item is unavailable right now.
          </HeroText>
          <HeroText className="mt-1 text-[12px] leading-5 text-neutral-500">
            Return to inventory and reopen the item after the list refreshes.
          </HeroText>
        </AppCard>
      </AppScreen>
    );
  }

  const summaryPrice = getInventoryPriceLabel(previewItem);

  const setField = <K extends keyof InventoryFormState>(
    key: K,
    value: InventoryFormState[K],
  ) => {
    setForm((current) => (current ? { ...current, [key]: value } : current));
    setErrors((current) => {
      if (!current[key]) {
        return current;
      }

      const nextErrors = { ...current };
      delete nextErrors[key];
      return nextErrors;
    });
    setStatusBanner(null);
  };

  const setScoreField = (key: ScoreKey, value: string) => {
    setField(SCORE_FORM_KEYS[key], value);
  };

  const pickImage = async () => {
    setIsPickingImage(true);
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
      setPendingImageUpload({
        uri: asset.uri,
        name: asset.fileName || `string-image-${Date.now()}.jpg`,
        type: asset.mimeType || 'image/jpeg',
      });
      setField('imageUrl', asset.uri);
    } finally {
      setIsPickingImage(false);
    }
  };

  const removeImage = () => {
    setPendingImageUpload(null);
    setField('imageUrl', undefined);
  };

  const saveInventory = async () => {
    const validation = validateForm(form);
    if (!validation.success) {
      setErrors(validation.errors);
      setStatusBanner({
        tone: 'error',
        message: 'Review the highlighted fields before saving.',
      });
      return;
    }

    setErrors({});
    setStatusBanner(null);

    if (!token) {
      setStatusBanner({
        tone: 'error',
        message: 'Your admin session expired. Sign in again before saving.',
      });
      return;
    }

    if (
      !hasCatalogServerChanges &&
      !hasScoreServerChanges &&
      !hasInventoryServerChanges &&
      !hasImageServerChanges
    ) {
      setStatusBanner({
        tone: 'success',
        message: 'No backend changes were needed.',
      });
      return;
    }

    setIsSaving(true);
    let savedServerChanges = false;
    try {
      const hasStructuredServerChanges =
        hasCatalogServerChanges ||
        hasScoreServerChanges ||
        hasInventoryServerChanges;

      if (hasStructuredServerChanges) {
        await backendApi.adminUpdateStringEditor(token!, stringItem.id, {
          ...(hasCatalogServerChanges
            ? { catalog: buildCatalogPayload(validation.data, stringItem) }
            : {}),
          ...(hasScoreServerChanges
            ? {
                official_performance: buildOfficialPerformancePayload(
                  validation.data,
                ),
              }
            : {}),
          ...(hasInventoryServerChanges
            ? { inventory: buildInventoryPayload(validation.data) }
            : {}),
        });
        savedServerChanges = true;
      }

      let imageSaveError: unknown = null;
      if (hasImageServerChanges) {
        try {
          if (pendingImageUpload && validation.data.imageUrl) {
            await backendApi.adminUploadStringImage(token!, stringItem.id, {
              photo: pendingImageUpload,
            });
            savedServerChanges = true;
          } else if (
            !validation.data.imageUrl &&
            initialNormalizedForm?.imageUrl &&
            isPersistedBackendImage(initialNormalizedForm.imageUrl)
          ) {
            await backendApi.adminDeleteStringImage(token!, stringItem.id);
            savedServerChanges = true;
          }
        } catch (error) {
          imageSaveError = error;
        }
      }

      const [inventoryResponse, officialPerformance] = await Promise.all([
        backendApi.adminFetchInventoryString(token!, stringItem.id),
        backendApi.adminFetchOfficialPerformance(token!, stringItem.id).catch((error) => {
          if (error instanceof BackendApiError && error.statusCode === 404) {
            return null;
          }
          throw error;
        }),
      ]);
      let mapped = mapBackendInventoryStringToStringItem(inventoryResponse);
      const officialScores = mapOfficialPerformanceToPerformanceScores(
        officialPerformance,
        mapped.ratings,
      );

      if (serializeComparable(officialScores) !== serializeComparable(mapped.ratings)) {
        const scorePatch = buildLocalPatch(
          mapped,
          normalizeForm({
            ...toFormState(mapped),
            powerScore: String(officialScores.power),
            controlScore: String(officialScores.control),
            durabilityScore: String(officialScores.durability),
            comfortScore: String(officialScores.comfort),
            soundScore: String(officialScores.sound),
          }),
        );
        mapped = { ...mapped, ...scorePatch } as StringItem;
      }

      updateStringItem(stringItem.id, mapped);

      if (imageSaveError) {
        const imageErrorMessage =
          imageSaveError instanceof BackendApiError
            ? imageSaveError.message
            : 'The image update could not be completed.';
        const partialSuccessMessage = hasStructuredServerChanges
          ? `Catalog, score, and shop changes were saved, but the image was not updated. ${imageErrorMessage}`
          : imageErrorMessage;
        setStatusBanner({
          tone: 'error',
          message: partialSuccessMessage,
        });
        showAlert('Image not saved', partialSuccessMessage);
        return;
      }

      const successMessage =
        'Catalog information, scores, media, and shop data were synced successfully.';

      setStatusBanner({
        tone: 'success',
        message: successMessage,
      });
      showAlert('String saved', successMessage);
    } catch (saveError) {
      const errorMessage =
        saveError instanceof BackendApiError
          ? saveError.message
          : 'Failed to save the latest string changes.';
      setStatusBanner({
        tone: 'error',
        message: savedServerChanges
          ? `Changes were saved, but the latest record could not be refreshed. ${errorMessage}`
          : errorMessage,
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <AppScreen
      tone="admin"
      headerVariant="secondary"
      showBackButton
      onBackPress={() => router.back()}
      title="Edit String"
      subtitle="Manage catalog info, scores, media, and shop inventory."
      footer={
        <View className="gap-2 border-t border-[#DCE6F7] bg-[#F7FAFF] pt-3">
          <AppButton
            label={isDirty ? 'Save string changes' : 'All changes saved'}
            onPress={() => void saveInventory()}
            isLoading={isSaving}
            isDisabled={!isDirty}
          />
          <AppButton label="Back to inventory" variant="outline" onPress={() => router.back()} />
        </View>
      }
    >
      <AppSection variant="compact">
        <AppCard variant="highlighted" padding="md">
          <View className="flex-row gap-4">
            <AdminStringThumbnail item={previewItem} size={92} />
            <View className="min-w-0 flex-1">
              <View className="flex-row items-start justify-between gap-3">
                <View className="min-w-0 flex-1">
                  <HeroText
                    className="text-[18px] font-bold tracking-tight text-neutral-950"
                    numberOfLines={2}
                  >
                    {buildStringDisplayName({
                      brand: normalizedForm.brand || stringItem.brand,
                      model: normalizedForm.modelName || stringItem.model,
                    })}
                  </HeroText>
                  <HeroText className="mt-1 text-[13px] font-semibold text-neutral-500">
                    {normalizedForm.brand || stringItem.brand}
                  </HeroText>
                </View>
                {isDirty ? <AppChip label="Unsaved" variant="warning" /> : null}
              </View>

              <View className="mt-3 flex-row flex-wrap gap-2">
                <AppChip
                  label={formatSingleGauge(
                    previewItem.catalog.gaugeMinMm ?? previewItem.catalog.gaugeMaxMm,
                    previewItem.gauge,
                  )}
                  variant="secondary"
                />
                <AppChip label={previewItem.catalog.mainTrait} variant="neutral" />
                <AppChip
                  label={formatAvailability(previewItem.inventory.availabilityStatus)}
                  variant={
                    previewItem.inventory.availabilityStatus === 'out_of_stock'
                      ? 'danger'
                      : previewItem.inventory.availabilityStatus === 'low_stock'
                        ? 'warning'
                        : 'primary'
                  }
                />
                <AppChip label={`Stock ${previewItem.inventory.stockQty}`} variant="neutral" />
                <AppChip label={summaryPrice.label} variant="secondary" />
              </View>
            </View>
          </View>

          <View className="mt-4 flex-row flex-wrap gap-3">
            <SummaryDetail
              label="Gauge"
              value={formatSingleGauge(
                previewItem.catalog.gaugeMinMm ?? previewItem.catalog.gaugeMaxMm,
                previewItem.gauge,
              )}
            />
            <SummaryDetail label="Main trait" value={previewItem.catalog.mainTrait} />
            <SummaryDetail
              label="Availability"
              value={formatAvailability(previewItem.inventory.availabilityStatus)}
            />
            <SummaryDetail
              label="Price"
              value={
                previewItem.inventory.priceStatus === 'quoted_at_shop'
                  ? 'Quoted at shop'
                  : previewItem.inventory.priceStatus === 'pending'
                    ? 'Price pending'
                    : `RM ${(previewItem.inventory.price ?? 0).toFixed(2)}`
              }
            />
          </View>
        </AppCard>
      </AppSection>

      <AppSection
        eyebrow="Catalog information"
        title="Catalog Information"
        subtitle="Core badminton string data used across admin, recommendation, and comparison surfaces."
      >
        <View className="flex-row gap-3">
          <AppInput
            label="Brand"
            value={form.brand}
            onChangeText={(value) => setField('brand', value)}
            error={errors.brand}
            className="flex-1"
          />
          <AppInput
            label="Model name"
            value={form.modelName}
            onChangeText={(value) => setField('modelName', value)}
            error={errors.modelName}
            className="flex-1"
          />
        </View>
        <AppInput
          label="Localized / Chinese name"
          value={form.localizedName}
          onChangeText={(value) => setField('localizedName', value)}
          error={errors.localizedName}
        />
        <AppInput
          label="Description"
          value={form.description}
          onChangeText={(value) => setField('description', value)}
          error={errors.description}
          multiline
          inputClassName="min-h-28"
        />
        <AppInput
          label="Material / construction"
          value={form.material}
          onChangeText={(value) => setField('material', value)}
          error={errors.material}
        />
        <View className="flex-row gap-3">
          <AppInput
            label="Gauge (mm)"
            value={form.gaugeMm}
            onChangeText={(value) => setField('gaugeMm', value)}
            error={errors.gaugeMm}
            keyboardType="decimal-pad"
            className="flex-1"
          />
          <AppInput
            label="Main trait"
            value={form.mainTrait}
            onChangeText={(value) => setField('mainTrait', value)}
            error={errors.mainTrait}
            className="flex-1"
          />
        </View>
        <View className="flex-row gap-3">
          <AppInput
            label="Tension min (lbs)"
            value={form.tensionMinLbs}
            onChangeText={(value) => setField('tensionMinLbs', value)}
            error={errors.tensionMinLbs}
            keyboardType="numeric"
            className="flex-1"
          />
          <AppInput
            label="Tension max (lbs)"
            value={form.tensionMaxLbs}
            onChangeText={(value) => setField('tensionMaxLbs', value)}
            error={errors.tensionMaxLbs}
            keyboardType="numeric"
            className="flex-1"
          />
        </View>
        <ChoiceGroup
          label="Category tags"
          value={form.category}
          options={CATEGORY_OPTIONS}
          onChange={(value) => setField('category', value)}
        />
        <ChoiceGroup
          label="Visible status"
          value={form.isActive}
          options={[...CATALOG_VISIBILITY_OPTIONS]}
          onChange={(value) => setField('isActive', value)}
          helperText="Hidden strings stay editable in admin while being removed from the live shelf."
        />
      </AppSection>

      <AppSection
        eyebrow="Performance scores"
        title="Performance Scores"
        subtitle="Editable 1 to 10 admin scores for recommendation-facing signals."
      >
        {SCORE_FIELDS.map((field) => (
          <ScoreRow
            key={field.key}
            label={field.label}
            value={form[SCORE_FORM_KEYS[field.key]] as string}
            error={errors[SCORE_FORM_KEYS[field.key]]}
            onChangeText={(value) => setScoreField(field.key, value)}
          />
        ))}
      </AppSection>

      <AppSection
        eyebrow="Media"
        title="Media"
        subtitle="Upload, replace, or remove the product image used in admin inventory surfaces."
      >
        <AppCard variant="default" padding="md">
          <View className="items-center gap-4">
            <AdminStringThumbnail item={previewItem} size={120} />
            <HeroText className="text-center text-[13px] leading-5 text-neutral-500">
              {form.imageUrl
                ? 'The selected image will be used for the admin shelf preview on this device.'
                : 'No image added yet. Upload a clean pack or spool image for faster admin identification.'}
            </HeroText>
            <View className="w-full flex-row flex-wrap gap-2">
              <AppButton
                label={form.imageUrl ? 'Replace image' : 'Upload image'}
                size="sm"
                onPress={() => void pickImage()}
                isLoading={isPickingImage}
                leadingIcon={<ImagePlus size={15} color="#FFFFFF" />}
              />
              <AppButton
                label="Remove image"
                size="sm"
                variant="outline"
                onPress={removeImage}
                isDisabled={!form.imageUrl}
                leadingIcon={<Trash2 size={15} color="#475569" />}
              />
            </View>
          </View>
        </AppCard>
      </AppSection>

      <AppSection
        eyebrow="Shop data"
        title="Shop Data"
        subtitle="Vendor-side pricing, stock, and availability controls for the current store."
      >
        <ChoiceGroup
          label="Pricing mode"
          value={form.pricingMode}
          options={PRICING_MODE_OPTIONS}
          onChange={(value) => setField('pricingMode', value)}
          helperText="Fixed price requires a value. Pending and quoted-at-shop save without a shelf price."
        />
        <View className="flex-row gap-3">
          <AppInput
            label="Price (RM)"
            value={form.priceRm}
            onChangeText={(value) => setField('priceRm', value)}
            error={errors.priceRm}
            keyboardType="decimal-pad"
            isDisabled={form.pricingMode !== 'fixed_price'}
            className="flex-1"
            helperText={
              form.pricingMode === 'fixed_price'
                ? 'Required for a fixed shelf price.'
                : 'Disabled while pricing mode is pending or quoted at shop.'
            }
          />
          <AppInput
            label="Stock level"
            value={form.stockLevel}
            onChangeText={(value) => setField('stockLevel', value)}
            error={errors.stockLevel}
            keyboardType="numeric"
            className="flex-1"
          />
        </View>
        <ChoiceGroup
          label="Availability"
          value={form.availabilityStatus}
          options={AVAILABILITY_OPTIONS}
          onChange={(value) => setField('availabilityStatus', value)}
          helperText="Zero stock will still save as out of stock. Low-stock versus in-stock is otherwise treated as admin UI state."
        />
        <AppInput
          label="Shop note"
          value={form.shopNote}
          onChangeText={(value) => setField('shopNote', value)}
          error={errors.shopNote}
          multiline
          inputClassName="min-h-24"
          helperText="Use for counter instructions, supplier notes, or shop-specific selling context."
        />
      </AppSection>

      {statusBanner ? (
        <StatusBanner tone={statusBanner.tone} message={statusBanner.message} />
      ) : null}

    </AppScreen>
  );
}
