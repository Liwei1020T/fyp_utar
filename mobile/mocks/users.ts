import type { AdminProfile, AppUser, PlayerProfile } from '../types/domain';

export const MOCK_PLAYERS: PlayerProfile[] = [
  {
    id: 'player-001',
    role: 'player',
    name: 'Aiman Faris',
    email: 'player@example.com',
    avatarLabel: 'AF',
    phone: '+60 12-410 8831',
    skillLevel: 'Intermediate',
    playingStyle: 'Attacking',
    playFrequency: 'Weekly',
    preferredTension: 26,
    priorities: {
      power: 9,
      control: 7,
      durability: 5,
      comfort: 6,
      sound: 8,
    },
    homeVenue: 'Bukit Jalil Badminton Arena',
    preferredAdminId: 'admin-001',
    recentGoal: 'More punch on back-court clears without losing net feel.',
  },
  {
    id: 'player-002',
    role: 'player',
    name: 'Nur Irdina',
    email: 'irdina@example.com',
    avatarLabel: 'NI',
    phone: '+60 17-662 9201',
    skillLevel: 'Advanced',
    playingStyle: 'Balanced',
    playFrequency: 'Tournament',
    preferredTension: 25,
    priorities: {
      power: 7,
      control: 8,
      durability: 8,
      comfort: 6,
      sound: 6,
    },
    homeVenue: 'Petaling Smash Hall',
    preferredAdminId: 'admin-001',
    recentGoal: 'Keep touch on slices while reducing frequent restrings.',
  },
  {
    id: 'player-003',
    role: 'player',
    name: 'Jason Kok',
    email: 'jason@example.com',
    avatarLabel: 'JK',
    phone: '+60 14-325 4087',
    skillLevel: 'Beginner',
    playingStyle: 'Control',
    playFrequency: 'Social',
    preferredTension: 23,
    priorities: {
      power: 4,
      control: 7,
      durability: 9,
      comfort: 8,
      sound: 4,
    },
    homeVenue: 'PJ Community Sports Hub',
    preferredAdminId: 'admin-001',
    recentGoal: 'More forgiving feel for longer weekend sessions.',
  },
];

export const MOCK_ADMINS: AdminProfile[] = [
  {
    id: 'admin-001',
    role: 'admin',
    name: 'Daniel Tan',
    email: 'admin@example.com',
    avatarLabel: 'DT',
    businessName: 'Apex String Lab',
    city: 'Kuala Lumpur',
    branchCode: 'ASL-KL-01',
    averageTurnaroundHours: 19,
    queueCapacity: 24,
    rating: 4.8,
    specialties: ['Tournament restrings', 'High-tension setups', 'Control tuning'],
    escalationEmail: 'ops@apexstringlab.my',
  },
];

export const MOCK_VENDORS = MOCK_ADMINS;

export const MOCK_USERS: AppUser[] = [...MOCK_PLAYERS, ...MOCK_ADMINS];
