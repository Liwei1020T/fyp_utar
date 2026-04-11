import React, { useEffect, useMemo, useState } from 'react';
import { Alert, View } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { ImagePlus, Trash2 } from 'lucide-react-native';
import { AdminInventoryPreviewCard, AdminStringThumbnail } from '../../../components/admin/inventory/AdminInventoryCard';
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
  sanitizePerformanceScores,
} from '../../../lib/inventory';
import { formatLabel } from '../../../lib/formatters';
import { BackendApiError, backendApi } from '../../../services/backendApi';
import { mapBackendInventoryStringToStringItem } from '../../../services/backendMappers';
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

interface InventoryFormState {
  brand: string;
  modelName: string;
  localizedName: string;
  gaugeMinMm: string;
  gaugeMaxMm: string;
  material: string;
  tensionMinLbs: string;
  tensionMaxLbs: string;
  mainTrait: string;
  category: StringItem['category'];
  description: string;
  isActive: boolean;
  powerScore: string;
  controlScore: string;
  durabilityScore: string;
  comfortScore: string;
  soundScore: string;
  imageUrl?: string;
  price: string;
  priceStatus: InventoryPriceStatus;
  stockLevel: string;
  availabilityStatus: InventoryAvailability;
  shopNote: string;
}

const CATALOG_VISIBILITY_OPTIONS = [
  { id: true, label: 'Visible' },
  { id: false, label: 'Hidden' },
] as const;

const PRICE_STATUS_OPTIONS: Array<{ id: InventoryPriceStatus; label: string }> = [
  { id: 'priced', label: 'Fixed price' },
  { id: 'pending', label: 'Price pending' },
  { id: 'quoted_at_shop', label: 'Quoted at shop' },
];

const AVAILABILITY_OPTIONS: Array<{ id: InventoryAvailability; label: string }> = [
  { id: 'in_stock', label: 'In Stock' },
  { id: 'low_stock', label: 'Low Stock' },
  { id: 'out_of_stock', label: 'Out of Stock' },
];

const CATEGORY_OPTIONS: Array<{ id: StringItem['category']; label: string }> = [
  { id: 'repulsion', label: 'Repulsion' },
  { id: 'balanced', label: 'Balanced' },
  { id: 'control', label: 'Control' },
  { id: 'durable', label: 'Durable' },
];

