import type {
  InventoryAvailability,
  InventoryPriceStatus,
  StringItem,
  StringPerformanceScores,
} from '../types/domain';

export type InventoryAttentionState =
  | 'ready'
  | 'low_stock'
  | 'out_of_stock'
  | 'price_missing'
  | 'inactive';

export function formatGaugeRange(
  min: number | null | undefined,
  max: number | null | undefined,
  fallback = 'Gauge pending',
) {
  if (min == null && max == null) {
    return fallback;
  }
  if (min != null && max != null) {
    if (Math.abs(min - max) < 0.001) {
      return `${min.toFixed(2)} mm`;
    }
    return `${min.toFixed(2)}-${max.toFixed(2)} mm`;
  }
  const value = min ?? max;
  return value == null ? fallback : `${value.toFixed(2)} mm`;
}

export function formatTensionRange(
  min: number | null | undefined,
  max: number | null | undefined,
  fallback = 'Tension pending',
) {
  if (min == null && max == null) {
    return fallback;
  }
  if (min != null && max != null) {
    return `${min}-${max} lbs`;
  }
  return `${min ?? max} lbs`;
}

export function clampScore(value: number) {
  return Math.max(1, Math.min(10, Math.round(value)));
}

export function sanitizePerformanceScores(
  scores: Partial<StringPerformanceScores>,
  fallback: StringPerformanceScores,
): StringPerformanceScores {
  return {
    power: clampScore(scores.power ?? fallback.power),
    control: clampScore(scores.control ?? fallback.control),
    durability: clampScore(scores.durability ?? fallback.durability),
    comfort: clampScore(scores.comfort ?? fallback.comfort),
    sound: clampScore(scores.sound ?? fallback.sound),
  };
}

export function derivePriceStatus(
  price: number | null | undefined,
  explicit?: InventoryPriceStatus | null,
) {
  if (explicit) {
    return explicit;
  }
  return price == null ? 'pending' : 'priced';
}

export function deriveAvailabilityStatus(
  stockQty: number,
  explicit?: InventoryAvailability | null,
) {
  if (explicit) {
    return explicit;
  }
  if (stockQty <= 0) {
    return 'out_of_stock';
  }
  if (stockQty <= 5) {
    return 'low_stock';
  }
  return 'in_stock';
}

export function getInventoryPriceLabel(item: StringItem) {
  const price = item.inventory.price;
  const status = derivePriceStatus(price, item.inventory.priceStatus);

  if (status === 'quoted_at_shop') {
    return {
      label: 'Quoted at shop',
      state: status,
      hasPrice: false,
    };
  }

  if (status === 'pending' || price == null) {
    return {
      label: 'Price pending',
      state: 'pending' as const,
      hasPrice: false,
    };
  }

  return {
    label: `RM ${price.toFixed(2)}`,
    state: 'priced' as const,
    hasPrice: true,
  };
}

export function getInventoryAttentionState(item: StringItem): InventoryAttentionState {
  if (!item.catalog.isActive) {
    return 'inactive';
  }
  if (item.inventory.availabilityStatus === 'out_of_stock') {
    return 'out_of_stock';
  }
  if (item.inventory.priceStatus === 'pending' || item.inventory.price == null) {
    return 'price_missing';
  }
  if (item.inventory.availabilityStatus === 'low_stock' || item.inventory.stockQty <= 5) {
    return 'low_stock';
  }
  return 'ready';
}

export function getInventoryAttentionLabel(item: StringItem) {
  switch (getInventoryAttentionState(item)) {
    case 'out_of_stock':
      return 'Restock before next booking';
    case 'price_missing':
      return 'Add shop price';
    case 'low_stock':
      return 'Low stock watch';
    case 'inactive':
      return 'Hidden from catalog';
    case 'ready':
    default:
      return 'Ready';
  }
}

export function inventoryAttentionScore(item: StringItem) {
  switch (getInventoryAttentionState(item)) {
    case 'out_of_stock':
      return 100;
    case 'price_missing':
      return 90;
    case 'low_stock':
      return 70;
    case 'inactive':
      return 40;
    case 'ready':
    default:
      return 0;
  }
}

export function buildStringDisplayName(item: Pick<StringItem, 'brand' | 'model'>) {
  return `${item.brand} ${item.model}`.trim();
}

export function buildStringSearchBlob(item: StringItem) {
  return [
    item.brand,
    item.model,
    item.localizedName,
    item.catalog.material,
    item.catalog.mainTrait,
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase();
}

export function getInventorySummary(items: StringItem[]) {
  const lowStock = items.filter(
    (item) => getInventoryAttentionState(item) === 'low_stock',
  ).length;
  const pricePending = items.filter(
    (item) => getInventoryAttentionState(item) === 'price_missing',
  ).length;

  return {
    itemCount: items.length,
    lowStockCount: lowStock,
    pricePendingCount: pricePending,
  };
}
