# Graph Report - StringSence  (2026-09-02)

## Corpus Check
- 464 files · ~2,144,481 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3957 nodes · 9321 edges · 329 communities (262 shown, 67 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 1044 edges (avg confidence: 0.74)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `1f2706d0`
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
- Community 108
- Community 109
- Community 110
- Community 111
- Community 112
- Community 113
- Community 114
- Community 115
- Community 116
- Community 117
- Community 118
- Community 119
- Community 120
- Community 121
- Community 122
- Community 123
- Community 124
- Community 125
- Appendix D: Recommendation Algorithm
- Community 127
- Community 128
- Community 129
- Community 130
- Community 131
- Community 132
- Community 133
- Community 134
- Community 135
- Community 136
- Community 137
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
- Community 152
- Community 153
- Community 154
- Community 155
- Community 156
- Community 157
- Community 158
- Community 159
- Community 160
- Community 161
- Community 162
- Community 163
- Community 164
- Community 165
- Community 166
- Community 167
- Community 168
- Community 169
- Community 170
- Community 171
- Community 172
- Community 173
- Community 174
- Community 175
- Community 176
- Community 177
- Community 178
- Community 179
- Community 180
- Community 181
- Community 182
- Community 183
- Community 184
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
- react-native-gesture-handler
- OfficialPerformanceRecord
- StringItem
- PlayerProfile
- StringItem
- StringItem
- PlayerProfile
- StringItem
- PlayerProfile
- PlayerProfile
- API Contract
- Test Plan
- Feedback Form Design
- RequestPasswordResetUseCase
- Versioning and Audit Evidence
- Database Design
- Player Experience
- conftest.py
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
- BudgetRange
- auth_routes.py
- page_to_dict
- Agent Scope Simplification Progress
- react-native
- react-native-qrcode-svg
- uxAccessibility.test.mjs
- StringItem
- Session
- react-native-svg
- BookingSlot
- expo
- FeedbackEligibilityOut
- FeedbackOut
- Racket
- .replace_score_cache
- Local Development Flow
- entities.py
- UpsertMyProfileUseCase
- Administrator Acceptance Record
- Proposed approval gates
- feedback_snapshot_to_dict
- BookingUpdates.tsx
- Base
- recommendation_features.py
- agentHistory.ts
- Collection
- Any
- Path
- datetime
- Page

## God Nodes (most connected - your core abstractions)
1. `CurrentUser` - 108 edges
2. `useAppStore` - 93 edges
3. `useCurrentUser()` - 72 edges
4. `HeroText` - 71 edges
5. `useBackendAccessToken()` - 68 edges
6. `expo-router` - 65 edges
7. `backendApi` - 50 edges
8. `AppCard()` - 50 edges
9. `get_settings()` - 47 edges
10. `useStrings()` - 44 edges

## Surprising Connections (you probably didn't know these)
- `_load_backend_components()` --indirect_call--> `RecommendationFeatureSignalModel`  [INFERRED]
  ml/nlp-workbench-latest/src/stringsense_nlp/bert_review.py → backend/app/domain/recommendation/entities.py
- `_load_backend_components()` --indirect_call--> `InventorySnapshot`  [INFERRED]
  ml/nlp-workbench-latest/src/stringsense_nlp/bert_review.py → backend/app/domain/catalog/entities.py
- `_load_backend_components()` --indirect_call--> `ContentRecommendationScorer`  [INFERRED]
  ml/nlp-workbench-latest/src/stringsense_nlp/bert_review.py → backend/app/domain/recommendation/scoring.py
- `_load_backend_components()` --indirect_call--> `RecommendationRequestModel`  [INFERRED]
  ml/nlp-workbench-latest/src/stringsense_nlp/bert_review.py → backend/app/domain/recommendation/entities.py
- `_load_backend_components()` --indirect_call--> `RecommendationCandidateModel`  [INFERRED]
  ml/nlp-workbench-latest/src/stringsense_nlp/bert_review.py → backend/app/domain/recommendation/entities.py

## Import Cycles
- None detected.

## Communities (329 total, 67 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.07
Nodes (61): hasUnreadPlayerMessages(), AdminRecommendationRunsScreen(), getStringLabel(), RequestCodeForm, requestCodeSchema, ResetPasswordForm, resetPasswordSchema, hasUnreadAdminMessages() (+53 more)

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (73): JwtTokenService, get_settings(), Path, Settings, AuthTokenPayload, get_media_file(), Protocol, TokenService (+65 more)

### Community 2 - "Community 2"
Cohesion: 0.21
Nodes (22): get_deepseek_agent_client(), QueryAgentUseCase, _answer_content(), _completion(), FakeModelClient, FakeToolbox, _login_admin(), AgentToolResult (+14 more)

### Community 3 - "Community 3"
Cohesion: 0.05
Nodes (69): AdminInventoryDetailScreen(), AVAILABILITY_OPTIONS, buildCatalogPayload(), buildInventoryPayload(), buildLocalPatch(), buildOfficialPerformancePayload(), CATALOG_VISIBILITY_OPTIONS, CATEGORY_OPTIONS (+61 more)

### Community 4 - "Community 4"
Cohesion: 0.06
Nodes (70): AdminAgentScreen(), ConversationEntry, starterQuestions, writeActions, AdminBookingDetailScreen(), AdminUpdateFeed(), getAllowedNextStatuses(), getPriceStateLabel() (+62 more)

### Community 5 - "Community 5"
Cohesion: 0.10
Nodes (59): AdminChatDetailScreen(), AdminLayout(), AdminRecommendationRunDetailScreen(), getStringLabel(), AdminAnalyticsScreen(), AdminChatQueueContent(), AdminChatQueueScreen(), AuthLayout() (+51 more)

### Community 6 - "Community 6"
Cohesion: 0.04
Nodes (74): AdminFeedbackScreen(), formatFeedbackScope(), CATEGORIES, AdminRacketModelsScreen(), sortModels(), PRIMARY_ACTIONS, RacketModelSelectorProps, BackendBookingPhotoType (+66 more)

### Community 7 - "Community 7"
Cohesion: 0.09
Nodes (32): LoginForm, loginSchema, LoginScreen(), RegisterForm, registerSchema, RegisterScreen(), AuthShell(), AuthShellProps (+24 more)

### Community 8 - "Community 8"
Cohesion: 0.23
Nodes (20): _attacking_request(), _candidate(), _candidate_with_core_scores(), RecommendationCandidateModel, RecommendationRequestModel, StringItem, _score_custom_candidates(), _string_item() (+12 more)

### Community 9 - "Community 9"
Cohesion: 0.10
Nodes (53): RacketModelCatalog, booking_to_dto(), BookingOut, AdminRacketModelOut, CurrentUser, BaseModel, _active_check_in_token(), admin_add_booking_update() (+45 more)

### Community 10 - "Community 10"
Cohesion: 0.06
Nodes (56): advancedPreferencesForPayload(), buildBackendProfilePayload(), deriveAdvancedPreferences(), deriveCategory(), derivedElasticityPreference(), derivedStringMovementPreference(), derivedTensionRetentionPreference(), deriveGaugeBounds() (+48 more)

### Community 11 - "Community 11"
Cohesion: 0.07
Nodes (19): Booking, BookingStatusHistory, BookingUpdate, Base, _booking_string_name(), Booking, to_booking_record(), Page (+11 more)

### Community 12 - "Community 12"
Cohesion: 0.06
Nodes (39): _assert_legacy_catalog_rows_are_not_active(), _assert_no_foreign_key_references(), _assert_required_tables(), _drop_feedback_tags(), remove obsolete feedback tags and legacy catalog tables  Revision ID: 20260902_0, _table_names(), upgrade(), _alter_columns() (+31 more)

### Community 13 - "Community 13"
Cohesion: 0.06
Nodes (44): AdminSettingsScreen(), normalizeNotificationSettings(), normalizeStorePolicyText(), NOTIFICATION_CATEGORIES, SlotPicker(), SlotPickerProps, ChatBubbleProps, ConversationCardProps (+36 more)

### Community 14 - "Community 14"
Cohesion: 0.11
Nodes (41): BookingFeedback, Base, Racket, AdminFeedbackOut, CreateFeedbackPayload, CreateRacketModelPayload, CreateRacketPayload, FeedbackOut (+33 more)

### Community 15 - "Community 15"
Cohesion: 0.04
Nodes (27): DeepSeekAgentClient, Any, AppError, ForbiddenError, NotFoundError, Any, ServiceUnavailableError, TooManyRequestsError (+19 more)

### Community 16 - "Community 16"
Cohesion: 0.19
Nodes (41): BookingConversation, One reusable general-support thread per player.      Booking support remains in, SupportConversation, BookingConversationMessageOut, BookingConversationOut, BaseModel, SendConversationMessagePayload, close_admin_conversation() (+33 more)

### Community 17 - "Community 17"
Cohesion: 0.10
Nodes (35): AdminUserBookingOut, AdminUserDetailOut, AdminUserProfileOut, AdminUsersOverviewOut, AdminUserSummaryOut, AuthResponse, ChangePasswordRequest, ForgotPasswordRequest (+27 more)

### Community 18 - "Community 18"
Cohesion: 0.09
Nodes (36): AnalyticsSummary, analytics_summary_to_dto(), AnalyticsSummaryOut, AnalyticsWorkloadEntryOut, BookingSlotOut, business_hours_to_dto(), BusinessHoursDayPayload, CheckInLookupOut (+28 more)

### Community 19 - "Community 19"
Cohesion: 0.15
Nodes (39): default_training_config(), run_bert_preparation(), validate_bert_pseudo_dataset(), artifact_records(), assert_zero_leakage(), deterministic_split(), fingerprint_inputs(), fingerprint_protected_assets() (+31 more)

### Community 20 - "Community 20"
Cohesion: 0.14
Nodes (32): Payment, Base, WalletTransaction, generate_uuid(), AdminPaymentStatusPayload, BookingPaymentQuoteOut, PaymentOut, BaseModel (+24 more)

### Community 21 - "Community 21"
Cohesion: 0.13
Nodes (32): send_openwa_text(), Pbkdf2PasswordHasher, format_bert_model_input(), acceptance_sample(), aggregate_candidate_cells(), attach_predictions(), build_candidate_matrix(), build_current_comparison() (+24 more)

### Community 22 - "Community 22"
Cohesion: 0.16
Nodes (19): editFieldsFor(), RacketEditFields, RacketPassportDetailScreen(), NewRacketScreen(), RacketForm, RacketFormInput, racketSchema, RacketModelSelector() (+11 more)

### Community 23 - "Community 23"
Cohesion: 0.13
Nodes (34): annotation_columns(), annotation_schema(), annotation_template(), build_gold_dataset(), build_silver_assisted_draft(), _human_annotation_eligible(), label_column(), label_distribution() (+26 more)

### Community 24 - "Community 24"
Cohesion: 0.26
Nodes (12): FeedbackFeatureAggregate, FeedbackRow, _aggregate_feedback_buckets(), _aggregate_personal_history(), build_personal_history_snapshot(), canonical_racket_model_key(), _digest(), _eligible_feedback_values() (+4 more)

### Community 25 - "Community 25"
Cohesion: 0.13
Nodes (34): Reusable implementation behind the canonical StringSense NLP notebooks., build_aspect_lexicon(), build_label_datasets(), build_normalizer(), _classification(), classify_review_aspect(), _extract_tension(), _has_price_mention() (+26 more)

### Community 26 - "Community 26"
Cohesion: 0.11
Nodes (10): UserAccount, Protocol, UserRepository, PasswordHasher, Protocol, GetCurrentUserUseCase, LoginUseCase, RegisterUserUseCase (+2 more)

### Community 27 - "Community 27"
Cohesion: 0.06
Nodes (34): Active Scope, Agent Scope Simplification Plan, Decisions, Deferred Scope, Errors Encountered, Goal, Phase 10 — Authentication and player page-by-page acceptance, Phase 11 — Admin page-by-page acceptance (+26 more)

### Community 28 - "Community 28"
Cohesion: 0.18
Nodes (8): StringCatalogItem, Collection, Session, StringItem, StringOfficialPerformance, SqlAlchemyCatalogRepository, test_catalog_editor_rolls_back_every_section_after_validation_failure(), test_sqlalchemy_booking_repository_creates_history_entries()

### Community 29 - "Community 29"
Cohesion: 0.06
Nodes (33): Acceptance Criteria, Audit Evidence, Collaborative Filtering, Combining Feedback and CF, Completed is not positive satisfaction, Current System Evidence, Decision Summary, Decisions Applied to V11 (+25 more)

### Community 30 - "Community 30"
Cohesion: 0.20
Nodes (14): PrivacySettingsPayload, profile_to_dto(), ProfileOut, ProfilePayload, BaseModel, PlayerProfile, get_privacy_settings(), get_profile() (+6 more)

### Community 31 - "Community 31"
Cohesion: 0.05
Nodes (41): backgroundColor, foregroundImage, adaptiveIcon, edgeToEdgeEnabled, predictiveBackGestureEnabled, expo, android, icon (+33 more)

### Community 32 - "Community 32"
Cohesion: 0.09
Nodes (21): UserPreferenceMatrix, _float_or_none(), _matrix_by_source(), _profile_preference_vector(), CachedRecommendationRecord, FeedbackRow, RacketRecommendationContext, RecommendationCandidateModel (+13 more)

### Community 33 - "Community 33"
Cohesion: 0.18
Nodes (30): main(), parse_args(), Namespace, _build_candidates(), build_cell_stability(), build_evidence_status_delta(), build_fixed_profile_comparison(), build_followup_sample() (+22 more)

### Community 34 - "Community 34"
Cohesion: 0.15
Nodes (30): _apply_cf(), _apply_feedback(), _apply_personal_history(), _auxiliary_scores(), _build_feature_evidence(), _build_reasons(), clamp01(), _effective_item_features() (+22 more)

### Community 35 - "Community 35"
Cohesion: 0.38
Nodes (9): FeedbackFeatureList(), FeedbackFeatureListProps, FEATURE_ORDER, feedbackEvidenceLabel(), feedbackFeatureEntries(), formatFeedbackScore(), formatFeedbackWeight(), BackendFeedbackFeatureSummary (+1 more)

### Community 36 - "Community 36"
Cohesion: 0.14
Nodes (15): Base, RecommendationRun, RecommendationRunItem, to_recommendation_run(), to_recommendation_run_item(), _float(), _mapping(), Any (+7 more)

### Community 37 - "Community 37"
Cohesion: 0.16
Nodes (18): RecommendationMatrixEntryRecord, CatalogTagOut, inventory_movement_to_dto(), InventoryMovementOut, InventoryUpdatePayload, official_performance_to_dto(), OfficialPerformanceOut, OfficialPerformancePayload (+10 more)

### Community 38 - "Community 38"
Cohesion: 0.07
Nodes (29): Admin QR configuration, Admin review, Admin Settings, API Plan, Approval Gate, Definition of Done, Delivery Phases, Existing Foundation to Reuse (+21 more)

### Community 39 - "Community 39"
Cohesion: 0.18
Nodes (28): AspectScoreMap, approved_catalog_defaults(), approved_catalog_ids(), approved_row_to_values(), as_string(), build_sku(), catalog_source_path(), clamp01() (+20 more)

### Community 40 - "Community 40"
Cohesion: 0.14
Nodes (33): RecommendationFeatureDefinition, _build_catalog_lookup(), _build_evidence_note(), _build_matrix_entries(), CatalogLookupEntry, _cell_text(), _clean_text(), _column_index() (+25 more)

### Community 41 - "Community 41"
Cohesion: 0.06
Nodes (19): InventoryMovementRecord, page_to_dict(), Any, list_active_strings(), CatalogRepository, Protocol, StringItem, StringOfficialPerformance (+11 more)

### Community 42 - "Community 42"
Cohesion: 0.07
Nodes (29): Active Business Tables, `booking_conversations`, `booking_feedback`, `booking_status_history`, `booking_updates`, `bookings`, Catalog Normalization, `check_in_tokens` (+21 more)

### Community 43 - "Community 43"
Cohesion: 0.19
Nodes (26): main(), parse_args(), Namespace, execute_notebook(), execute_run(), main(), parse_args(), Namespace (+18 more)

### Community 45 - "Community 45"
Cohesion: 0.21
Nodes (4): Backend Docs Index, Current Guides, Scope, Plans, and Evidence, Workspace Docs Index

### Community 46 - "Community 46"
Cohesion: 0.28
Nodes (21): NotificationDelivery, AdminNotificationOut, admin_export_feedback(), admin_feedback(), admin_notifications(), admin_resend_notification(), admin_send_notification(), _deliver_notification() (+13 more)

### Community 47 - "Community 47"
Cohesion: 0.23
Nodes (6): AuthProvider, StrEnum, UserRole, FastPasswordHasher, FixedClock, datetime

### Community 48 - "Community 48"
Cohesion: 0.19
Nodes (21): RecommendationResultModel, ProfileRecommendationPayload, Any, BaseModel, datetime, recommendation_detail_to_dto(), recommendation_request_to_domain(), recommendation_response_to_dto() (+13 more)

### Community 49 - "Community 49"
Cohesion: 0.15
Nodes (16): _cache_payload_with_run_id(), _cached_price(), _cached_run_id(), _float_or_none(), _isoformat_or_none(), _profile_snapshot(), CachedRecommendationRecord, RacketRecommendationContext (+8 more)

### Community 50 - "Community 50"
Cohesion: 0.17
Nodes (12): Controlled residual boundaries, Decision, Finding disposition, Gate 5, P0 blockers, P1 findings, P2 findings, P3 findings (+4 more)

### Community 51 - "Community 51"
Cohesion: 0.14
Nodes (14): P1-10 — Legacy AI implementations are eagerly loaded at API startup, P1-11 — Current dependency baseline contains known vulnerabilities, P1-12 — Backend sessions are intentionally lost on app/browser restart, P1-13 — Most catalog prices are incomplete, P1-1 — Clean-environment demo credentials are not reproducible, P1-2 — Recommendation percentage is multiplied twice, P1-3 — Failed live slot loading silently switches to mock booking data, P1-4 — Booking mapper invents payment facts and mutable prices (+6 more)

### Community 52 - "Community 52"
Cohesion: 0.15
Nodes (25): build_bert_pseudo_dataset(), _canonical_name_index(), filter_bert_string_cohort(), DataFrame, _mappings(), DataFrame, Path, _silver() (+17 more)

### Community 53 - "Community 53"
Cohesion: 0.13
Nodes (11): PasswordResetCode, to_password_reset_code(), datetime, Session, SqlAlchemyPasswordResetRepository, PasswordResetCodeRecord, PasswordResetRepository, datetime (+3 more)

### Community 54 - "Community 54"
Cohesion: 0.11
Nodes (24): get_booking_repository(), get_catalog_repository(), get_current_admin(), get_current_customer(), get_current_user(), get_password_hasher(), get_password_reset_repository(), get_profile_repository() (+16 more)

### Community 55 - "Community 55"
Cohesion: 0.16
Nodes (20): booking_slot_datetime_utc(), booking_slot_id_for_datetime(), booking_slot_id_for_stored_datetime(), normalize_datetime(), normalize_store_input_datetime(), parse_booking_slot_id(), parse_hhmm(), BookingSlot (+12 more)

### Community 56 - "Community 56"
Cohesion: 0.08
Nodes (23): 1. Purpose, 2. Admin Inventory List, 3. Admin String Detail, 4. Unified Inventory Card Design, 5. Backend Field Mapping, 6. Admin Microcopy, 7. ASCII Wireframes, 8. Implementation Checklist (+15 more)

### Community 57 - "Community 57"
Cohesion: 0.15
Nodes (24): Brand, InventoryMovement, Base, RecommendationScoreCache, StringCatalogMetric, StringCatalogTag, StringInventoryItem, StringRecommendationMatrix (+16 more)

### Community 58 - "Community 58"
Cohesion: 0.07
Nodes (17): StoreBusinessHours, StoreSettings, StoreBusinessHoursRecord, StoreSettingsRecord, to_business_hours(), to_store_settings(), Session, SqlAlchemyStoreRepository (+9 more)

### Community 59 - "Community 59"
Cohesion: 0.09
Nodes (23): clsx, expo-camera, expo-constants, expo-device, expo-image-picker, @expo/metro-runtime, expo-secure-store, expo-status-bar (+15 more)

### Community 60 - "Community 60"
Cohesion: 0.09
Nodes (22): 10. Design Summary, 11. FYP2 Architecture Conformance (2026-08-30), 1. Scope, 2. End-to-End Runtime Flow, 3.1 User-side inputs, 3.2 Item-side inputs, 3.3 Feature mapping note, 3.4 Runtime learning signals (+14 more)

### Community 61 - "Community 61"
Cohesion: 0.15
Nodes (15): Any, ensure_racket_model_catalog_seeded(), ensure_seed_user(), ensure_seed_users(), ensure_store_defaults(), _import_startup_recommendation_matrix(), _load_store_seed(), Session (+7 more)

### Community 62 - "Community 62"
Cohesion: 0.10
Nodes (20): 12-by-9 Matrix Generation, Active cohort, Approved promotion record, BERT ABSA Review Optimization Design, Colab full run, Completed full-run evidence, Decision Summary, Done Criteria (+12 more)

### Community 63 - "Community 63"
Cohesion: 0.15
Nodes (16): StringOfficialPerformance, _collapsed_aspect_scores(), _normalize_availability_status(), _normalize_pricing_mode(), _normalized_name(), StringCatalogItem, to_official_performance(), to_recommendation_matrix_entry() (+8 more)

### Community 64 - "Community 64"
Cohesion: 0.21
Nodes (5): Profile, to_profile(), PlayerProfile, Session, SqlAlchemyProfileRepository

### Community 65 - "Community 65"
Cohesion: 0.26
Nodes (13): get_db(), commit_transaction_effects(), _get_effects(), Session, register_created_file(), register_removed_file(), rollback_transaction_effects(), TransactionEffects (+5 more)

### Community 66 - "Community 66"
Cohesion: 0.11
Nodes (19): Backend, Backend Config And Runtime, Backend Domains And Use Cases, Backend Layers, Backend Persistence And Migrations, Backend Route Files, Backend Tests, Common Change Recipes (+11 more)

### Community 67 - "Community 67"
Cohesion: 0.12
Nodes (22): FEATURE_LABELS, StringDetailScreen(), toAspectLabel(), toSentiment(), BrandGroup, CatalogListItem, DisplayMode, isBrandGroup() (+14 more)

### Community 68 - "Community 68"
Cohesion: 0.12
Nodes (19): SupportConversationMessage, AdminAgentToolbox, _masked_phone(), _optional_choice(), _optional_text(), BookingStatus, StrEnum, AgentToolResult (+11 more)

### Community 69 - "Community 69"
Cohesion: 0.12
Nodes (12): AnalyticsSummary, AnalyticsWorkloadEntry, BookedSlot, BookingSlot, BusinessHoursDay, CheckInLookup, PopularString, ServiceQueue (+4 more)

### Community 70 - "Community 70"
Cohesion: 0.26
Nodes (16): MarkNotificationsReadOut, MarkNotificationsReadPayload, notification_preferences_to_dto(), NotificationOut, NotificationPreferencesPayload, BaseModel, SendNotificationPayload, _derived_notification_events() (+8 more)

### Community 71 - "Community 71"
Cohesion: 0.07
Nodes (26): BOOKING_STEPS, BookingForm, BookingFormInput, bookingSchema, BookingStep, getSlotPeriod(), NewBookingScreen(), SLOT_PERIOD_OPTIONS (+18 more)

### Community 72 - "Community 72"
Cohesion: 0.28
Nodes (14): CheckInToken, NotificationRead, Base, _admin_token(), _headers(), notification_activity(), NotificationActivity, _register() (+6 more)

### Community 73 - "Community 73"
Cohesion: 0.15
Nodes (17): ContentRecommendationScorer, Rule-enhanced, content-based, and explainable scorer., FakeRecommendationRepository, test_cf_alone_changes_final_score_after_support_gate(), test_enabled_cf_can_change_ranking(), test_feedback_and_enabled_cf_are_bounded(), test_feedback_calibration_alone_changes_feature_and_final_score(), test_fixed_fusion_ignores_review_popularity_and_removed_metadata() (+9 more)

### Community 74 - "Community 74"
Cohesion: 0.22
Nodes (5): InventorySnapshot, RecommendationMatrixInspectionRecord, StringOfficialPerformance, StringTag, GetRecommendationMatrixUseCase

### Community 75 - "Community 75"
Cohesion: 0.21
Nodes (15): add_security_headers(), _feedback_followup_loop(), handle_app_error(), handle_http_exception(), handle_integrity_error(), handle_validation_error(), lifespan(), JSONResponse (+7 more)

### Community 76 - "Community 76"
Cohesion: 0.18
Nodes (11): Architecture assessment, Candidate A — Booking Integrity Module, Candidate B — Mobile Data Boundary, Candidate C — Catalog and Inventory Aggregate, Candidate D — Recommendation Runtime Module, Candidate E — NLP Experiment Boundary, Candidate F — Runtime and delivery foundation, Constraint (+3 more)

### Community 77 - "Community 77"
Cohesion: 0.12
Nodes (16): Acceptance Criteria, Admin Experience, Cache Policy, Current Capability Status, Decisions Applied to V11, Deferred or Partial Work, Document Status, Explicit Non-Goals (+8 more)

### Community 78 - "Community 78"
Cohesion: 0.28
Nodes (9): AgentToolbox, _optional_number(), _optional_string(), AgentToolResult, _required_string(), _source(), _string_list(), _version() (+1 more)

### Community 79 - "Community 79"
Cohesion: 0.12
Nodes (16): Account Security and Privacy, API Contract, Auth, Bookings, Grounded Player And Admin Agent, Health, Human Support Conversations, Notifications (+8 more)

### Community 80 - "Community 80"
Cohesion: 0.12
Nodes (15): Agent comparison and validation (2026-08-24), Agent Scope Findings, Authentication Pages, Cash payment option (2026-08-18), Current page-review conclusion, Final FYP2 Classification, Follow-up fix evidence — 2026-08-17, Full Page Review (2026-08-17) (+7 more)

### Community 81 - "Community 81"
Cohesion: 0.10
Nodes (16): advancedPreferenceKeys, preferredFeelOptions, preferredGaugeOptions, priorityKeys, ProfileEditScreen(), ProfileForm, ProfileFormInput, profileSchema (+8 more)

### Community 82 - "Community 82"
Cohesion: 0.13
Nodes (15): Active Runtime, AI Boundary, Authentication Abuse Boundary, Backend Architecture, Bounded Contexts, Catalog Boundary, Commerce Flow, Folder Map (+7 more)

### Community 83 - "Community 83"
Cohesion: 0.13
Nodes (15): Backend, Documentation and governance state, Gate 0 decision, Mobile, NLP artifact handoff, Postgres, Protected inputs and data state, Purpose and gate (+7 more)

### Community 84 - "Community 84"
Cohesion: 0.25
Nodes (14): _confusion_matrix(), _limit_splits(), main(), _metrics(), parse_args(), Any, DataFrame, Namespace (+6 more)

### Community 85 - "Community 85"
Cohesion: 0.13
Nodes (14): AGENTS.md - mobile, Architecture Map, Canonical Commands, Change Rules, Critical Paths, Definition of Done, High-Risk Changes (Ask Before Proceeding), Maintenance Rule (+6 more)

### Community 86 - "Community 86"
Cohesion: 0.22
Nodes (16): AdminBusinessHoursScreen(), clampClosedDay(), closedDayOptions(), closedMonthOptions(), CURRENT_YEAR, daysInMonth(), formatClosedDate(), minimumClosedDay() (+8 more)

### Community 87 - "Community 87"
Cohesion: 0.36
Nodes (11): BookingStatusHistoryEntry, BookingUpdateEntry, booking_history_to_dto(), booking_update_to_dto(), BookingStatusHistoryOut, BookingUpdateOut, CancelBookingPayload, CheckInTokenOut (+3 more)

### Community 88 - "Community 88"
Cohesion: 0.12
Nodes (10): CachedRecommendationRecord, PersonalHistoryAggregate, PersonalHistorySnapshot, RacketRecommendationContext, RecommendationCandidateModel, RecommendationDetailModel, RecommendationFeatureSignalModel, UserPreferenceVectorEntry (+2 more)

### Community 89 - "Community 89"
Cohesion: 0.53
Nodes (13): complete_booking(), create_booking(), create_racket(), first_string_id(), headers(), login_admin(), register_customer(), test_admin_manages_the_racket_models_available_to_players() (+5 more)

### Community 90 - "Community 90"
Cohesion: 0.23
Nodes (11): AdminUsersScreen(), joinedLabel(), orderStatusVariant(), profileValue(), requestErrorMessage(), roleLabel(), UserDetailModal(), UserRow() (+3 more)

### Community 91 - "Community 91"
Cohesion: 0.29
Nodes (13): calendarDayNumber(), formatClockTime(), formatRelativeBookingDate(), getBookingPaymentLabel(), getBookingPriceLabel(), getNextBookingStep(), getNextOpenLabel(), getStoreHoursLabel() (+5 more)

### Community 92 - "Community 92"
Cohesion: 0.14
Nodes (13): engines, node, main, name, private, scripts, android, ios (+5 more)

### Community 93 - "Community 93"
Cohesion: 0.26
Nodes (10): AgentActionDto, AgentContextDto, AgentGeneratedAnswerDto, AgentHandoffDto, AgentMessageDto, AgentQueryDto, AgentResponseDto, AgentSourceDto (+2 more)

### Community 94 - "Community 94"
Cohesion: 0.15
Nodes (12): Administrator pages, Authentication pages, Automated validation, Cross-role and security checks, Follow-up fixes — 2026-08-17, Initial functional defects — repaired, Lower-severity findings, Player pages (+4 more)

### Community 95 - "Community 95"
Cohesion: 0.15
Nodes (13): Backend, Coverage conclusion, Coverage definition, Explicitly not executed, Mobile and Node, Negative and integrity probes, NLP validation executed, Purpose (+5 more)

### Community 96 - "Community 96"
Cohesion: 0.15
Nodes (13): 1. Start Postgres, 2. Start the backend, 3. Start the mobile app in a browser, 4. Start the mobile app on Expo Go, 5. Run the NLP workbench when you need fresh recommendation artifacts, Backend and NLP Integration, Current Delivery Boundary, Documentation Map (+5 more)

### Community 97 - "Community 97"
Cohesion: 0.17
Nodes (15): AgentActionDto, _action_is_verified(), AgentModelClient, _collect_named_ids(), _completion_message(), _empty_verified_ids(), _parse_tool_call(), _provider_user_id() (+7 more)

### Community 98 - "Community 98"
Cohesion: 0.17
Nodes (12): Administrator Browser Coverage, Cross-Role Persistence Proof, Customer and Administrator Acceptance Record, Customer Browser Coverage, Deliberate External Boundaries, External payments, Final Classification, Page Inventory (+4 more)

### Community 99 - "Community 99"
Cohesion: 0.17
Nodes (11): Accessibility, Buttons, Cards And Elevation, Color Palette, Components, Design System Inspiration of Apple, Implementation Notes, Layout (+3 more)

### Community 100 - "Community 100"
Cohesion: 0.18
Nodes (11): babel-preset-expo, eslint, eslint-config-expo, devDependencies, babel-preset-expo, eslint, eslint-config-expo, @types/react (+3 more)

### Community 101 - "Community 101"
Cohesion: 0.22
Nodes (9): DETAIL_API_KEYS, DETAIL_RATINGS, DetailRatingKey, emptyDetailRatings(), FeedbackScreen(), RATING_VALUES, mapBackendFeedbackToBookingFeedback(), BackendUpdateFeedbackPayload (+1 more)

### Community 102 - "Community 102"
Cohesion: 0.20
Nodes (10): AGENTS.md - StringSence, Architecture Map, Change Rules, Definition of Done, Graphify Workflow, High-Risk Changes (Ask Before Proceeding), Project Context, Quick Start (+2 more)

### Community 103 - "Community 103"
Cohesion: 0.20
Nodes (9): AGENTS.md - backend, Architecture Map, Change Rules, Definition of Done, High-Risk Changes (Ask Before Proceeding), Project Context, Quick Start, Scope (+1 more)

### Community 104 - "Community 104"
Cohesion: 0.20
Nodes (8): check_database_connection(), Session, health_payload(), Session, api_health(), Session, Session, root_health()

### Community 105 - "Community 105"
Cohesion: 0.31
Nodes (8): _backend_root(), _catalog_payload(), _gauge_score(), _normalize_name(), Path, normalize string catalog  Revision ID: 20260412_0008 Revises: 20260411_0007 Crea, _slug(), upgrade()

### Community 106 - "Community 106"
Cohesion: 0.31
Nodes (8): _candidate_category(), _headers(), _login_admin(), RecommendationCandidateModel, _register_customer(), test_catalog_inventory_and_recommendations_only_expose_the_twelve_strings(), test_feel_and_gauge_preferences_raise_matching_candidate_scores(), test_seed_contains_only_approved_strings()

### Community 107 - "Community 107"
Cohesion: 0.20
Nodes (10): Acceptance Database Boundary, Audit Result, Definition, Deliberate External Boundary, Mock Page Remediation, Page Entry Points, Payment Boundary, Resolved Pages (+2 more)

### Community 108 - "Community 108"
Cohesion: 0.18
Nodes (10): BERT pseudo-label baseline, Dataset summary, Environment, Frozen-model offline inference, Full training on Colab, Immutable boundary, NLP-01 data foundation, NLP Workbench Latest — Canonical Experiment Root (+2 more)

### Community 109 - "Community 109"
Cohesion: 0.20
Nodes (10): 12. Styling and Theming, 14. Screen Composition Pattern, 15. Current Architectural Strengths, 16. Current Architectural Constraints, 17. Recommended Evolution Path, 19. Summary, 1. Overview, 3. System Shape (+2 more)

### Community 110 - "Community 110"
Cohesion: 0.20
Nodes (10): 18. Directory Guide, `app/`, `components/*`, `components/shared/`, `components/ui/`, `lib/`, `services/`, `store/` (+2 more)

### Community 111 - "Community 111"
Cohesion: 0.22
Nodes (8): Algorithm Version, Appendix D: Recommendation Algorithm, Core Recommendation Dimensions, Explainability Output, Important FYP1 Claim Boundary, Input Features, Persistence Boundary, Score Layers

### Community 112 - "Community 112"
Cohesion: 0.22
Nodes (8): Appendix E: Key Source Code Extracts, Backend Application, Booking Status Transition Policy, Mobile Application, Mobile Recommendation Trigger, Notes, Recommendation Score Weights, Suggested Code Extracts for Report

### Community 113 - "Community 113"
Cohesion: 0.22
Nodes (9): Active Structure, API Contract, Catalog Refactor Notes, Environment, Local Postgres, Recommendation Refactor Notes, Run, StringSense Backend (+1 more)

### Community 114 - "Community 114"
Cohesion: 0.64
Nodes (8): _create_booking(), _headers(), _login_admin(), _register_customer(), test_booking_conversation_lifecycle_and_thread_dto(), test_conversation_message_length_validation_and_closed_guard(), test_conversation_routes_enforce_booking_ownership_and_admin_role(), test_general_support_is_available_without_a_booking_and_reuses_thread()

### Community 115 - "Community 115"
Cohesion: 0.22
Nodes (8): Hierarchy, Layout, Modern mobile expression, Motion, Platform behavior, Product direction, StringSense interface system, Visual system

### Community 116 - "Community 116"
Cohesion: 0.22
Nodes (8): Admin, Backend, FYP1 Demo Proof, FYP1 Included, Outside The FYP1 Proof, Player, Recommendation Positioning, StringSense FYP1 Scope

### Community 117 - "Community 117"
Cohesion: 0.22
Nodes (8): Accessibility & Inclusion, Anti-references, Brand Personality, Design Principles, Product, Product Purpose, Register, Users

### Community 118 - "Community 118"
Cohesion: 0.39
Nodes (6): APIRoute, _get_db_dependants(), _iter_api_routes(), _iter_dependants(), test_all_get_db_dependencies_are_function_scoped_and_cached(), Dependant

### Community 119 - "Community 119"
Cohesion: 0.39
Nodes (7): _iso(), _item_payload(), main(), datetime, Path, StringItem, _sha256()

### Community 120 - "Community 120"
Cohesion: 0.54
Nodes (7): headers(), login_admin(), register_player(), register_player_with_id(), test_admin_can_search_and_open_user_detail(), test_admin_user_overview_returns_real_counts_and_safe_fields(), test_player_cannot_access_admin_user_overview()

### Community 121 - "Community 121"
Cohesion: 0.54
Nodes (7): _headers(), _login_admin(), _register(), test_check_in_rolls_back_consumed_token_when_booking_write_fails(), test_password_reset_rolls_back_password_when_code_write_fails(), test_profile_rolls_back_when_preference_vector_write_fails(), test_recommendation_rolls_back_cache_when_run_write_fails()

### Community 122 - "Community 122"
Cohesion: 0.25
Nodes (7): Active Backend Boundary, Active Scope, Configuration, Deferred But Preserved, FYP-Scoped Player And Admin Agent, Re-Enabling Deferred Capabilities, Safety Rules That Remain Active

### Community 123 - "Community 123"
Cohesion: 0.25
Nodes (7): Allowed labels, Annotation unit, Blind workflow, Decision rules, Examples, Purpose, StringSense Gold Annotation Guideline v1

### Community 124 - "Community 124"
Cohesion: 0.29
Nodes (6): Path, test_protected_asset_snapshot_does_not_open_source_archive(), test_review_frame_reads_raw_price_and_treats_zero_as_missing(), test_run_id_rejects_unsafe_paths(), test_stage_directory_is_create_once(), MonkeyPatch

### Community 125 - "Community 125"
Cohesion: 0.22
Nodes (10): ConversationEntry, starterQuestions, compactSentence(), formatExperienceScope(), formatPercent(), formatRating(), humanizeFeature(), RecommendationExplanationScreen() (+2 more)

### Community 126 - "Appendix D: Recommendation Algorithm"
Cohesion: 0.25
Nodes (8): 13. Unified Header System, Back button rules, Header types, Height and spacing guidance, Page mapping, Right-side action rules, Typography hierarchy, Visual direction

### Community 127 - "Community 127"
Cohesion: 0.25
Nodes (8): Architecture Decisions, Features, Getting Started, Project Structure, StringSense Mobile App, Styling Runtime, Tech Stack, Validation

### Community 128 - "Community 128"
Cohesion: 0.25
Nodes (7): compilerOptions, strict, exclude, extends, **/._*, dist, expo/tsconfig.base

### Community 129 - "Community 129"
Cohesion: 0.29
Nodes (6): Appendix G: NLP and Recommendation Artifacts, Backend Integration, Current BERT Boundary, Feedback Linkage, Main Artifacts, Suggested Appendix Use

### Community 130 - "Community 130"
Cohesion: 0.43
Nodes (5): get_clock(), FixedClock, datetime, test_analytics_uses_persisted_payments_and_store_local_day(), SystemClock

### Community 131 - "Community 131"
Cohesion: 0.17
Nodes (12): GenerateRecommendationUseCase, FakeProfileRepository, FakeRecommendationRunRepository, FeedbackRow, test_cached_recommendation_detail_returns_rationale(), test_execute_profile_persists_true_profile_snapshot(), test_personal_history_changes_invalidate_cached_results(), test_preview_does_not_persist_and_profile_persists_preference_vector_and_cache() (+4 more)

### Community 132 - "Community 132"
Cohesion: 0.29
Nodes (7): API Layer, Business Logic, Clean Architecture Migration Map, ORM and Repositories, Runtime Entry, Security and Recommendation, Shared / Config

### Community 133 - "Community 133"
Cohesion: 0.48
Nodes (5): _ensure_column(), _ensure_index(), upgrade(), Column, Inspector

### Community 134 - "Community 134"
Cohesion: 0.38
Nodes (5): _json_insert(), Any, _seed_values(), upgrade(), TextClause

### Community 135 - "Community 135"
Cohesion: 0.48
Nodes (6): _backfill_feedback_seed(), _catalog_seed(), downgrade(), rename legacy catalog terminology to feedback  Revision ID: 20260831_0038 Revise, _rename_metric_column(), upgrade()

### Community 136 - "Community 136"
Cohesion: 0.14
Nodes (12): 1. Create deployment secrets, 2. Build and start without Cloudflare, 3. Connect Cloudflare Tunnel, 4. Operate safely, StringSence Docker Deployment, Automated verification, Hardening delivered, Operator handoff (+4 more)

### Community 137 - "Community 137"
Cohesion: 0.29
Nodes (6): Backend Evidence, Implemented, Mobile Evidence, QR Payment and Proof Acceptance — 2026-08-18, Security Boundaries Verified, Unverified

### Community 138 - "Community 138"
Cohesion: 0.21
Nodes (8): Base, User, UserAccount, to_user_account(), Session, SqlAlchemyUserRepository, hash_check_in_token(), test_concurrent_reset_and_check_in_requests_keep_one_active_token()

### Community 139 - "Community 139"
Cohesion: 0.29
Nodes (7): 11. Feature Module Breakdown, Admin Operations, Authentication, Booking, Booking Support Chat, Profile And Player Retention Modules, Recommendation and catalog

### Community 140 - "Community 140"
Cohesion: 0.29
Nodes (7): 5. Routing and Access Control, `app/admin`, `app/auth`, `app/player`, Guard model, Root routing, Route groups

### Community 141 - "Community 141"
Cohesion: 0.29
Nodes (7): overrides, brace-expansion@1.1.16, brace-expansion@5.0.7, js-yaml@3.15.0, js-yaml@4.3.0, postcss, uuid

### Community 142 - "Community 142"
Cohesion: 0.53
Nodes (4): _backfill_inventory_status_columns(), _drop_named_legacy_booking_fk(), _rebuild_sqlite_bookings_without_legacy_fk(), upgrade()

### Community 143 - "Community 143"
Cohesion: 0.60
Nodes (5): downgrade(), Any, _row_params(), _seed_values(), upgrade()

### Community 144 - "Community 144"
Cohesion: 0.73
Nodes (5): _headers(), _register(), test_admin_payment_qr_can_be_replaced_deleted_and_downloaded(), test_booking_payment_quote_is_owned_and_uses_active_ledger_amount(), test_cash_booking_payment_and_top_up_wait_for_admin_confirmation()

### Community 146 - "Community 146"
Cohesion: 0.33
Nodes (5): Full Disaster Recovery, Recovery Evidence, Restore One Archived String, Result, Runtime Catalog Archive — 2026-08-18

### Community 147 - "Community 147"
Cohesion: 0.33
Nodes (6): Confidence and influence, Eligibility and Aggregation, Eligible records, Normalization, Preventing frequent-user dominance, Zero-feedback invariant

### Community 149 - "Community 149"
Cohesion: 0.26
Nodes (12): formatDropOffDateTime(), formatTrackingDateTime(), getCurrentStageKey(), getHeroStatusChipClasses(), getHeroStatusLabel(), getLatestUpdate(), getNextStepLabel(), getQuoteStatus() (+4 more)

### Community 150 - "Community 150"
Cohesion: 0.33
Nodes (5): 2026-08-17, 2026-08-17 follow-up fixes, 2026-08-18, 2026-08-24, Agent Scope Simplification Progress

### Community 151 - "Community 151"
Cohesion: 0.40
Nodes (4): Admin Endpoints, Appendix B: Backend API Endpoint Summary, Notes for Report, Public and Player Endpoints

### Community 152 - "Community 152"
Cohesion: 0.40
Nodes (4): Appendix C: Database Schema Summary, Important Design Boundaries, Main Tables, Suggested ERD Grouping

### Community 153 - "Community 153"
Cohesion: 0.40
Nodes (4): Appendix F: Testing Evidence, Recommended Test Evidence Table, Report Notes, Suggested Validation Commands

### Community 154 - "Community 154"
Cohesion: 0.60
Nodes (4): _alter_feedback_table(), downgrade(), remove durability from player feedback  Revision ID: 20260825_0033 Revises: 2026, upgrade()

### Community 155 - "Community 155"
Cohesion: 0.18
Nodes (8): RecommendationResponseModel, Any, Page, Protocol, RecommendationRunRepository, test_latest_recommendation_tool_returns_backend_run_source(), test_out_of_stock_tool_returns_only_similar_in_budget_candidates(), test_what_if_tool_maps_changes_without_mutating_saved_profile()

### Community 156 - "Community 156"
Cohesion: 0.40
Nodes (4): Design QA — Player tools hub, Findings and iteration history, Interaction checks, Visual comparison

### Community 157 - "Community 157"
Cohesion: 0.40
Nodes (5): Current feedback path, Current System Evidence, Feedback collection corrections implemented, Migration alignment implemented, Runtime path

### Community 158 - "Community 158"
Cohesion: 0.40
Nodes (5): Implementation Record, Phase 1: Correct feedback collection — completed, Phase 2: Build and inspect feedback aggregates — completed, Phase 3: Enable feedback calibration and V11 CF — completed, Phase 4: Player and admin feedback presentation — completed

### Community 159 - "Community 159"
Cohesion: 0.17
Nodes (12): Gate 1 decision, Node decision, P0-1 — Empty-database migration fails at revision 0008, P0-2 — Booking creation bypasses slot capacity and scheduling policy, P0-3 — Canonical NLP evidence is not executable or evaluation-safe, P0 blockers, P2 medium-severity findings, P3 hygiene and evidence findings (+4 more)

### Community 160 - "Community 160"
Cohesion: 0.40
Nodes (5): 2. Technology Stack, Core framework, Forms and validation, State and data, UI and styling

### Community 161 - "Community 161"
Cohesion: 0.40
Nodes (5): 6. State Architecture, Derived accessors, Runtime and Bundling Constraints, Store actions, Store contents

### Community 162 - "Community 162"
Cohesion: 0.40
Nodes (4): config, { getDefaultConfig }, path, { withUniwindConfig }

### Community 164 - "Community 164"
Cohesion: 0.26
Nodes (11): buildTrackingSteps(), formatTrackingDateTime(), getStageBadge(), NODE_STYLES, TimelineStep, TimelineStepDefinition, TimelineVisualState, TRACKING_SEQUENCE (+3 more)

### Community 165 - "Community 165"
Cohesion: 0.24
Nodes (6): validate_status_transition(), validate_terminal_status_note(), datetime, UpdateBookingStatusUseCase, test_booking_status_transition_accepts_valid_progression(), test_booking_status_transition_rejects_invalid_progression()

### Community 166 - "Community 166"
Cohesion: 0.35
Nodes (10): build_feedback_snapshot(), cf_weight_for_support(), _feedback(), test_cf_weight_requires_three_distinct_supporting_users_and_is_bounded(), test_custom_racket_feedback_uses_global_scope(), test_feedback_snapshot_version_does_not_depend_on_query_order(), test_feedback_source_version_changes_when_rating_changes(), test_feedback_uses_exact_context_then_global_and_averages_each_user() (+2 more)

### Community 167 - "Community 167"
Cohesion: 0.22
Nodes (5): ProfileRepository, PlayerProfile, Protocol, GetMyProfileUseCase, PlayerProfile

### Community 168 - "Community 168"
Cohesion: 0.22
Nodes (6): PlayerTool, PlayerToolGroup, playerToolGroups, PlayerToolsSheet(), PlayerToolsSheetProps, styles

### Community 169 - "Community 169"
Cohesion: 0.83
Nodes (3): _column_exists(), downgrade(), upgrade()

### Community 170 - "Community 170"
Cohesion: 0.83
Nodes (3): _column_exists(), downgrade(), upgrade()

### Community 171 - "Community 171"
Cohesion: 0.83
Nodes (3): _headers(), _login_admin(), test_player_admin_operational_flow()

### Community 172 - "Community 172"
Cohesion: 0.50
Nodes (4): Algorithm version, Candidate loading, Recommendation Integration, Scoring order

### Community 173 - "Community 173"
Cohesion: 0.50
Nodes (4): API Contract, Create feedback, Feedback summary, Update feedback

### Community 174 - "Community 174"
Cohesion: 0.50
Nodes (4): Backend unit and integration tests, Mobile tests, Required validation commands, Test Plan

### Community 175 - "Community 175"
Cohesion: 0.50
Nodes (4): Durability flow, Feedback Form Design, Field semantics, Interaction rules

### Community 176 - "Community 176"
Cohesion: 0.67
Nodes (3): main(), parse_args(), Namespace

### Community 177 - "Community 177"
Cohesion: 0.28
Nodes (9): AdminInventoryStringOut, admin_inventory_string_detail(), admin_update_inventory_string(), admin_update_string_editor(), inventory_update_values(), _prepare_string_values(), InventoryUpdatePayload, PrepareStringValuesUseCase (+1 more)

### Community 178 - "Community 178"
Cohesion: 0.31
Nodes (8): CollaborativeEvidence, RecommendationInteraction, build_cf_evidence(), _cosine_similarity(), _empty_cf(), _interaction(), test_cf_evidence_requires_exact_model_peer(), test_cf_keeps_missing_tension_peers_in_denominator_without_support()

### Community 179 - "Community 179"
Cohesion: 0.25
Nodes (7): AgentQueryDto, AgentResponseDto, Session, query_agent(), test_deepseek_client_retries_empty_json_content_once(), test_deepseek_client_uses_official_model_and_chat_completion_endpoint(), DeepSeekAgentClient

### Community 180 - "Community 180"
Cohesion: 0.50
Nodes (4): 8. Domain Model, Important enums and unions, Inventory modeling note, Main entities

### Community 181 - "Community 181"
Cohesion: 0.50
Nodes (4): 9.1 HeroUI wrapper layer, 9.2 App primitives, 9.3 Shared layout shell, 9. UI System

### Community 182 - "Community 182"
Cohesion: 0.25
Nodes (4): Path, RecommendationMatrixImportReport, Path, ImportRecommendationMatrixUseCase

### Community 183 - "Community 183"
Cohesion: 0.50
Nodes (3): NOTE: This file is generated by uniwind and it should not be edited manually., uniwind, UniwindConfig

### Community 215 - "expo-constants"
Cohesion: 0.67
Nodes (3): Database Design, Existing table remains authoritative, Required indexes

### Community 216 - "expo-linking"
Cohesion: 0.67
Nodes (3): Feedback screen, Player Experience, String catalog presentation

### Community 217 - "expo-splash-screen"
Cohesion: 0.67
Nodes (3): Feedback source version, Recommendation rationale, Versioning and Audit Evidence

### Community 219 - "react-native"
Cohesion: 0.67
Nodes (3): 10. Navigation UX Structure, Admin Information Architecture, Player information architecture

### Community 220 - "react-native-gesture-handler"
Cohesion: 0.67
Nodes (3): 7.1 Mutable runtime state: `store/appStore.ts`, 7.2 Unified backend bridge, 7. Data Layer Model

### Community 305 - "expo"
Cohesion: 0.36
Nodes (7): inventory_availability(), StringItem, AdminInventoryStringOut, inventory_string_to_dto(), StringItem, string_to_dto(), StringOut

### Community 312 - ".replace_score_cache"
Cohesion: 0.25
Nodes (5): _optional_float(), CachedRecommendationRecord, _required_float(), _required_int(), _required_mapping()

### Community 314 - "Local Development Flow"
Cohesion: 0.29
Nodes (6): 1. Prepare Environment, 2. Start the Unified Backend, 3. Validation Commands, 4. Catalog and Recommendation Notes, 5. Commerce Boundary, Local Development Flow

### Community 315 - "entities.py"
Cohesion: 0.47
Nodes (5): GameType, PlayerProfile, PlayingStyle, StrEnum, SkillLevel

### Community 316 - "UpsertMyProfileUseCase"
Cohesion: 0.47
Nodes (4): RecommendationRequestModel, _is_complete(), PlayerProfile, UpsertMyProfileUseCase

### Community 317 - "Administrator Acceptance Record"
Cohesion: 0.33
Nodes (6): Acceptance Data and Restoration, Administrator Acceptance Record, Browser Coverage, External Payment Boundary, Repository Quality Gates, Result

### Community 318 - "Proposed approval gates"
Cohesion: 0.33
Nodes (6): Gate 1 — Review and candidate selection (current stop), Gate 2 — Candidate design approval, Gate 3 — Per-candidate implementation, Gate 4 — Complete regression, Gate 5 — FYP2 readiness decision, Proposed approval gates

### Community 319 - "feedback_snapshot_to_dict"
Cohesion: 0.40
Nodes (4): FeedbackSnapshot, feedback_snapshot_to_dict(), get_admin_feedback_summary(), get_feedback_summary()

### Community 320 - "BookingUpdates.tsx"
Cohesion: 0.60
Nodes (4): BookingUpdates(), BookingUpdatesProps, formatUpdateDate(), BookingUpdate

## Knowledge Gaps
- **881 isolated node(s):** `Scope`, `Project Context`, `Validation Commands`, `Architecture Map`, `Change Rules` (+876 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **67 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `to_string_item()` connect `Community 63` to `Community 3`, `Community 28`?**
  _High betweenness centrality (0.188) - this node is a cross-community bridge._
- **Why does `StringItem` connect `Community 3` to `Community 0`, `Community 67`, `Community 5`, `Community 10`, `Community 13`, `Community 63`?**
  _High betweenness centrality (0.185) - this node is a cross-community bridge._
- **Why does `CurrentUser` connect `Community 9` to `Community 138`, `Community 11`, `Community 14`, `Community 16`, `Community 17`, `Community 18`, `Community 20`, `Community 30`, `Community 36`, `Community 46`, `Community 47`, `Community 48`, `Community 177`, `Community 179`, `Community 54`, `Community 184`, `feedback_snapshot_to_dict`, `Community 68`, `Community 70`?**
  _High betweenness centrality (0.102) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `CurrentUser` (e.g. with `SqlAlchemyBookingRepository` and `SqlAlchemyRecommendationRunRepository`) actually correct?**
  _`CurrentUser` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Scope`, `Project Context`, `Validation Commands` to the rest of the system?**
  _881 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.07317933345089049 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.053289473684210525 - nodes in this community are weakly interconnected._