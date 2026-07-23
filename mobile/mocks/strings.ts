import type { StringItem } from '../types/domain';
import {
  deriveAvailabilityStatus,
  derivePriceStatus,
  formatGaugeRange,
} from '../lib/inventory';

function createMockStringItem(input: {
  id: string;
  brand: string;
  model: string;
  localizedName?: string;
  category: StringItem['category'];
  mainTrait: string;
  gaugeMinMm: number;
  gaugeMaxMm: number;
  material: string;
  price: number | null;
  priceStatus?: StringItem['priceStatus'];
  tensionMinLbs: number;
  tensionMaxLbs: number;
  ratings: StringItem['ratings'];
  description: string;
  bestFor: string[];
  strengths: string[];
  tradeOffs: string[];
  reviewHighlight: string;
  inventoryTags: string[];
  stockLevel: number;
  availability?: StringItem['availability'];
  adminNote?: string;
  imageUrl?: string;
  isActive?: boolean;
}) {
  const availability = deriveAvailabilityStatus(
    input.stockLevel,
    input.availability,
  );
  const priceStatus = derivePriceStatus(input.price, input.priceStatus);
  const now = '2026-04-10T10:00:00.000Z';
  const gauge = formatGaugeRange(input.gaugeMinMm, input.gaugeMaxMm);
  const recommendedTension: [number, number] = [
    input.tensionMinLbs,
    input.tensionMaxLbs,
  ];
  const isActive = input.isActive ?? true;
  const catalog = {
    id: input.id,
    brand: input.brand,
    modelName: input.model,
    localizedName: input.localizedName,
    isHybrid: false,
    gaugeMinMm: input.gaugeMinMm,
    gaugeMaxMm: input.gaugeMaxMm,
    material: input.material,
    description: input.description,
    mainTrait: input.mainTrait,
    category: input.category,
    tensionMinLbs: input.tensionMinLbs,
    tensionMaxLbs: input.tensionMaxLbs,
    performanceScores: input.ratings,
    imageUrl: input.imageUrl,
    isActive,
    createdAt: now,
    updatedAt: now,
  };
  const inventory = {
    id: `inventory-${input.id}`,
    vendorId: 'admin-001',
    stringId: input.id,
    stockQty: input.stockLevel,
    price: input.price,
    priceStatus,
    availabilityStatus: availability,
    shopNote: input.adminNote,
    updatedAt: now,
  };

  return {
    id: input.id,
    brand: input.brand,
    model: input.model,
    localizedName: input.localizedName,
    category: input.category,
    mainTrait: input.mainTrait,
    gauge,
    gaugeMinMm: input.gaugeMinMm,
    gaugeMaxMm: input.gaugeMaxMm,
    material: input.material,
    price: input.price ?? 0,
    priceStatus,
    recommendedTension,
    tensionMinLbs: input.tensionMinLbs,
    tensionMaxLbs: input.tensionMaxLbs,
    ratings: input.ratings,
    tensionNote: `Recommended at ${input.tensionMinLbs}-${input.tensionMaxLbs} lbs for the current shop setup.`,
    description: input.description,
    imageUrl: input.imageUrl,
    isActive,
    createdAt: now,
    updatedAt: now,
    inventoryUpdatedAt: now,
    bestFor: input.bestFor,
    strengths: input.strengths,
    tradeOffs: input.tradeOffs,
    reviewHighlight: input.reviewHighlight,
    inventoryTags: input.inventoryTags,
    stockLevel: input.stockLevel,
    availability,
    adminNote: input.adminNote,
    catalog,
    inventory,
  } satisfies StringItem;
}

