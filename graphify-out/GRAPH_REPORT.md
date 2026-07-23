# Graph Report - .  (2026-07-23)

> Generated before the same-day API-only page remediation. Preserve this report
> as a graph snapshot; use `docs/codebase-map.md` for the current route, model,
> migration, and test inventory.

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 2094 nodes · 5613 edges · 191 communities (154 shown, 37 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 668 edges (avg confidence: 0.69)
- Token cost: 0 input · 0 output

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
- Community 104
- Community 105
- Community 106
- Community 107
- Community 123
- Community 124
- Community 127
- Community 128
- Community 129
- Community 130
- Community 131
- Community 132
- Community 133
- Community 134
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
- Community 187
- Community 188
- Community 189
- Community 191

## God Nodes (most connected - your core abstractions)
1. `useAppStore` - 82 edges
2. `useCurrentUser()` - 78 edges
3. `HeroText` - 71 edges
4. `CurrentUser` - 69 edges
5. `AppCard()` - 51 edges
6. `AppScreen()` - 46 edges
7. `useStrings()` - 46 edges
8. `NotFoundError` - 45 edges
9. `AppChip()` - 45 edges
10. `Page` - 43 edges

## Surprising Connections (you probably didn't know these)
- `test_get_string_accepts_brand_and_punctuation_aliases()` --calls--> `RecommendationService`  [INFERRED]
  backend/tests/test_ai_service_service.py → backend/ai_service/service.py
- `to_string_item()` --calls--> `StringTag`  [INFERRED]
  backend/app/adapters/persistence/sqlalchemy/repositories/mappers.py → backend/app/domain/catalog/entities.py
- `to_business_hours()` --calls--> `BusinessHoursDay`  [INFERRED]
  backend/app/adapters/persistence/sqlalchemy/repositories/mappers.py → backend/app/domain/store/entities.py
- `reset_unified_backend_db()` --calls--> `drop_all_tables()`  [INFERRED]
  backend/tests/conftest.py → backend/app/adapters/persistence/sqlalchemy/session.py
- `upsert_profile()` --calls--> `PlayerProfile`  [INFERRED]
  backend/app/entrypoints/api/routes/profile_routes.py → backend/app/domain/profile/entities.py

## Import Cycles
- None detected.

## Communities (191 total, 37 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.09
Nodes (59): PRIMARY_ACTIONS, RequestCodeForm, requestCodeSchema, ResetPasswordForm, resetPasswordSchema, advancedPreferenceKeys, budgetOptions, preferredFeelOptions (+51 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (76): AdminBookingDetailScreen(), AdminUpdateFeed(), getAllowedNextStatuses(), getPriceStateLabel(), getStatusHeroCopy(), getUpdateMetaLabel(), getWorkflowActionLabel(), getWorkflowOptionHint() (+68 more)

### Community 2 - "Community 2"
Cohesion: 0.08
Nodes (58): AdminBusinessHoursScreen(), AdminLayout(), DEFERRED_ADMIN_SEGMENTS, AdminRecommendationRunsScreen(), getStringLabel(), AdminSettingsScreen(), normalizeFyp1PolicyText(), AdminAnalyticsScreen() (+50 more)

### Community 3 - "Community 3"
Cohesion: 0.05
Nodes (45): AdminTabIcon(), AuthLayout(), demoUsers, LoginForm, loginSchema, LoginScreen(), RegisterForm, registerSchema (+37 more)

### Community 4 - "Community 4"
Cohesion: 0.06
Nodes (47): BackendBookingPhotoType, BackendUploadFile, buildBookingUpdateForm(), buildImageUploadForm(), normalizeUploadFile(), RequestOptions, BackendAdminInventoryString, BackendAnalyticsSummary (+39 more)

### Community 5 - "Community 5"
Cohesion: 0.08
Nodes (19): admin_recommendation_run_detail(), AppError, BadRequestError, ForbiddenError, NotFoundError, Any, UnauthorizedError, LoginUseCase (+11 more)

### Community 6 - "Community 6"
Cohesion: 0.14
Nodes (40): handle_app_error(), handle_http_exception(), handle_integrity_error(), handle_validation_error(), Session, root_health(), error_payload(), Any (+32 more)

### Community 7 - "Community 7"
Cohesion: 0.09
Nodes (25): AdminPaymentsScreen(), AdminRecommendationRunDetailScreen(), buildRationaleSummary(), buildSnapshotItems(), formatScalarValue(), getStringLabel(), paymentOptions, ChatBubble() (+17 more)

### Community 8 - "Community 8"
Cohesion: 0.12
Nodes (23): RecommendationCandidateModel, _attacking_request(), _candidate(), _candidate_with_core_scores(), FakeProfileRepository, FakeRecommendationLogRepository, FakeRecommendationRepository, _optional_float() (+15 more)

### Community 9 - "Community 9"
Cohesion: 0.09
Nodes (29): AdminInventoryDetailScreen(), AVAILABILITY_OPTIONS, buildCatalogPayload(), buildInventoryPayload(), buildOfficialPerformancePayload(), CATALOG_VISIBILITY_OPTIONS, CATEGORY_OPTIONS, comparableCatalogState() (+21 more)

### Community 10 - "Community 10"
Cohesion: 0.14
Nodes (20): AuthResponse, ForgotPasswordRequest, ForgotPasswordRequestResponse, ForgotPasswordResetRequest, LoginRequest, MessageResponse, BaseModel, RegisterRequest (+12 more)

### Community 11 - "Community 11"
Cohesion: 0.18
Nodes (29): RecommendationFeatureSignalModel, _auxiliary_scores(), _budget_fit_score(), _build_feature_evidence(), _build_reasons(), _candidate_feature_source_version(), _candidate_matrix_version(), clamp01() (+21 more)

### Community 12 - "Community 12"
Cohesion: 0.13
Nodes (27): booking_to_dto(), BookingOut, page_to_dict(), Any, CurrentUser, BaseModel, admin_bookings(), admin_check_in_booking() (+19 more)

### Community 13 - "Community 13"
Cohesion: 0.11
Nodes (31): formatTensionRange(), apiRootUrl(), resolveBackendMediaUrl(), deriveCategory(), deriveGaugeBounds(), deriveMainTrait(), deriveMaterial(), deriveRecommendedTension() (+23 more)

### Community 14 - "Community 14"
Cohesion: 0.17
Nodes (10): StringCatalogItem, OfficialPerformanceRecord, StringItem, StringOfficialPerformance, to_official_performance(), to_string_item(), OfficialPerformanceRecord, Session (+2 more)

### Community 15 - "Community 15"
Cohesion: 0.15
Nodes (27): _build_evidence_note(), _build_matrix_entries(), CatalogLookupEntry, _cell_text(), _clean_text(), _column_index(), CsvFeatureSpec, _first_sheet_name() (+19 more)

### Community 17 - "Community 17"
Cohesion: 0.16
Nodes (14): RecommendationScoreCache, UserPreferenceMatrix, _float_or_none(), _matrix_by_source(), _optional_string(), Session, _recommendation_feature_key(), _required_float() (+6 more)

### Community 18 - "Community 18"
Cohesion: 0.17
Nodes (25): ProfileRecommendationPayload, Any, BaseModel, datetime, recommendation_detail_to_dto(), recommendation_log_to_dict(), recommendation_request_to_domain(), recommendation_response_to_dto() (+17 more)

### Community 19 - "Community 19"
Cohesion: 0.16
Nodes (16): review_analyze(), ExplainRequest, ExplainResponse, BaseModel, RagQueryRequest, RagQueryResponse, RecommendationResponse, RecommendationResult (+8 more)

### Community 20 - "Community 20"
Cohesion: 0.18
Nodes (23): BudgetRange, ExplainRequest, ExplainResponse, BaseModel, RecommendationContext, RecommendationResultItem, RecommendRequest, RecommendResponse (+15 more)

### Community 21 - "Community 21"
Cohesion: 0.10
Nodes (9): InventoryMovementRecord, Any, Protocol, RecommendationLogRepository, Page, ListInventoryMovementsUseCase, StringItem, ListRecommendationLogsUseCase (+1 more)

### Community 22 - "Community 22"
Cohesion: 0.11
Nodes (19): AdminInventoryStringOut, inventory_string_to_dto(), StringItem, string_to_dto(), StringOut, StringWritePayload, admin_create_string(), admin_deactivate_string() (+11 more)

### Community 23 - "Community 23"
Cohesion: 0.23
Nodes (23): AspectScoreMap, approved_catalog_defaults(), approved_row_to_values(), as_string(), build_sku(), catalog_source_path(), clamp01(), derive_aspect_scores() (+15 more)

### Community 24 - "Community 24"
Cohesion: 0.13
Nodes (7): BookingRecord, BookingRepository, datetime, Protocol, ListAdminBookingsUseCase, ListMyBookingsUseCase, ListSlotsUseCase

### Community 25 - "Community 25"
Cohesion: 0.11
Nodes (12): MOCK_BUSINESS_HOURS, MOCK_ADMIN_SETTINGS, MOCK_NOTIFICATION_PREFERENCES, MOCK_PLAYERS, MOCK_USERS, getAdminSettings(), getBusinessHoursForAdmin(), getNotificationPreferences() (+4 more)

### Community 26 - "Community 26"
Cohesion: 0.17
Nodes (8): _booking_string_name(), to_booking_record(), Session, SqlAlchemyBookingRepository, BookingStatusHistoryEntry, BookingUpdateEntry, booking_order_code(), Booking

### Community 27 - "Community 27"
Cohesion: 0.15
Nodes (16): admin_add_booking_update(), admin_delete_string_image(), admin_upload_booking_photo(), admin_upload_string_image(), BookingPhotoType, UploadFile, read_upload_bytes_limited(), save_string_image_upload() (+8 more)

### Community 28 - "Community 28"
Cohesion: 0.09
Nodes (22): backgroundColor, foregroundImage, adaptiveIcon, edgeToEdgeEnabled, predictiveBackGestureEnabled, expo, android, icon (+14 more)

### Community 29 - "Community 29"
Cohesion: 0.21
Nodes (21): _as_string(), _aspect_value(), _clamp01(), _derive_scores(), _first_number(), _first_string(), get_fallback_jsonl_path(), get_matrix_path() (+13 more)

### Community 30 - "Community 30"
Cohesion: 0.15
Nodes (8): to_user_account(), Session, SqlAlchemyUserRepository, UserAccount, Protocol, UserRepository, GetCurrentUserUseCase, test_sqlalchemy_booking_repository_creates_history_entries()

### Community 31 - "Community 31"
Cohesion: 0.17
Nodes (20): CatalogTagOut, inventory_movement_to_dto(), InventoryMovementOut, InventoryUpdatePayload, official_performance_to_dto(), OfficialPerformanceOut, OfficialPerformancePayload, BaseModel (+12 more)

### Community 32 - "Community 32"
Cohesion: 0.10
Nodes (20): BookingUpdatesProps, MOCK_NOTIFICATIONS, AdvancedPreferenceKey, BookingUpdate, BudgetRange, BusinessHoursDay, ChatMessageRole, ConversationMode (+12 more)

### Community 33 - "Community 33"
Cohesion: 0.15
Nodes (17): AdminChatQueueScreen(), PlayerChatDetailScreen(), PlayerChatThreadsScreen(), BrandGroup, CatalogListItem, DisplayMode, isBrandGroup(), modeOptions (+9 more)

### Community 34 - "Community 34"
Cohesion: 0.26
Nodes (14): Base, Booking, BookingStatusHistory, BookingUpdate, RecommendationRunItem, Brand, InventoryMovement, RecommendationFeatureDefinition (+6 more)

### Community 35 - "Community 35"
Cohesion: 0.18
Nodes (11): RecommendationLog, RecommendationRun, to_recommendation_log(), to_recommendation_run(), _float(), _mapping(), Any, Session (+3 more)

### Community 36 - "Community 36"
Cohesion: 0.20
Nodes (11): RecommendationDetailModel, RecommendationResponseModel, RecommendationResultModel, _feature_source_version_from_results(), _float_or_none(), GenerateRecommendationUseCase, _isoformat_or_none(), _matrix_version_from_results() (+3 more)

### Community 37 - "Community 37"
Cohesion: 0.13
Nodes (12): inventory_availability(), StringItem, AnalyticsSummary, AnalyticsWorkloadEntry, BookingSlot, BusinessHoursDay, CheckInLookup, ServiceQueue (+4 more)

### Community 38 - "Community 38"
Cohesion: 0.20
Nodes (15): analytics_summary_to_dto(), AnalyticsSummaryOut, AnalyticsWorkloadEntryOut, BookingSlotOut, BusinessHoursDayPayload, CheckInLookupOut, CheckInPayload, BaseModel (+7 more)

### Community 39 - "Community 39"
Cohesion: 0.12
Nodes (17): axios, clsx, expo-blur, expo-constants, expo-linking, expo-splash-screen, dependencies, axios (+9 more)

### Community 40 - "Community 40"
Cohesion: 0.13
Nodes (12): explain(), get_string(), ExplainRequest, ExplainResponse, RagQueryRequest, RagQueryResponse, rag_query(), _verify_internal_api_key() (+4 more)

### Community 41 - "Community 41"
Cohesion: 0.19
Nodes (12): BookingStatus, StrEnum, booking_history_to_dto(), booking_update_to_dto(), BookingStatusHistoryOut, BookingUpdateOut, CreateBookingPayload, BaseModel (+4 more)

### Community 42 - "Community 42"
Cohesion: 0.17
Nodes (6): StoreSettings, to_store_settings(), StoreSettingsRecord, Protocol, StoreRepository, UpdateStoreSettingsUseCase

### Community 43 - "Community 43"
Cohesion: 0.23
Nodes (13): StringRecommendationMatrix, _build_catalog_lookup(), ensure_recommendation_feature_definitions(), import_recommendation_matrix_csv(), normalize_legacy_feature_keys(), Session, ensure_catalog_seeded(), RecommendationMatrixImportReport (+5 more)

### Community 44 - "Community 44"
Cohesion: 0.15
Nodes (11): RecommendationRequestModel, Fyp1ContentRecommendationScorer, _primary_fit_angle(), FYP1 scorer: rule-enhanced, confidence-aware, content-based, explainable., _trade_off_summary(), Protocol, StringItem, RecommendationEngine (+3 more)

### Community 45 - "Community 45"
Cohesion: 0.20
Nodes (14): AdminInventoryScreen(), InventorySort, InventoryStatusFilter, matchesStatusFilter(), SearchField(), SORT_OPTIONS, sortInventory(), STATUS_FILTERS (+6 more)

### Community 46 - "Community 46"
Cohesion: 0.22
Nodes (14): buildMatchReasons(), buildRecommendationSummary(), clampPercent(), compactSentence(), formatCurrency(), formatScore(), getBudgetCopy(), getReviewStrengths() (+6 more)

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
Cohesion: 0.19
Nodes (3): BaseSettings, Path, Settings

### Community 51 - "Community 51"
Cohesion: 0.29
Nodes (12): get_settings(), get_media_file(), build_signed_media_url(), _detect_image_extension(), Path, _resolve_upload_destination(), resolve_upload_media_path(), save_booking_update_photo() (+4 more)

### Community 52 - "Community 52"
Cohesion: 0.21
Nodes (8): validate_status_transition(), validate_terminal_status_note(), ConflictError, datetime, UpdateBookingStatusUseCase, ConfirmCheckInUseCase, test_booking_status_transition_accepts_valid_progression(), test_booking_status_transition_rejects_invalid_progression()

### Community 53 - "Community 53"
Cohesion: 0.21
Nodes (10): profile_to_dto(), ProfileOut, ProfilePayload, BaseModel, PlayerProfile, get_profile(), upsert_profile(), GetMyProfileUseCase (+2 more)

### Community 54 - "Community 54"
Cohesion: 0.24
Nodes (13): get_booking_repository(), get_catalog_repository(), get_current_admin(), get_current_customer(), get_password_reset_repository(), get_profile_repository(), get_recommendation_log_repository(), get_recommendation_repository() (+5 more)

### Community 55 - "Community 55"
Cohesion: 0.30
Nodes (13): AdminInventoryCard(), AdminInventoryPreviewCard(), AdminStringThumbnail(), buildInitials(), getAttentionChipVariant(), getBadgeVariant(), getPriceChipVariant(), QuickAction() (+5 more)

### Community 56 - "Community 56"
Cohesion: 0.18
Nodes (7): JwtTokenService, AuthTokenPayload, get_current_user(), get_token_service(), Protocol, TokenService, HTTPAuthorizationCredentials

### Community 57 - "Community 57"
Cohesion: 0.22
Nodes (9): settings_to_dto(), StoreSettingsOut, StoreSettingsPayload, admin_get_store_settings(), admin_update_store_settings(), public_get_store_settings(), public_list_slots(), date (+1 more)

### Community 58 - "Community 58"
Cohesion: 0.28
Nodes (13): advancedPreferencesForPayload(), buildBackendProfilePayload(), buildRecommendationPayload(), deriveAdvancedPreferences(), derivedElasticityPreference(), derivedStringMovementPreference(), derivedTensionRetentionPreference(), derivedValuePreference() (+5 more)

### Community 59 - "Community 59"
Cohesion: 0.22
Nodes (8): _collapsed_aspect_scores(), _normalize_availability_status(), _normalize_pricing_mode(), _normalized_name(), canonical_feature_key(), domain_feature_key(), InventoryAvailabilityStatus, InventoryPricingMode

### Community 60 - "Community 60"
Cohesion: 0.21
Nodes (7): business_hours_to_dto(), StoreBusinessHoursOut, StoreBusinessHoursPayload, admin_get_business_hours(), admin_update_business_hours(), GetBusinessHoursUseCase, UpdateBusinessHoursUseCase

### Community 61 - "Community 61"
Cohesion: 0.20
Nodes (11): InventoryFormState, buildStringSearchBlob(), clampScore(), InventoryAttentionState, sanitizePerformanceScores(), deriveScores(), mapOfficialPerformanceToPerformanceScores(), InventoryAvailability (+3 more)

### Community 62 - "Community 62"
Cohesion: 0.26
Nodes (11): buildTrackingSteps(), formatTrackingDateTime(), getStageBadge(), NODE_STYLES, TimelineStep, TimelineStepDefinition, TimelineVisualState, TRACKING_SEQUENCE (+3 more)

### Community 63 - "Community 63"
Cohesion: 0.23
Nodes (10): MOCK_ADMINS, AppStoreState, AdminProfile, AdminSettings, AppUser, BookingDraft, NotificationPreferences, PlayerProfile (+2 more)

### Community 64 - "Community 64"
Cohesion: 0.17
Nodes (11): engines, node, main, name, private, scripts, android, ios (+3 more)

### Community 65 - "Community 65"
Cohesion: 0.25
Nodes (6): Profile, PlayerProfile, to_profile(), PlayerProfile, Session, SqlAlchemyProfileRepository

### Community 66 - "Community 66"
Cohesion: 0.20
Nodes (5): Clock, datetime, Protocol, RequestPasswordResetUseCase, ResetPasswordUseCase

### Community 67 - "Community 67"
Cohesion: 0.29
Nodes (10): buildLocalPatch(), mapPricingModeToPriceStatus(), deriveAvailabilityStatus(), derivePriceStatus(), formatGaugeRange(), createMockStringItem(), MOCK_STRINGS, mapBackendInventoryStringToStringItem() (+2 more)

### Community 68 - "Community 68"
Cohesion: 0.20
Nodes (9): BookingForm, BookingFormInput, bookingSchema, getSlotPeriod(), SLOT_PERIOD_OPTIONS, SlotPeriod, AppSegmentedControl(), AppSegmentedControlProps (+1 more)

### Community 69 - "Community 69"
Cohesion: 0.18
Nodes (7): RacketPassportCardProps, MOCK_BOOKINGS, MOCK_PAYMENTS, MOCK_RACKETS, getBookingById(), Payment, RacketPassport

### Community 70 - "Community 70"
Cohesion: 0.31
Nodes (5): recommend(), RecommendationRequest, StringRecord, ExplainRequest, ExplainResponse

### Community 71 - "Community 71"
Cohesion: 0.27
Nodes (8): BaseModel, RagDocument, RagMatch, RagQueryRequest, RagQueryResponse, RagQueryRequest, RagQueryResponse, query_rag()

### Community 72 - "Community 72"
Cohesion: 0.31
Nodes (5): StoreBusinessHours, to_business_hours(), Session, SqlAlchemyStoreRepository, StoreBusinessHoursRecord

### Community 73 - "Community 73"
Cohesion: 0.13
Nodes (13): to_recommendation_matrix_entry(), to_recommendation_run_item(), InventorySnapshot, RecommendationMatrixEntryRecord, RecommendationMatrixInspectionRecord, StringOfficialPerformance, StringTag, RecommendationRunItemRecord (+5 more)

### Community 74 - "Community 74"
Cohesion: 0.24
Nodes (3): CachedRecommendationRecord, Protocol, RecommendationRepository

### Community 75 - "Community 75"
Cohesion: 0.31
Nodes (8): _backend_root(), _catalog_payload(), _gauge_score(), _normalize_name(), Path, normalize string catalog  Revision ID: 20260412_0008 Revises: 20260411_0007 Crea, _slug(), upgrade()

### Community 76 - "Community 76"
Cohesion: 0.28
Nodes (6): extract_ascii_words(), normalize_lookup_name(), _build_string_lookup_index(), _lookup_targets(), _string_lookup_aliases(), _unique()

### Community 77 - "Community 77"
Cohesion: 0.39
Nodes (7): ensure_seed_user(), ensure_seed_users(), ensure_store_defaults(), Session, create_all_tables(), lifespan(), reset_unified_backend_db()

### Community 78 - "Community 78"
Cohesion: 0.25
Nodes (6): check_database_connection(), drop_all_tables(), get_db(), Session, api_health(), Session

### Community 79 - "Community 79"
Cohesion: 0.42
Nodes (5): _budget_fit_score(), _item_price_tier(), StringItem, RecommendationEngineAdapter, get_recommendation_engine()

### Community 80 - "Community 80"
Cohesion: 0.31
Nodes (3): PasswordResetRepository, datetime, Protocol

### Community 81 - "Community 81"
Cohesion: 0.43
Nodes (6): BaseModel, ReviewAnalysisRequest, ReviewAnalysisResponse, ReviewAspectSummary, ReviewRecord, analyze_reviews()

### Community 82 - "Community 82"
Cohesion: 0.25
Nodes (7): compilerOptions, strict, exclude, extends, **/._*, dist, expo/tsconfig.base

### Community 83 - "Community 83"
Cohesion: 0.29
Nodes (7): babel-preset-expo, devDependencies, babel-preset-expo, @types/react, typescript, @types/react, typescript

### Community 85 - "Community 85"
Cohesion: 0.38
Nodes (4): AuthProvider, StrEnum, UserRole, RegisterUserUseCase

### Community 86 - "Community 86"
Cohesion: 0.38
Nodes (5): PopularString, popular_string_to_dto(), PopularStringOut, admin_popular_strings(), GetStoreAnalyticsUseCase

### Community 87 - "Community 87"
Cohesion: 0.48
Nodes (5): _ensure_column(), _ensure_index(), upgrade(), Column, Inspector

### Community 88 - "Community 88"
Cohesion: 0.33
Nodes (5): SlotPicker(), SlotPickerProps, MOCK_BOOKING_SLOTS, SLOT_DATA, BookingSlot

### Community 89 - "Community 89"
Cohesion: 0.47
Nodes (5): GameType, PlayerProfile, PlayingStyle, StrEnum, SkillLevel

### Community 90 - "Community 90"
Cohesion: 0.40
Nodes (3): ProfileRepository, PlayerProfile, Protocol

### Community 91 - "Community 91"
Cohesion: 0.53
Nodes (4): _backfill_inventory_status_columns(), _drop_named_legacy_booking_fk(), _rebuild_sqlite_bookings_without_legacy_fk(), upgrade()

### Community 92 - "Community 92"
Cohesion: 0.33
Nodes (5): MOCK_WALLET_TRANSACTIONS, MOCK_WALLETS, getWalletByUserId(), WalletBalance, WalletTransaction

### Community 93 - "Community 93"
Cohesion: 0.50
Nodes (3): datetime, SystemClock, get_clock()

### Community 94 - "Community 94"
Cohesion: 0.60
Nodes (3): include_object(), run_migrations_offline(), run_migrations_online()

### Community 96 - "Community 96"
Cohesion: 0.60
Nodes (4): make_alembic_config(), test_booking_drift_repair_migration_restores_missing_booking_columns(), test_catalog_normalization_migration_preserves_existing_booking(), Config

### Community 97 - "Community 97"
Cohesion: 0.40
Nodes (4): ConversationCardProps, MOCK_CHAT_CONVERSATIONS, getConversationById(), ChatConversation

### Community 98 - "Community 98"
Cohesion: 0.40
Nodes (4): config, { getDefaultConfig }, path, { withUniwindConfig }

### Community 105 - "Community 105"
Cohesion: 0.50
Nodes (3): MOCK_ADMIN_ANALYTICS, getAdminAnalytics(), AdminAnalyticsSummary

### Community 106 - "Community 106"
Cohesion: 0.50
Nodes (3): NOTE: This file is generated by uniwind and it should not be edited manually., uniwind, UniwindConfig

## Knowledge Gaps
- **208 isolated node(s):** `StringOfficialPerformance`, `BookingSlot`, `stringsense-backend`, `name`, `slug` (+203 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **37 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `CurrentUser` connect `Community 12` to `Community 5`, `Community 10`, `Community 14`, `Community 17`, `Community 18`, `Community 19`, `Community 22`, `Community 26`, `Community 27`, `Community 30`, `Community 31`, `Community 35`, `Community 38`, `Community 49`, `Community 53`, `Community 54`, `Community 56`, `Community 57`, `Community 60`, `Community 65`, `Community 72`, `Community 79`, `Community 84`, `Community 85`, `Community 86`, `Community 93`?**
  _High betweenness centrality (0.091) - this node is a cross-community bridge._
- **Why does `get_settings()` connect `Community 51` to `Community 5`, `Community 6`, `Community 10`, `Community 43`, `Community 77`, `Community 50`, `Community 22`, `Community 56`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Why does `Page` connect `Community 21` to `Community 34`, `Community 35`, `Community 102`, `Community 8`, `Community 12`, `Community 14`, `Community 47`, `Community 48`, `Community 22`, `Community 24`, `Community 26`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Are the 17 inferred relationships involving `CurrentUser` (e.g. with `SqlAlchemyBookingRepository` and `SqlAlchemyCatalogRepository`) actually correct?**
  _`CurrentUser` has 17 INFERRED edges - model-reasoned connections that need verification._
- **What connects `StringOfficialPerformance`, `BookingSlot`, `stringsense-backend` to the rest of the system?**
  _208 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.08741408934707903 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.060678962844159315 - nodes in this community are weakly interconnected._