const SCORE_FIELDS: Array<{ key: ScoreKey; label: string }> = [
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

function toFormState(item: StringItem): InventoryFormState {
  return {
    brand: item.catalog.brand,
    modelName: item.catalog.modelName,
    localizedName: item.catalog.localizedName ?? '',
    gaugeMinMm: item.catalog.gaugeMinMm?.toFixed(2) ?? '',
    gaugeMaxMm: item.catalog.gaugeMaxMm?.toFixed(2) ?? '',
    material: item.catalog.material,
    tensionMinLbs: item.catalog.tensionMinLbs?.toString() ?? '',
    tensionMaxLbs: item.catalog.tensionMaxLbs?.toString() ?? '',
    mainTrait: item.catalog.mainTrait,
    category: item.catalog.category,
    description: item.catalog.description,
    isActive: item.catalog.isActive,
    powerScore: String(item.catalog.performanceScores.power),
    controlScore: String(item.catalog.performanceScores.control),
    durabilityScore: String(item.catalog.performanceScores.durability),
    comfortScore: String(item.catalog.performanceScores.comfort),
    soundScore: String(item.catalog.performanceScores.sound),
    imageUrl: item.catalog.imageUrl ?? item.imageUrl,
    price: item.inventory.price != null ? String(item.inventory.price) : '',
    priceStatus: item.inventory.priceStatus,
    stockLevel: String(item.inventory.stockQty),
    availabilityStatus: item.inventory.availabilityStatus,
    shopNote: item.inventory.shopNote ?? '',
  };
}

function parseNumber(value: string, fallback: number | null = null) {
  if (!value.trim()) {
    return fallback;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
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
  options: Array<{ id: T; label: string }>;
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
  onChangeText,
}: {
  label: string;
  value: string;
  onChangeText: (value: string) => void;
}) {
  return (
    <View className="mb-3 flex-row items-center gap-3 rounded-[18px] border border-[#D8E2EE] bg-white px-4 py-3">
      <View className="flex-1">
        <HeroText className="text-[14px] font-semibold text-neutral-900">
          {label}
        </HeroText>
        <HeroText className="mt-0.5 text-[12px] text-neutral-500">
          Scale 1 to 10
        </HeroText>
      </View>
      <View className="h-11 w-[74px] rounded-[14px] border border-[#D8E2EE] bg-[#F8FBFF] px-3">
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
  );
}

function buildLocalPatch(
  stringItem: StringItem,
  form: InventoryFormState,
): Partial<StringItem> {
  const gaugeMinMm = parseNumber(form.gaugeMinMm, stringItem.catalog.gaugeMinMm);
  const gaugeMaxMm = parseNumber(form.gaugeMaxMm, stringItem.catalog.gaugeMaxMm);
  const tensionMinLbs = parseNumber(
    form.tensionMinLbs,
    stringItem.catalog.tensionMinLbs,
  );
  const tensionMaxLbs = parseNumber(
    form.tensionMaxLbs,
    stringItem.catalog.tensionMaxLbs,
  );
  const price =
    form.priceStatus === 'priced'
      ? parseNumber(form.price, stringItem.inventory.price)
      : null;
  const stockQty = Math.max(0, parseNumber(form.stockLevel, stringItem.inventory.stockQty) ?? 0);
  const availabilityStatus =
    stockQty === 0
      ? 'out_of_stock'
      : deriveAvailabilityStatus(stockQty, form.availabilityStatus);
  const performanceScores = sanitizePerformanceScores(
    {
      power: parseNumber(form.powerScore, stringItem.catalog.performanceScores.power) ?? 6,
      control:
        parseNumber(form.controlScore, stringItem.catalog.performanceScores.control) ?? 6,
      durability:
        parseNumber(
          form.durabilityScore,
          stringItem.catalog.performanceScores.durability,
        ) ?? 6,
      comfort:
        parseNumber(form.comfortScore, stringItem.catalog.performanceScores.comfort) ?? 6,
      sound: parseNumber(form.soundScore, stringItem.catalog.performanceScores.sound) ?? 6,
    },
    stringItem.catalog.performanceScores,
  );
  const catalog = {
    ...stringItem.catalog,
    brand: form.brand.trim(),
    modelName: form.modelName.trim(),
    localizedName: form.localizedName.trim() || undefined,
    gaugeMinMm,
    gaugeMaxMm,
    material: form.material.trim(),
    tensionMinLbs,
    tensionMaxLbs,
    mainTrait: form.mainTrait.trim(),
    category: form.category,
    description: form.description.trim(),
    performanceScores,
    imageUrl: form.imageUrl,
    isActive: form.isActive,
    updatedAt: new Date().toISOString(),
  };
  const inventory = {
    ...stringItem.inventory,
    stockQty,
    price,
    priceStatus: derivePriceStatus(price, form.priceStatus),
    availabilityStatus,
    shopNote: form.shopNote.trim() || undefined,
    updatedAt: new Date().toISOString(),
  };
  const retainedTags = stringItem.inventoryTags.filter((tag) => {
    const normalized = tag.toLowerCase();
    return (
      normalized !== stringItem.catalog.mainTrait.toLowerCase()
      && normalized !== formatLabel(stringItem.category).toLowerCase()
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
      tensionMinLbs ?? stringItem.recommendedTension[0],
      tensionMaxLbs ?? stringItem.recommendedTension[1],
    ],
    tensionMinLbs,
    tensionMaxLbs,
    ratings: performanceScores,
    tensionNote: `Recommended at ${
      tensionMinLbs ?? stringItem.recommendedTension[0]
    }-${tensionMaxLbs ?? stringItem.recommendedTension[1]} lbs for the current shop setup.`,
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

function compareMasterData(
  original: StringItem,
  nextPatch: Partial<StringItem>,
) {
  return JSON.stringify({
    catalog: original.catalog,
    ratings: original.ratings,
    imageUrl: original.imageUrl,
    isActive: original.isActive,
    topLevel: {
      brand: original.brand,
      model: original.model,
      localizedName: original.localizedName,
      category: original.category,
      mainTrait: original.mainTrait,
      gaugeMinMm: original.gaugeMinMm,
      gaugeMaxMm: original.gaugeMaxMm,
      description: original.description,
    },
  }) !== JSON.stringify({
    catalog: nextPatch.catalog,
    ratings: nextPatch.ratings,
    imageUrl: nextPatch.imageUrl,
    isActive: nextPatch.isActive,
    topLevel: {
      brand: nextPatch.brand,
      model: nextPatch.model,
      localizedName: nextPatch.localizedName,
      category: nextPatch.category,
      mainTrait: nextPatch.mainTrait,
      gaugeMinMm: nextPatch.gaugeMinMm,
      gaugeMaxMm: nextPatch.gaugeMaxMm,
      description: nextPatch.description,
    },
  });
}

export default function AdminInventoryDetailScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ id?: string }>();
  const token = useBackendAccessToken();
  const strings = useStrings();
  const sessionSource = useAppStore((state) => state.sessionSource);
  const updateStringItem = useAppStore((state) => state.updateStringItem);
  const stringItem = strings.find((item) => item.id === params.id);
  const [form, setForm] = useState<InventoryFormState | null>(
    stringItem ? toFormState(stringItem) : null,
  );
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isPickingImage, setIsPickingImage] = useState(false);

  useEffect(() => {
    if (stringItem) {
      setForm(toFormState(stringItem));
    }
  }, [stringItem]);

  useEffect(() => {
    if (!token || !params.id) {
      return;
    }

    const stringId = params.id;
    let cancelled = false;

    const hydrateInventoryItem = async () => {
      try {
        const response = await backendApi.adminFetchInventoryString(token, stringId);
        if (cancelled) {
          return;
        }
        const mapped = mapBackendInventoryStringToStringItem(response);
        updateStringItem(mapped.id, mapped);
      } catch (loadError) {
        if (!cancelled) {
          setError(
            loadError instanceof BackendApiError
              ? loadError.message
              : 'Failed to load inventory item.',
          );
        }
      }
    };

    void hydrateInventoryItem();

    return () => {
      cancelled = true;
    };
  }, [params.id, token, updateStringItem]);

  const previewItem = useMemo(() => {
    if (!stringItem || !form) {
      return null;
    }
    return { ...stringItem, ...buildLocalPatch(stringItem, form) } as StringItem;
  }, [form, stringItem]);

  if (!stringItem || !form || !previewItem) {
    return (
      <AppScreen
        tone="admin"
        headerVariant="secondary"
        showBackButton
        onBackPress={() => router.back()}
        title="Inventory item"
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

  const backendSyncLimited = sessionSource === 'backend' && Boolean(token);

  const setField = <K extends keyof InventoryFormState>(
    key: K,
    value: InventoryFormState[K],
  ) => {
    setForm((current) => (current ? { ...current, [key]: value } : current));
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

      setField('imageUrl', result.assets[0].uri);
    } finally {
      setIsPickingImage(false);
    }
  };

  const removeImage = () => {
    setField('imageUrl', undefined);
  };

  const saveInventory = async () => {
    const localPatch = buildLocalPatch(stringItem, form);
    const hasMasterDataChanges = compareMasterData(stringItem, localPatch);
    const nextInventory = localPatch.inventory ?? stringItem.inventory;

    setError(null);

    if (!backendSyncLimited) {
      updateStringItem(stringItem.id, localPatch);
      Alert.alert('String saved', 'Catalog, score, media, and shop data were updated locally.');
      return;
    }

    setIsSaving(true);
    try {
      const updated = await backendApi.adminUpdateInventoryString(token!, stringItem.id, {
        price_rm: nextInventory.priceStatus === 'priced' ? nextInventory.price : null,
        stock_level: nextInventory.stockQty,
        admin_note: nextInventory.shopNote ?? null,
      });
      const mapped = mapBackendInventoryStringToStringItem(updated);

      updateStringItem(
        stringItem.id,
        hasMasterDataChanges
          ? {
              ...mapped,
              ...localPatch,
              price: nextInventory.price ?? 0,
              priceStatus: nextInventory.priceStatus,
              stockLevel: nextInventory.stockQty,
              availability: nextInventory.availabilityStatus,
              adminNote: nextInventory.shopNote,
              inventoryUpdatedAt: mapped.inventoryUpdatedAt ?? nextInventory.updatedAt,
              inventory: { ...mapped.inventory, ...nextInventory },
              catalog: localPatch.catalog,
            }
          : mapped,
      );

      Alert.alert(
        hasMasterDataChanges ? 'Shop data synced' : 'String saved',
        hasMasterDataChanges
          ? 'Price, stock, and shop note were synced to the backend. Catalog, score, and media edits remain local until master-data endpoints are added.'
          : 'Price, stock, and shop note were synced to the backend.',
      );
    } catch (saveError) {
      setError(
        saveError instanceof BackendApiError
          ? saveError.message
          : 'Failed to update inventory.',
      );
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
      title={buildStringDisplayName(stringItem)}
      subtitle="Edit string data, media, scores, and shop inventory."
    >
      {backendSyncLimited ? (
        <AppSection variant="compact">
          <AppCard variant="subtle" padding="md">
            <HeroText className="text-[13px] font-semibold text-neutral-900">
              Backend sync scope
            </HeroText>
            <HeroText className="mt-1 text-[12px] leading-5 text-neutral-500">
              The current live backend persists shop data only: price, stock level, and shop note. Catalog details, media, visibility, and score edits stay local in this prototype until master-data endpoints are added.
            </HeroText>
          </AppCard>
        </AppSection>
      ) : null}

      <AppSection eyebrow="String preview" title="Current shelf snapshot" variant="compact">
        <AdminInventoryPreviewCard item={previewItem} />
      </AppSection>

      <AppSection
        eyebrow="Catalog information"
        title="Master data"
        subtitle="Core string data shared across recommendation, comparison, and admin views."
      >
        <View className="flex-row gap-3">
          <AppInput
            label="Brand"
            value={form.brand}
            onChangeText={(value) => setField('brand', value)}
            className="flex-1"
          />
          <AppInput
            label="Model name"
            value={form.modelName}
            onChangeText={(value) => setField('modelName', value)}
            className="flex-1"
          />
        </View>
        <AppInput
          label="Localized / Chinese name"
          value={form.localizedName}
          onChangeText={(value) => setField('localizedName', value)}
        />
        <View className="flex-row gap-3">
          <AppInput
            label="Gauge min (mm)"
            value={form.gaugeMinMm}
            onChangeText={(value) => setField('gaugeMinMm', value)}
            keyboardType="decimal-pad"
            className="flex-1"
          />
          <AppInput
            label="Gauge max (mm)"
            value={form.gaugeMaxMm}
            onChangeText={(value) => setField('gaugeMaxMm', value)}
            keyboardType="decimal-pad"
            className="flex-1"
          />
        </View>
        <AppInput
          label="Material"
          value={form.material}
          onChangeText={(value) => setField('material', value)}
        />
        <View className="flex-row gap-3">
          <AppInput
            label="Tension min (lbs)"
            value={form.tensionMinLbs}
            onChangeText={(value) => setField('tensionMinLbs', value)}
            keyboardType="numeric"
            className="flex-1"
          />
          <AppInput
            label="Tension max (lbs)"
            value={form.tensionMaxLbs}
            onChangeText={(value) => setField('tensionMaxLbs', value)}
            keyboardType="numeric"
            className="flex-1"
          />
        </View>
        <AppInput
          label="Main trait"
          value={form.mainTrait}
          onChangeText={(value) => setField('mainTrait', value)}
        />
        <ChoiceGroup
          label="Category"
          value={form.category}
          options={CATEGORY_OPTIONS}
          onChange={(value) => setField('category', value)}
        />
        <ChoiceGroup
          label="Visible status"
          value={form.isActive}
          options={[...CATALOG_VISIBILITY_OPTIONS]}
          onChange={(value) => setField('isActive', value)}
          helperText="Hidden strings stay in the catalog editor but can be excluded from live recommendation and shelf views."
        />
        <AppInput
          label="Description"
          value={form.description}
          onChangeText={(value) => setField('description', value)}
          multiline
          inputClassName="min-h-28"
        />
      </AppSection>

      <AppSection
        eyebrow="Performance scores"
        title="Recommendation signals"
        subtitle="These 1 to 10 scores should stay aligned with radar charts and recommendation logic."
      >
        {SCORE_FIELDS.map((field) => (
          <ScoreRow
            key={field.key}
            label={field.label}
            value={form[SCORE_FORM_KEYS[field.key]] as string}
            onChangeText={(value) => setScoreField(field.key, value)}
          />
        ))}
      </AppSection>

      <AppSection
        eyebrow="Media"
        title="String image"
        subtitle="Use a clean pack or spool image so the counter team can identify the item quickly."
      >
        <AppCard variant="default" padding="md">
          <View className="flex-row items-center gap-4">
            <AdminStringThumbnail item={previewItem} size={96} />
            <View className="min-w-0 flex-1">
              <HeroText className="text-[15px] font-semibold text-neutral-900">
                {buildStringDisplayName(previewItem)}
              </HeroText>
              <HeroText className="mt-1 text-[12px] leading-5 text-neutral-500">
                {form.imageUrl
                  ? 'Current image will be used for inventory cards, detail preview, and future backend media sync.'
                  : 'No image uploaded yet. Add one so the admin desk can identify the string faster.'}
              </HeroText>
            </View>
          </View>
          <View className="mt-4 flex-row flex-wrap gap-2">
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
        </AppCard>
      </AppSection>

      <AppSection
        eyebrow="Shop data"
        title="Inventory and pricing"
        subtitle="Vendor-side shelf data for stock control, pricing, and counter notes."
      >
        <ChoiceGroup
          label="Price state"
          value={form.priceStatus}
          options={PRICE_STATUS_OPTIONS}
          onChange={(value) => setField('priceStatus', value)}
          helperText="Use pending or quoted at shop instead of storing a fake RM 0.00."
        />
        <View className="flex-row gap-3">
          <AppInput
            label="Price (RM)"
            value={form.price}
            onChangeText={(value) => setField('price', value)}
            keyboardType="decimal-pad"
            className="flex-1"
            helperText={
              form.priceStatus === 'priced'
                ? 'Fixed shelf price shown to admins.'
                : 'Ignored while price is pending or quoted at shop.'
            }
          />
          <AppInput
            label="Stock level"
            value={form.stockLevel}
            onChangeText={(value) => setField('stockLevel', value)}
            keyboardType="numeric"
            className="flex-1"
          />
        </View>
        <ChoiceGroup
          label="Availability"
          value={form.availabilityStatus}
          options={AVAILABILITY_OPTIONS}
          onChange={(value) => setField('availabilityStatus', value)}
          helperText="Availability can be adjusted manually, but zero stock will still save as out of stock."
        />
        <AppInput
          label="Shop note"
          value={form.shopNote}
          onChangeText={(value) => setField('shopNote', value)}
          multiline
          inputClassName="min-h-24"
          helperText="Use for counter instructions, supplier notes, or in-shop pricing context."
        />
      </AppSection>

      {error ? (
        <View className="mt-4 rounded-[20px] border border-red-100 bg-red-50 px-4 py-3">
          <HeroText className="text-[13px] font-semibold text-red-700">
            {error}
          </HeroText>
        </View>
      ) : null}

      <View className="mt-6 gap-3">
        <AppButton
          label="Save string changes"
          onPress={() => void saveInventory()}
          isLoading={isSaving}
        />
        <AppButton
          label="Back to inventory"
          variant="outline"
          onPress={() => router.back()}
        />
      </View>
    </AppScreen>
  );
}