export const MOCK_STRINGS: StringItem[] = [
  createMockStringItem({
    id: 'string-001',
    brand: 'Yonex',
    model: 'BG66 Ultimax',
    localizedName: '尤尼克斯 BG66 超极限',
    category: 'repulsion',
    mainTrait: 'Repulsion',
    gaugeMinMm: 0.65,
    gaugeMaxMm: 0.65,
    material: 'High-intensity nylon multifilament',
    price: 36,
    tensionMinLbs: 24,
    tensionMaxLbs: 29,
    ratings: { power: 9, control: 7, durability: 5, comfort: 6, sound: 10 },
    description:
      'A lively attacking string with sharp shuttle release and a crisp sound that feels premium on contact.',
    bestFor: ['Attacking doubles players', 'Fast repulsion seekers', 'Players who enjoy audible feedback'],
    strengths: ['Immediate rebound', 'Sharp hitting sound', 'Easy to feel sweet spot timing'],
    tradeOffs: ['Needs more frequent restringing', 'Less forgiving if you mishit often'],
    reviewHighlight: 'Players love how quickly the shuttle jumps off the bed during steep follow-up attacks.',
    inventoryTags: ['Fast seller', 'Counter display', 'Repulsion'],
    stockLevel: 18,
    adminNote: 'Displayed near the counter because it pairs well with attacking profiles.',
    imageUrl: 'https://placehold.co/240x240/F6F8FB/2F64B6.png?text=BG66',
  }),
  createMockStringItem({
    id: 'string-002',
    brand: 'Victor',
    model: 'VBS-68 Power',
    localizedName: '胜利 VBS-68 力量',
    category: 'balanced',
    mainTrait: 'Power',
    gaugeMinMm: 0.68,
    gaugeMaxMm: 0.68,
    material: 'Nano nylon fiber braid',
    price: 32,
    tensionMinLbs: 23,
    tensionMaxLbs: 28,
    ratings: { power: 8, control: 7, durability: 8, comfort: 7, sound: 7 },
    description:
      'A dependable all-round string that blends solid punch with better longevity for frequent weekly play.',
    bestFor: ['Club players', 'Balanced setups', 'Anyone moving up from entry strings'],
    strengths: ['Steady tension retention', 'Reliable durability', 'Comfortable impact feel'],
    tradeOffs: ['Less explosive than ultra-thin strings', 'Sound profile is more muted'],
    reviewHighlight: 'Easy recommendation when players want one string that does many things well.',
    inventoryTags: ['Balanced', 'Good durability'],
    stockLevel: 2,
    adminNote: 'Counter team is holding the last two packs for weekend bookings.',
    imageUrl: 'https://placehold.co/240x240/F8F4E9/9A6B17.png?text=VBS68',
  }),
  createMockStringItem({
    id: 'string-003',
    brand: 'Li-Ning',
    model: 'No.1',
    localizedName: '李宁 1号线',
    category: 'balanced',
    mainTrait: 'Control',
    gaugeMinMm: 0.65,
    gaugeMaxMm: 0.65,
    material: 'Heat-resistant braided multifilament',
    price: null,
    priceStatus: 'pending',
    tensionMinLbs: 24,
    tensionMaxLbs: 30,
    ratings: { power: 9, control: 8, durability: 7, comfort: 6, sound: 8 },
    description:
      'A premium tournament-oriented string with quick rebound, sharp control, and a lively high-tension response.',
    bestFor: ['Competitive players', 'Control-minded attackers', 'High-tension builds'],
    strengths: ['High-tension stability', 'Crisp directional feedback', 'Strong all-court pace'],
    tradeOffs: ['Feels firmer for casual players', 'Price sits above the category average'],
    reviewHighlight: 'Often chosen by regular tournament players who want power without losing command on slices.',
    inventoryTags: ['Tournament', 'Price review'],
    stockLevel: 9,
    adminNote: 'Waiting for the new supplier quote before this goes live in-shop.',
    imageUrl: 'https://placehold.co/240x240/EEF8F4/2F7A58.png?text=NO1',
  }),
  createMockStringItem({
    id: 'string-004',
    brand: 'Yonex',
    model: 'Exbolt 63',
    localizedName: '尤尼克斯 Exbolt 63',
    category: 'repulsion',
    mainTrait: 'Repulsion',
    gaugeMinMm: 0.63,
    gaugeMaxMm: 0.63,
    material: 'Forged fiber core with elastic outer coating',
    price: 44,
    tensionMinLbs: 24,
    tensionMaxLbs: 29,
    ratings: { power: 10, control: 7, durability: 4, comfort: 5, sound: 9 },
    description:
      'An ultra-thin premium option built for instant repulsion and a very crisp, modern high-speed response.',
    bestFor: ['Fast front-court players', 'Players who love sharp repulsion', 'Aggressive doubles setups'],
    strengths: ['Fastest rebound in the catalog', 'Excellent drive exchanges', 'Premium feel'],
    tradeOffs: ['Lowest durability among premium picks', 'Less forgiving on mishits'],
    reviewHighlight: 'Feels electric in quick exchanges and rewards players who hit cleanly and early.',
    inventoryTags: ['Elite', 'Ultra thin'],
    stockLevel: 5,
    adminNote: 'Low stock because it is currently the most booked premium string.',
    imageUrl: 'https://placehold.co/240x240/F1F5F9/475569.png?text=EX63',
  }),
  createMockStringItem({
    id: 'string-005',
    brand: 'Gosen',
    model: 'G-Tone 5',
    localizedName: '高神 G-Tone 5',
    category: 'control',
    mainTrait: 'Control',
    gaugeMinMm: 0.65,
    gaugeMaxMm: 0.65,
    material: 'High polymer nylon with textured surface',
    price: 35,
    priceStatus: 'quoted_at_shop',
    tensionMinLbs: 23,
    tensionMaxLbs: 29,
    ratings: { power: 7, control: 9, durability: 6, comfort: 7, sound: 9 },
    description:
      'A textured control string popular with players who want cleaner shuttle hold and a sharp sound.',
    bestFor: ['Net-play specialists', 'Control-heavy doubles players', 'Touch-focused setups'],
    strengths: ['Excellent net feel', 'Controlled slice response', 'Strong acoustic feedback'],
    tradeOffs: ['Less raw punch than power-first options', 'Durability is only mid-pack'],
    reviewHighlight: 'A favorite when players ask for better placement and cleaner front-court confidence.',
    inventoryTags: ['Control', 'Coach pick'],
    stockLevel: 11,
    adminNote: 'Coach packages use custom pricing, so the desk quotes this at collection.',
    imageUrl: 'https://placehold.co/240x240/FFF1F1/B42318.png?text=GT5',
  }),
  createMockStringItem({
    id: 'string-006',
    brand: 'Ashaway',
    model: 'ZyMax 66 Fire Power',
    localizedName: '阿沙威 ZyMax 66 火力',
    category: 'durable',
    mainTrait: 'Durable',
    gaugeMinMm: 0.66,
    gaugeMaxMm: 0.66,
    material: 'BETA polymer multifilament',
    price: 33,
    tensionMinLbs: 22,
    tensionMaxLbs: 29,
    ratings: { power: 8, control: 7, durability: 8, comfort: 8, sound: 7 },
    description:
      'A stable and comfortable option with solid tension retention for players who want fewer restrings.',
    bestFor: ['Frequent weekly players', 'Comfort-first builds', 'Durability-minded setups'],
    strengths: ['Strong durability', 'Comfortable feel', 'Good long-term consistency'],
    tradeOffs: ['Less lively sound', 'Does not feel as premium as the fastest strings'],
    reviewHighlight: 'Recommended often when players complain their last setup lost feel too quickly.',
    inventoryTags: ['Comfort', 'Durable'],
    stockLevel: 0,
    availability: 'out_of_stock',
    adminNote: 'Supplier delay until next Tuesday. Hide from walk-in recommendations for now.',
    imageUrl: 'https://placehold.co/240x240/F6F8FB/2F64B6.png?text=ZM66',
  }),
];
