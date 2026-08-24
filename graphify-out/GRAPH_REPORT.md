# Graph Report - StringSence  (2026-08-24)

## Corpus Check
- 443 files · ~2,129,677 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2850 nodes · 5765 edges · 287 communities (219 shown, 68 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 544 edges (avg confidence: 0.67)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8eba1869`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11
- Community 12
- Community 13
- Community 14
- Community 15
- Community 16
- Community 17
- Community 18
- Community 19
- Community 20
- Community 21
- Community 22
- Community 23
- Community 24
- Community 25
- Community 26
- Community 27
- Community 28
- Community 29
- Community 30
- Community 31
- Community 32
- Community 33
- Community 34
- Community 35
- Community 36
- Community 37
- Community 38
- Community 39
- Community 40
- Community 41
- Community 42
- Community 43
- Community 44
- Community 45
- Community 46
- Community 47
- Community 48
- Community 49
- Community 50
- Community 51
- Community 52
- Community 53
- Community 54
- Community 55
- Community 56
- Community 57
- Community 58
- Community 59
- Community 60
- Community 61
- Community 62
- Community 63
- Community 64
- Community 65
- Community 66
- Community 67
- Community 68
- Community 69
- Community 70
- Community 71
- Community 72
- Community 73
- Community 74
- Community 75
- Community 76
- Community 77
- Community 78
- Community 79
- Community 80
- Community 81
- Community 82
- Community 83
- Community 84
- Community 85
- Community 86
- Community 87
- Community 88
- Community 89
- Community 90
- Community 91
- Community 92
- Community 93
- Community 94
- Community 95
- Community 96
- Community 97
- Community 98
- Community 99
- Community 100
- Community 101
- Community 102
- Community 103
- Community 104
- Community 105
- Community 106
- Community 107
- Community 123
- Community 124
- Appendix D: Recommendation Algorithm
- Community 127
- Community 128
- Community 129
- Community 130
- Community 131
- Community 132
- Community 133
- Community 134
- Community 136
- Community 138
- Community 139
- Community 140
- Community 141
- Community 142
- Community 143
- Community 144
- Community 145
- Community 146
- Community 147
- Community 148
- Community 149
- Community 150
- Community 151
- Community 157
- Community 187
- Community 188
- Community 189
- Community 191
- 11. Feature Module Breakdown
- 5. Routing and Access Control
- StringSense: AI-Driven Mobile Platform
- NLP Workbench Latest — Canonical Experiment Root
- 7. Data Layer Model
- Appendix B: Backend API Endpoint Summary
- Appendix C: Database Schema Summary
- Appendix F: Testing Evidence
- Appendix G: NLP and Recommendation Artifacts
- _verify_internal_api_key
- BookingUpdates.tsx
- 2. Technology Stack
- 6. State Architecture
- RagAdapter
- 8. Domain Model
- 9. UI System
- BusinessHours
- 10. Navigation UX Structure
- eslint.config.js
- 00_appendix_index.md
- axios
- test_runtime_boundaries.py
- expo-blur
- expo-constants
- expo-linking
- expo-splash-screen
- bootstrap.sh
- react-native
- react-native-gesture-handler
- admin-bookings-snapshot.md
- admin-dashboard-snapshot.md
- auth-login-snapshot.md
- auth-welcome-snapshot.md
- player-home-snapshot.md
- react-native
- API Contract
- Test Plan
- Feedback Form Design
- RequestPasswordResetUseCase
- Versioning and Audit Evidence
- Database Design
- Player Experience
- Decision Summary
- Target Architecture
- ExplainResponse
- RagQueryRequest
- RagQueryResponse
- BaseSettings
- ExplainResponse
- RagQueryResponse
- RagQueryRequest
- RagQueryResponse
- ExplainRequest
- ExplainResponse
- BaseSettings
- Path
- BookingPhotoType
- date
- UploadFile
- Protocol
- StringItem
- BudgetRange
- auth_routes.py
- page_to_dict
- Agent Scope Simplification Progress
- chatbot.tsx
- normalizeUploadFile
- ListInventoryStringsUseCase
- ListStringsUseCase
- error_payload
- build-backend-image.sh
- expo-blur
- expo-camera
- expo-device
- expo-linking
- expo-notifications
- expo-splash-screen
- gsap
- react-native
- react-native-gesture-handler
- react-native-qrcode-svg
- uxAccessibility.test.mjs
- StringItem
- Session

## God Nodes (most connected - your core abstractions)
1. `useAppStore` - 65 edges
2. `useCurrentUser()` - 62 edges
3. `HeroText` - 55 edges
4. `AppCard()` - 51 edges
5. `NotFoundError` - 45 edges
6. `AppChip()` - 43 edges
7. `Page` - 43 edges
8. `get_settings()` - 34 edges
9. `AppScreen()` - 34 edges
10. `BookingRecord` - 33 edges

## Surprising Connections (you probably didn't know these)
- `test_all_approved_strings_have_a_seeded_feel_category()` --calls--> `get_settings()`  [INFERRED]
  backend/tests/test_system_string_cohort.py → backend/app/config/settings.py
- `test_backend_and_nlp_read_the_same_versioned_cohort()` --calls--> `get_settings()`  [INFERRED]
  backend/tests/test_system_string_cohort.py → backend/app/config/settings.py
- `to_string_item()` --calls--> `StringTag`  [INFERRED]
  backend/app/adapters/persistence/sqlalchemy/repositories/mappers.py → backend/app/domain/catalog/entities.py
- `to_business_hours()` --calls--> `BusinessHoursDay`  [INFERRED]
  backend/app/adapters/persistence/sqlalchemy/repositories/mappers.py → backend/app/domain/store/entities.py
- `upsert_profile()` --calls--> `PlayerProfile`  [INFERRED]
  backend/app/entrypoints/api/routes/profile_routes.py → backend/app/domain/profile/entities.py

## Import Cycles
- None detected.

## Communities (287 total, 68 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.09
Nodes (47): PaymentDecision, NOTIFICATION_CATEGORIES, AdminChatQueueScreen(), PRIMARY_ACTIONS, PlayerChatDetailScreen(), PlayerChatThreadsScreen(), formatScore(), ScoreMeter() (+39 more)

### Community 1 - "Community 1"
Cohesion: 0.12
Nodes (34): AdminChatDetailScreen(), AdminCheckInScreen(), CHECKLIST_ITEMS, ChecklistKey, formatDropOffDateTime(), getDropOffConfirmationStatus(), getLookupTokens(), getTodayLocalDate() (+26 more)

### Community 2 - "Community 2"
Cohesion: 0.12
Nodes (36): AdminAnalyticsScreen(), AdminDashboardScreen(), AuthLayout(), IndexScreen(), DEFERRED_PLAYER_SEGMENTS, PlayerLayout(), NotificationsScreen(), NotificationPreferencesScreen() (+28 more)

### Community 3 - "Community 3"
Cohesion: 0.08
Nodes (31): AdminTabIcon(), PaymentResultScreen(), CompareStringsScreen(), StandardTabIcon(), BrandGroup, CatalogListItem, DisplayMode, isBrandGroup() (+23 more)

### Community 4 - "Community 4"
Cohesion: 0.05
Nodes (65): BackendBookingPhotoType, BackendUploadFile, BackendAdminCommunitySummary, BackendAdminDeviceToken, BackendAdminFeedback, BackendAdminInventoryString, BackendAdminNotification, BackendAgentQuery (+57 more)

### Community 5 - "Community 5"
Cohesion: 0.27
Nodes (5): AppError, ForbiddenError, Any, UnauthorizedError, Exception

### Community 6 - "Community 6"
Cohesion: 0.06
Nodes (79): get_settings(), Settings, booking_update_to_dto(), get_media_file(), build_signed_media_url(), delete_booking_update_photo(), delete_string_catalog_image(), _detect_image_extension() (+71 more)

### Community 7 - "Community 7"
Cohesion: 0.11
Nodes (25): AdminRecommendationRunsScreen(), getStringLabel(), AdminRecommendationRunDetailScreen(), buildRationaleSummary(), buildSnapshotItems(), formatScalarValue(), getStringLabel(), ChatBubble() (+17 more)

### Community 8 - "Community 8"
Cohesion: 0.10
Nodes (28): InventorySnapshot, RecommendationCandidateModel, Fyp1ContentRecommendationScorer, FYP1 scorer: rule-enhanced, confidence-aware, content-based, explainable., _attacking_request(), _candidate(), _candidate_with_core_scores(), FakeProfileRepository (+20 more)

### Community 9 - "Community 9"
Cohesion: 0.08
Nodes (32): AdminInventoryScreen(), InventorySort, InventoryStatusFilter, matchesStatusFilter(), SearchField(), SORT_OPTIONS, sortInventory(), STATUS_FILTERS (+24 more)

### Community 10 - "Community 10"
Cohesion: 0.14
Nodes (20): AuthResponse, ForgotPasswordRequest, ForgotPasswordRequestResponse, ForgotPasswordResetRequest, LoginRequest, MessageResponse, BaseModel, RegisterRequest (+12 more)

### Community 11 - "Community 11"
Cohesion: 0.16
Nodes (31): RecommendationFeatureSignalModel, _auxiliary_scores(), _budget_fit_score(), _build_feature_evidence(), _build_reasons(), _candidate_feature_source_version(), _candidate_matrix_version(), clamp01() (+23 more)

### Community 12 - "Community 12"
Cohesion: 0.18
Nodes (9): validate_status_transition(), validate_terminal_status_note(), CheckInLookup, booking_check_in_reference(), ConflictError, ConfirmCheckInUseCase, LookupCheckInUseCase, test_booking_status_transition_accepts_valid_progression() (+1 more)

### Community 13 - "Community 13"
Cohesion: 0.07
Nodes (38): deriveCategory(), deriveGaugeBounds(), deriveMainTrait(), deriveMaterial(), deriveRecommendedTension(), deriveScores(), deriveStrengthLabels(), initials() (+30 more)

### Community 14 - "Community 14"
Cohesion: 0.18
Nodes (7): StringCatalogItem, StringOfficialPerformance, OfficialPerformanceRecord, Session, StringItem, SqlAlchemyCatalogRepository, test_sqlalchemy_booking_repository_creates_history_entries()

### Community 15 - "Community 15"
Cohesion: 0.11
Nodes (38): RecommendationFeatureDefinition, StringRecommendationMatrix, _build_catalog_lookup(), _build_evidence_note(), _build_matrix_entries(), CatalogLookupEntry, _cell_text(), _clean_text() (+30 more)

### Community 16 - "Community 16"
Cohesion: 0.06
Nodes (27): InventoryMovementRecord, RecommendationMatrixEntryRecord, RecommendationMatrixInspectionRecord, StringItem, StringOfficialPerformance, StringTag, AdminInventoryStringOut, CatalogTagOut (+19 more)

### Community 17 - "Community 17"
Cohesion: 0.21
Nodes (12): RecommendationScoreCache, UserPreferenceMatrix, _float_or_none(), _optional_string(), Session, _required_float(), _required_int(), _required_mapping() (+4 more)

### Community 18 - "Community 18"
Cohesion: 0.17
Nodes (21): ProfileRecommendationPayload, Any, BaseModel, datetime, recommendation_detail_to_dto(), recommendation_log_to_dict(), recommendation_request_to_domain(), recommendation_response_to_dto() (+13 more)

### Community 21 - "Community 21"
Cohesion: 0.17
Nodes (5): Page, ListAdminBookingsUseCase, ListMyBookingsUseCase, ListInventoryMovementsUseCase, ListRecommendationRunsUseCase

### Community 22 - "Community 22"
Cohesion: 0.09
Nodes (32): AdminInventoryDetailScreen(), AVAILABILITY_OPTIONS, buildCatalogPayload(), buildInventoryPayload(), buildLocalPatch(), buildOfficialPerformancePayload(), CATALOG_VISIBILITY_OPTIONS, CATEGORY_OPTIONS (+24 more)

### Community 23 - "Community 23"
Cohesion: 0.19
Nodes (24): AspectScoreMap, approved_catalog_defaults(), approved_row_to_values(), as_string(), build_sku(), catalog_source_path(), clamp01(), derive_aspect_scores() (+16 more)

### Community 24 - "Community 24"
Cohesion: 0.40
Nodes (4): settings_to_dto(), StoreSettingsOut, public_get_store_settings(), GetStoreSettingsUseCase

### Community 25 - "Community 25"
Cohesion: 0.07
Nodes (48): AgentActionDto, AgentQueryDto, AgentResponseDto, _action_is_verified(), AgentModelClient, _collect_named_ids(), _completion_message(), _empty_verified_ids() (+40 more)

### Community 26 - "Community 26"
Cohesion: 0.11
Nodes (13): Booking, BookingStatusHistory, BookingUpdate, to_booking_record(), Session, SqlAlchemyBookingRepository, BookingRecord, BookingStatusHistoryEntry (+5 more)

### Community 27 - "Community 27"
Cohesion: 0.07
Nodes (58): AdminInventoryStringOut, _active_check_in_token(), admin_add_booking_update(), admin_bookings(), admin_check_in_booking(), admin_confirm_secure_check_in(), admin_delete_payment_qr(), admin_delete_string_image() (+50 more)

### Community 28 - "Community 28"
Cohesion: 0.09
Nodes (22): backgroundColor, foregroundImage, adaptiveIcon, edgeToEdgeEnabled, predictiveBackGestureEnabled, expo, android, icon (+14 more)

### Community 30 - "Community 30"
Cohesion: 0.15
Nodes (8): to_user_account(), Session, SqlAlchemyUserRepository, UserAccount, Protocol, UserRepository, GetCurrentUserUseCase, LoginUseCase

### Community 31 - "Community 31"
Cohesion: 0.24
Nodes (16): booking_to_dto(), BookingOut, CurrentUser, get_current_admin(), get_current_customer(), BaseModel, require_roles(), add_booking_update() (+8 more)

### Community 32 - "Community 32"
Cohesion: 0.06
Nodes (46): AdminBusinessHoursScreen(), SlotPickerProps, ConversationCardProps, RacketPassportCard(), RacketPassportCardProps, mapBackendBusinessHoursToBusinessHours(), mapBusinessHoursToBackendPayload(), AppStoreState (+38 more)

### Community 33 - "Community 33"
Cohesion: 0.14
Nodes (42): _booking_completed_at(), _completed_at(), _confirmed_fields(), create_feedback(), create_racket(), delete_racket(), _durability_available_at(), feedback_to_dto() (+34 more)

### Community 34 - "Community 34"
Cohesion: 0.32
Nodes (8): Base, Brand, InventoryMovement, StringCatalogMetric, StringCatalogTag, StringInventoryItem, User, DeclarativeBase

### Community 35 - "Community 35"
Cohesion: 0.07
Nodes (26): ABSA Evaluation, Backend Compatibility Inputs, Backend Integration Design, Baselines, BERT ABSA Review Optimization Design, Current Context, Data And Annotation Design, Difficult-Case Pool (+18 more)

### Community 36 - "Community 36"
Cohesion: 0.20
Nodes (12): RecommendationDetailModel, RecommendationRequestModel, RecommendationResponseModel, RecommendationResultModel, _feature_source_version_from_results(), _float_or_none(), GenerateRecommendationUseCase, _isoformat_or_none() (+4 more)

### Community 37 - "Community 37"
Cohesion: 0.16
Nodes (10): AnalyticsSummary, AnalyticsWorkloadEntry, BookingSlot, BusinessHoursDay, PopularString, ServiceQueue, ServiceQueueItem, ServiceQueueLane (+2 more)

### Community 38 - "Community 38"
Cohesion: 0.15
Nodes (19): analytics_summary_to_dto(), AnalyticsSummaryOut, AnalyticsWorkloadEntryOut, BookingSlotOut, business_hours_to_dto(), BusinessHoursDayPayload, CheckInLookupOut, CheckInPayload (+11 more)

### Community 39 - "Community 39"
Cohesion: 0.09
Nodes (23): clsx, expo-constants, expo-font, expo-secure-store, expo-status-bar, dependencies, clsx, expo-constants (+15 more)

### Community 41 - "Community 41"
Cohesion: 0.08
Nodes (23): 1. Purpose, 2. Admin Inventory List Proposal, 3. Admin String Detail Proposal, 4. Unified Inventory Card Design, 5. Backend Field Mapping, 6. Admin Microcopy, 7. ASCII Wireframes, 8. Implementation Checklist (+15 more)

### Community 42 - "Community 42"
Cohesion: 0.17
Nodes (6): StoreSettings, to_store_settings(), StoreSettingsRecord, Protocol, StoreRepository, UpdateStoreSettingsUseCase

### Community 43 - "Community 43"
Cohesion: 0.10
Nodes (21): 10. Design Summary, 1. Scope, 2. End-to-End Runtime Flow, 3.1 User-side inputs, 3.2 Item-side inputs, 3.3 Feature mapping note, 3. Data Inputs and Signal Layers, 4.1 Core feature space (+13 more)

### Community 44 - "Community 44"
Cohesion: 0.11
Nodes (18): description, icons, 128, 16, manifest_version, minimum_chrome_version, name, platforms (+10 more)

### Community 45 - "Community 45"
Cohesion: 0.09
Nodes (15): NotFoundError, CreateBookingUseCase, datetime, GetBookingUseCase, datetime, UpdateBookingStatusUseCase, DeactivateStringUseCase, StringItem (+7 more)

### Community 46 - "Community 46"
Cohesion: 0.18
Nodes (17): buildMatchReasons(), buildRecommendationSummary(), clampPercent(), compactSentence(), formatCurrency(), formatScore(), getBudgetCopy(), getReviewStrengths() (+9 more)

### Community 47 - "Community 47"
Cohesion: 0.21
Nodes (13): normalize_datetime(), parse_hhmm(), BookingSlot, date, datetime, slot_busy_label(), slot_label(), slots_for_date() (+5 more)

### Community 48 - "Community 48"
Cohesion: 0.21
Nodes (4): CatalogRepository, Protocol, StringItem, StringOfficialPerformance

### Community 49 - "Community 49"
Cohesion: 0.27
Nodes (6): PasswordResetCode, to_password_reset_code(), datetime, Session, SqlAlchemyPasswordResetRepository, PasswordResetCodeRecord

### Community 50 - "Community 50"
Cohesion: 0.12
Nodes (16): Active Business Tables, `booking_status_history`, `booking_updates`, `bookings`, Catalog Normalization, `inventory_items`, `profiles`, `recommendation_logs` (+8 more)

### Community 51 - "Community 51"
Cohesion: 0.14
Nodes (9): Database Ownership and Schema Strategy, Source of Truth, Backend Docs Index, 1. Prepare Environment, 2. Start the Unified Backend, 3. Validation Commands, 4. Catalog and Recommendation Notes, 5. Commerce Boundary (+1 more)

### Community 52 - "Community 52"
Cohesion: 0.06
Nodes (34): Active Scope, Agent Scope Simplification Plan, Decisions, Deferred Scope, Errors Encountered, Goal, Phase 10 — Authentication and player page-by-page acceptance, Phase 11 — Admin page-by-page acceptance (+26 more)

### Community 53 - "Community 53"
Cohesion: 0.24
Nodes (6): ProfileRepository, PlayerProfile, Protocol, _is_complete(), PlayerProfile, UpsertMyProfileUseCase

### Community 54 - "Community 54"
Cohesion: 0.16
Nodes (12): datetime, SystemClock, get_booking_repository(), get_catalog_repository(), get_clock(), get_password_reset_repository(), get_profile_repository(), get_recommendation_log_repository() (+4 more)

### Community 55 - "Community 55"
Cohesion: 0.06
Nodes (39): RequestCodeForm, requestCodeSchema, ResetPasswordForm, resetPasswordSchema, demoUsers, LoginForm, loginSchema, LoginScreen() (+31 more)

### Community 56 - "Community 56"
Cohesion: 0.12
Nodes (15): 10. Cold-Start And Fallback, 11. Explanation And Admin Audit, 12. Evaluation, 13. Implementation Boundaries, 14. Design Summary, 1. Goal, 2. Current Baseline, 3. Formal Positioning (+7 more)

### Community 57 - "Community 57"
Cohesion: 0.22
Nodes (20): AdminDeviceTokenOut, AdminNotificationOut, DeviceTokenOut, MarkNotificationsReadOut, MarkNotificationsReadPayload, notification_preferences_to_dto(), NotificationOut, NotificationPreferencesPayload (+12 more)

### Community 58 - "Community 58"
Cohesion: 0.21
Nodes (12): advancedPreferencesForPayload(), buildBackendProfilePayload(), deriveAdvancedPreferences(), derivedElasticityPreference(), derivedStringMovementPreference(), derivedTensionRetentionPreference(), mapFrontendPlayingStyle(), mapFrontendSkillLevel() (+4 more)

### Community 59 - "Community 59"
Cohesion: 0.17
Nodes (7): BadRequestError, AddBookingUpdateUseCase, ImportRecommendationMatrixUseCase, StringItem, UpdateInventoryStringUseCase, StringOfficialPerformance, UpdateOfficialPerformanceUseCase

### Community 60 - "Community 60"
Cohesion: 0.12
Nodes (16): Acceptance Criteria, Admin Experience, Cache Policy, Community Feedback Calibration Development Design, Current Capability Status, Decisions Applied to V11, Deferred or Partial Work, Document Status (+8 more)

### Community 61 - "Community 61"
Cohesion: 0.31
Nodes (8): BookingStatus, StrEnum, booking_history_to_dto(), BookingStatusHistoryOut, BookingUpdateOut, CreateBookingPayload, BaseModel, UpdateBookingStatusPayload

### Community 62 - "Community 62"
Cohesion: 0.26
Nodes (11): buildTrackingSteps(), formatTrackingDateTime(), getStageBadge(), NODE_STYLES, TimelineStep, TimelineStepDefinition, TimelineVisualState, TRACKING_SEQUENCE (+3 more)

### Community 63 - "Community 63"
Cohesion: 0.24
Nodes (8): AdminAgentToolbox, _masked_phone(), _optional_choice(), _optional_text(), AgentToolResult, inventory_availability(), InventoryAvailability, StringItem

### Community 64 - "Community 64"
Cohesion: 0.29
Nodes (6): engines, node, main, name, private, version

### Community 65 - "Community 65"
Cohesion: 0.25
Nodes (6): Profile, PlayerProfile, to_profile(), PlayerProfile, Session, SqlAlchemyProfileRepository

### Community 66 - "Community 66"
Cohesion: 0.20
Nodes (5): Clock, datetime, Protocol, RequestPasswordResetUseCase, ResetPasswordUseCase

### Community 67 - "Community 67"
Cohesion: 0.18
Nodes (13): AdminAgentScreen(), ConversationEntry, starterQuestions, writeActions, historyToTimeline(), mapBackendBookingToBooking(), mapBackendBookingUpdateToBookingUpdate(), mapBackendConversationToConversation() (+5 more)

### Community 68 - "Community 68"
Cohesion: 0.22
Nodes (11): AdminBookingDetailScreen(), AdminUpdateFeed(), getAllowedNextStatuses(), getPriceStateLabel(), getStatusHeroCopy(), getUpdateMetaLabel(), getWorkflowActionLabel(), getWorkflowOptionHint() (+3 more)

### Community 69 - "Community 69"
Cohesion: 0.12
Nodes (21): RecommendationRunItem, _booking_string_name(), _collapsed_aspect_scores(), _normalize_availability_status(), _normalize_pricing_mode(), _normalized_name(), OfficialPerformanceRecord, StringItem (+13 more)

### Community 72 - "Community 72"
Cohesion: 0.17
Nodes (7): StoreBusinessHours, to_business_hours(), Session, SqlAlchemyStoreRepository, StoreBusinessHoursRecord, GetBusinessHoursUseCase, UpdateBusinessHoursUseCase

### Community 73 - "Community 73"
Cohesion: 0.19
Nodes (11): AdminSettingsScreen(), normalizeStorePolicyText(), emptyDetailRatings(), FeedbackScreen(), SENTIMENT_OPTIONS, paymentOptions, PaymentScreen(), QrTransferPanel() (+3 more)

### Community 74 - "Community 74"
Cohesion: 0.13
Nodes (14): AGENTS.md - mobile, Architecture Map, Canonical Commands, Change Rules, Critical Paths, Definition of Done, High-Risk Changes (Ask Before Proceeding), Maintenance Rule (+6 more)

### Community 75 - "Community 75"
Cohesion: 0.31
Nodes (8): _backend_root(), _catalog_payload(), _gauge_score(), _normalize_name(), Path, normalize string catalog  Revision ID: 20260412_0008 Revises: 20260411_0007 Crea, _slug(), upgrade()

### Community 76 - "Community 76"
Cohesion: 0.18
Nodes (7): JwtTokenService, AuthTokenPayload, get_current_user(), get_token_service(), Protocol, TokenService, HTTPAuthorizationCredentials

### Community 77 - "Community 77"
Cohesion: 0.31
Nodes (5): _float(), _mapping(), Any, Session, SqlAlchemyRecommendationLogRepository

### Community 78 - "Community 78"
Cohesion: 0.05
Nodes (41): AppError, api_health(), Session, _authorized_target_user_id(), generate_recommendations(), get_cached_recommendation_detail(), get_cached_recommendations(), CurrentUser (+33 more)

### Community 80 - "Community 80"
Cohesion: 0.06
Nodes (32): 1. Create deployment secrets, 2. Build and start without Cloudflare, 3. Connect Cloudflare Tunnel, 4. Operate safely, StringSence Docker Deployment, Backend, Backend Config And Runtime, Backend Domains And Use Cases (+24 more)

### Community 82 - "Community 82"
Cohesion: 0.25
Nodes (7): compilerOptions, strict, exclude, extends, **/._*, dist, expo/tsconfig.base

### Community 83 - "Community 83"
Cohesion: 0.18
Nodes (11): babel-preset-expo, eslint, eslint-config-expo, devDependencies, babel-preset-expo, eslint, eslint-config-expo, @types/react (+3 more)

### Community 84 - "Community 84"
Cohesion: 0.17
Nodes (11): Accessibility, Buttons, Cards And Elevation, Color Palette, Components, Design System Inspiration of Apple, Implementation Notes, Layout (+3 more)

### Community 85 - "Community 85"
Cohesion: 0.38
Nodes (4): AuthProvider, StrEnum, UserRole, RegisterUserUseCase

### Community 86 - "Community 86"
Cohesion: 0.13
Nodes (15): Active Runtime, AI Boundary, Authentication Abuse Boundary, Backend Architecture, Bounded Contexts, Catalog Boundary, Commerce Flow, Folder Map (+7 more)

### Community 87 - "Community 87"
Cohesion: 0.48
Nodes (5): _ensure_column(), _ensure_index(), upgrade(), Column, Inspector

### Community 88 - "Community 88"
Cohesion: 0.25
Nodes (7): BookingForm, BookingFormInput, bookingSchema, getSlotPeriod(), NewBookingContent(), SLOT_PERIOD_OPTIONS, SlotPeriod

### Community 89 - "Community 89"
Cohesion: 0.18
Nodes (11): 18. Directory Guide, `app/`, `components/*`, `components/shared/`, `components/ui/`, `lib/`, `mocks/`, `services/` (+3 more)

### Community 90 - "Community 90"
Cohesion: 0.12
Nodes (15): Agent comparison and validation (2026-08-24), Agent Scope Findings, Authentication Pages, Cash payment option (2026-08-18), Current page-review conclusion, Final FYP2 Classification, Follow-up fix evidence — 2026-08-17, Full Page Review (2026-08-17) (+7 more)

### Community 91 - "Community 91"
Cohesion: 0.53
Nodes (4): _backfill_inventory_status_columns(), _drop_named_legacy_booking_fk(), _rebuild_sqlite_bookings_without_legacy_fk(), upgrade()

### Community 92 - "Community 92"
Cohesion: 0.26
Nodes (12): formatDropOffDateTime(), formatTrackingDateTime(), getCurrentStageKey(), getHeroStatusChipClasses(), getHeroStatusLabel(), getLatestUpdate(), getNextStepLabel(), getQuoteStatus() (+4 more)

### Community 93 - "Community 93"
Cohesion: 0.20
Nodes (9): AGENTS.md - backend, Architecture Map, Change Rules, Definition of Done, High-Risk Changes (Ask Before Proceeding), Project Context, Quick Start, Scope (+1 more)

### Community 94 - "Community 94"
Cohesion: 0.60
Nodes (3): include_object(), run_migrations_offline(), run_migrations_online()

### Community 95 - "Community 95"
Cohesion: 0.21
Nodes (10): profile_to_dto(), ProfileOut, ProfilePayload, BaseModel, PlayerProfile, get_profile(), upsert_profile(), GetMyProfileUseCase (+2 more)

### Community 96 - "Community 96"
Cohesion: 0.18
Nodes (10): 12. Styling and Theming, 14. Screen Composition Pattern, 15. Current Architectural Strengths, 16. Current Architectural Constraints, 17. Recommended Evolution Path, 19. Summary, 1. Overview, 3. System Shape (+2 more)

### Community 97 - "Community 97"
Cohesion: 0.20
Nodes (9): AGENTS.md - StringSence, Architecture Map, Change Rules, Definition of Done, High-Risk Changes (Ask Before Proceeding), Project Context, Quick Start, Scope (+1 more)

### Community 98 - "Community 98"
Cohesion: 0.40
Nodes (4): config, { getDefaultConfig }, path, { withUniwindConfig }

### Community 101 - "Community 101"
Cohesion: 0.18
Nodes (11): 1. Start Postgres, 2. Start the backend, 3. Start the mobile app in a browser, 4. Start the mobile app on Expo Go, 5. Run the NLP workbench when you need fresh recommendation artifacts, Backend and NLP Integration, Current Delivery Boundary, Quick Start (+3 more)

### Community 102 - "Community 102"
Cohesion: 0.22
Nodes (8): Algorithm Version, Appendix D: Recommendation Algorithm, Core Recommendation Dimensions, Explainability Output, Final Score Formula, Important FYP1 Claim Boundary, Input Features, Preference Vector

### Community 103 - "Community 103"
Cohesion: 0.31
Nodes (3): PasswordResetRepository, datetime, Protocol

### Community 104 - "Community 104"
Cohesion: 0.17
Nodes (9): AdminLayout(), DEFERRED_ADMIN_SEGMENTS, BackendSessionBootstrap(), queryClient, RootErrorBoundary, mapBackendInventoryStringToStringItem(), mapBackendPricingModeToPriceStatus(), mapBackendUserToAdminProfile() (+1 more)

### Community 105 - "Community 105"
Cohesion: 0.22
Nodes (8): Appendix E: Key Source Code Extracts, Backend Application, Booking Status Transition Policy, Mobile Application, Mobile Recommendation Trigger, Notes, Recommendation Score Weights, Suggested Code Extracts for Report

### Community 106 - "Community 106"
Cohesion: 0.50
Nodes (3): NOTE: This file is generated by uniwind and it should not be edited manually., uniwind, UniwindConfig

### Community 124 - "Community 124"
Cohesion: 0.25
Nodes (7): Active Backend Boundary, Active Scope, Configuration, Deferred But Preserved, FYP-Scoped Player And Admin Agent, Re-Enabling Deferred Capabilities, Safety Rules That Remain Active

### Community 126 - "Appendix D: Recommendation Algorithm"
Cohesion: 0.14
Nodes (14): Account Security and Privacy, Auth, Bookings, Grounded Player And Admin Agent, Health, Human Support Conversations, Notifications, Payments and Wallet (+6 more)

### Community 127 - "Community 127"
Cohesion: 0.29
Nodes (8): AdminBookingsContent(), AdminQueueCard(), compareBookings(), FILTER_OPTIONS, getAdminActionLabel(), getPriceLabel(), getQueueMetaLabel(), STATUS_PRIORITY

### Community 131 - "Community 131"
Cohesion: 0.20
Nodes (9): appHeaderMetrics, AppHeaderVariant, AppPageHeader(), AppPageHeaderProps, contentStyles, minHeights, titleStyles, variantStyles (+1 more)

### Community 138 - "Community 138"
Cohesion: 0.28
Nodes (4): RecommendationLog, to_recommendation_log(), RecommendationLogRecord, ListRecommendationLogsUseCase

### Community 140 - "Community 140"
Cohesion: 0.39
Nodes (4): RecommendationRun, to_recommendation_run(), RecommendationRunRecord, GetRecommendationRunUseCase

### Community 143 - "Community 143"
Cohesion: 0.29
Nodes (3): Any, Protocol, RecommendationLogRepository

### Community 145 - "Community 145"
Cohesion: 0.33
Nodes (3): check_database_connection(), get_db(), Session

### Community 147 - "Community 147"
Cohesion: 0.29
Nodes (7): overrides, brace-expansion@1.1.16, brace-expansion@5.0.7, js-yaml@3.15.0, js-yaml@4.3.0, postcss, uuid

### Community 148 - "Community 148"
Cohesion: 0.29
Nodes (7): scripts, android, ios, lint, start, test, web

### Community 150 - "Community 150"
Cohesion: 0.53
Nodes (5): describeTensionFit(), FEATURE_LABELS, StringDetailScreen(), toAspectLabel(), toSentiment()

### Community 157 - "Community 157"
Cohesion: 0.47
Nodes (5): GameType, PlayerProfile, PlayingStyle, StrEnum, SkillLevel

### Community 187 - "Community 187"
Cohesion: 0.33
Nodes (6): Confidence and influence, Eligibility and Aggregation, Eligible records, Normalization, Preventing frequent-user dominance, Zero-feedback invariant

### Community 188 - "Community 188"
Cohesion: 0.70
Nodes (4): ensure_seed_user(), ensure_seed_users(), ensure_store_defaults(), Session

### Community 189 - "Community 189"
Cohesion: 0.60
Nodes (4): make_alembic_config(), test_booking_drift_repair_migration_restores_missing_booking_columns(), test_catalog_normalization_migration_preserves_existing_booking(), Config

### Community 192 - "11. Feature Module Breakdown"
Cohesion: 0.14
Nodes (11): API Contract, Response Shape, Active Structure, API Summary, Catalog Refactor Notes, Environment, Local Postgres, Recommendation Refactor Notes (+3 more)

### Community 193 - "5. Routing and Access Control"
Cohesion: 0.83
Nodes (3): headers(), login_admin(), test_admin_can_inspect_and_reimport_recommendation_matrix()

### Community 194 - "StringSense: AI-Driven Mobile Platform"
Cohesion: 0.22
Nodes (8): Admin, Backend, FYP1 Demo Proof, FYP1 Included, FYP2 Deferred, Player, Recommendation Positioning, StringSense FYP1 Scope

### Community 195 - "NLP Workbench Latest — Canonical Experiment Root"
Cohesion: 0.25
Nodes (8): 13. Unified Header System, Back button rules, Header types, Height and spacing guidance, Page mapping, Right-side action rules, Typography hierarchy, Visual direction

### Community 196 - "7. Data Layer Model"
Cohesion: 0.25
Nodes (7): description, name, version, x-cdm-codecs, x-cdm-host-versions, x-cdm-interface-versions, x-cdm-module-versions

### Community 197 - "Appendix B: Backend API Endpoint Summary"
Cohesion: 0.29
Nodes (7): API Layer, Business Logic, Clean Architecture Migration Map, ORM and Repositories, Runtime Entry, Security and Recommendation, Shared / Config

### Community 198 - "Appendix C: Database Schema Summary"
Cohesion: 0.60
Nodes (4): BookingUpdates(), BookingUpdatesProps, formatUpdateDate(), BookingUpdate

### Community 199 - "Appendix F: Testing Evidence"
Cohesion: 0.29
Nodes (6): impeccable, dependencies, impeccable, _npx, packages, impeccable

### Community 200 - "Appendix G: NLP and Recommendation Artifacts"
Cohesion: 0.29
Nodes (7): 11. Feature Module Breakdown, Admin Operations, Authentication, Booking, Deferred Chat, Profile And Deferred Player Retention Modules, Recommendation and catalog

### Community 201 - "_verify_internal_api_key"
Cohesion: 0.29
Nodes (7): 5. Routing and Access Control, `app/admin`, `app/auth`, `app/player`, Guard model, Root routing, Route groups

### Community 202 - "BookingUpdates.tsx"
Cohesion: 0.20
Nodes (8): Architecture Decisions, Features, Getting Started, Project Structure, StringSense: AI-Driven Mobile Platform, Styling Runtime, Tech Stack, Validation

### Community 203 - "2. Technology Stack"
Cohesion: 0.29
Nodes (6): dependencies, @playwright/cli, @playwright/cli, @playwright/cli, _npx, packages

### Community 204 - "6. State Architecture"
Cohesion: 0.29
Nodes (6): description, icons, manifest_version, name, update_url, version

### Community 205 - "RagAdapter"
Cohesion: 0.29
Nodes (6): dependencies, @playwright/cli, @playwright/cli, @playwright/cli, _npx, packages

### Community 206 - "8. Domain Model"
Cohesion: 0.29
Nodes (6): dependencies, @playwright/cli, @playwright/cli, @playwright/cli, _npx, packages

### Community 207 - "9. UI System"
Cohesion: 0.29
Nodes (6): Data boundary, Dataset summary, Included files, NLP Workbench Latest — Canonical Root, Run the notebooks, Runtime handoff

### Community 208 - "BusinessHours"
Cohesion: 0.33
Nodes (6): 7.1 Mutable runtime state: `store/appStore.ts`, 7.2 Hybrid player backend bridge, 7.3 Read helpers over seed data: `services/mockAppService.ts`, 7.4 Mock data sources: `mocks/`, 7. Data Layer Model, Architectural note

### Community 209 - "10. Navigation UX Structure"
Cohesion: 0.40
Nodes (4): Admin Endpoints, Appendix B: Backend API Endpoint Summary, Notes for Report, Public and Player Endpoints

### Community 210 - "eslint.config.js"
Cohesion: 0.40
Nodes (4): Appendix C: Database Schema Summary, Important Design Boundaries, Main Tables, Suggested ERD Grouping

### Community 211 - "00_appendix_index.md"
Cohesion: 0.40
Nodes (4): Appendix F: Testing Evidence, Recommended Test Evidence Table, Report Notes, Suggested Validation Commands

### Community 212 - "axios"
Cohesion: 0.40
Nodes (4): Appendix G: NLP and Recommendation Artifacts, Backend Integration, Main Artifacts, Suggested Appendix Use

### Community 213 - "test_runtime_boundaries.py"
Cohesion: 0.40
Nodes (5): Current feedback path, Current System Evidence, Feedback collection corrections implemented, Migration alignment implemented, Runtime path

### Community 214 - "expo-blur"
Cohesion: 0.40
Nodes (5): 2. Technology Stack, Core framework, Forms and validation, State and data, UI and styling

### Community 215 - "expo-constants"
Cohesion: 0.40
Nodes (5): 6. State Architecture, Derived accessors, Runtime and Bundling Constraints, Store actions, Store contents

### Community 216 - "expo-linking"
Cohesion: 0.40
Nodes (4): is_preloaded, manifest_version, name, version

### Community 217 - "expo-splash-screen"
Cohesion: 0.40
Nodes (4): manifest_version, name, pre_installed, version

### Community 218 - "bootstrap.sh"
Cohesion: 0.40
Nodes (4): manifest_version, name, pre_installed, version

### Community 219 - "react-native"
Cohesion: 0.40
Nodes (4): manifest_version, name, pre_installed, version

### Community 220 - "react-native-gesture-handler"
Cohesion: 0.50
Nodes (4): 8. Domain Model, Important enums and unions, Inventory modeling note, Main entities

### Community 221 - "admin-bookings-snapshot.md"
Cohesion: 0.50
Nodes (4): 9.1 HeroUI wrapper layer, 9.2 App primitives, 9.3 Shared layout shell, 9. UI System

### Community 223 - "auth-login-snapshot.md"
Cohesion: 0.67
Nodes (3): 10. Navigation UX Structure, Admin Information Architecture, Player information architecture

### Community 224 - "auth-welcome-snapshot.md"
Cohesion: 0.40
Nodes (5): Implementation Record, Phase 1: Correct feedback collection — completed, Phase 2: Build and inspect community aggregates — completed, Phase 3: Enable community calibration and V11 CF — completed, Phase 4: Player and admin community presentation — completed

### Community 225 - "player-home-snapshot.md"
Cohesion: 0.50
Nodes (4): Algorithm version, Candidate loading, Recommendation Integration, Scoring order

### Community 237 - "API Contract"
Cohesion: 0.50
Nodes (4): API Contract, Community summary, Create feedback, Update feedback

### Community 238 - "Test Plan"
Cohesion: 0.50
Nodes (4): Backend unit and integration tests, Mobile tests, Required validation commands, Test Plan

### Community 239 - "Feedback Form Design"
Cohesion: 0.50
Nodes (4): Durability flow, Feedback Form Design, Field semantics, Interaction rules

### Community 240 - "RequestPasswordResetUseCase"
Cohesion: 0.20
Nodes (3): CachedRecommendationRecord, Protocol, RecommendationRepository

### Community 241 - "Versioning and Audit Evidence"
Cohesion: 0.67
Nodes (3): Community source version, Recommendation rationale, Versioning and Audit Evidence

### Community 242 - "Database Design"
Cohesion: 0.67
Nodes (3): Database Design, Existing table remains authoritative, Required indexes

### Community 243 - "Player Experience"
Cohesion: 0.67
Nodes (3): Feedback screen, Player Experience, String catalog presentation

### Community 266 - "page_to_dict"
Cohesion: 0.22
Nodes (6): page_to_dict(), Any, public_list_slots(), date, ListSlotsUseCase, T

### Community 267 - "Agent Scope Simplification Progress"
Cohesion: 0.33
Nodes (5): 2026-08-17, 2026-08-17 follow-up fixes, 2026-08-18, 2026-08-24, Agent Scope Simplification Progress

### Community 269 - "normalizeUploadFile"
Cohesion: 0.50
Nodes (4): buildBookingUpdateForm(), buildImageUploadForm(), buildPaymentForm(), normalizeUploadFile()

## Knowledge Gaps
- **719 isolated node(s):** `1. Create deployment secrets`, `2. Build and start without Cloudflare`, `3. Connect Cloudflare Tunnel`, `4. Operate safely`, `build-backend-image.sh script` (+714 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **68 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_settings()` connect `Community 6` to `Community 59`, `Community 10`, `Community 76`, `Community 78`, `Community 15`, `Community 27`, `Community 188`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Why does `ensure_catalog_seeded()` connect `Community 15` to `Community 34`, `Community 6`, `Community 14`, `Community 23`, `Community 188`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **Why does `react` connect `Community 55` to `Community 0`, `Community 62`, `Community 39`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Are the 42 inferred relationships involving `NotFoundError` (e.g. with `get_customer_owned_booking()` and `get_media_file()`) actually correct?**
  _`NotFoundError` has 42 INFERRED edges - model-reasoned connections that need verification._
- **What connects `1. Create deployment secrets`, `2. Build and start without Cloudflare`, `3. Connect Cloudflare Tunnel` to the rest of the system?**
  _719 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.09334537789822343 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.11875843454790823 - nodes in this community are weakly interconnected._