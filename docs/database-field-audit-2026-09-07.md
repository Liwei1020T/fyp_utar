# Database field audit - 2026-09-07

## Scope and result

- Target: running main stringsense PostgreSQL database at 127.0.0.1:55432, container stringsense-postgres, PostgreSQL 16.15.
- Baseline captured before this patch: Alembic 20260902_0045, 32 application tables, 327 application columns, plus alembic_version.
- Every baseline application column is listed exactly once below. Counts are exact row/population counts only; no stored personal values are included.
- Repository ORM metadata and the retained live database now contain 324 columns. Revisions 20260907_0046 and 20260907_0047 removed the three baseline storage columns after backup and isolated PostgreSQL rehearsal.
- Exact deletion set: inventory_items.sku, users.auth_provider, users.external_auth_id.
- No table deletion, Agent write-tool change, frontend/BERT rebuild, or non-approved live DDL was performed. Only the reviewed three-column migration was applied.

## Evidence rules

- R/W evidence is grouped by table because the application maps ORM rows through explicit domain/DTO constructors rather than serializing ORM objects generically. Each column row points to the table surface code below.
- H means immutable historical migration evidence. C lists live database constraints/indexes. The live populated count is shown as populated/rows.
- A null field, empty table, or no frontend use is not sufficient for removal. Only the three reviewed storage fields are selected; all other fields are retained.

## Live row counts

booking_conversations=4 | booking_feedback=362 | booking_status_history=400 | booking_updates=17 | bookings=373 | brands=6 | check_in_tokens=10 | inventory_items=12 | inventory_movements=16 | notification_reads=18 | notifications=10 | password_reset_codes=4 | payments=0 | profiles=94 | racket_model_catalog=6 | rackets=78 | recommendation_feature_definitions=26 | recommendation_run_items=152 | recommendation_runs=44 | recommendation_score_cache=0 | store_business_hours=1 | store_settings=1 | string_catalog_metrics=12 | string_catalog_tags=48 | string_official_performance=12 | string_recommendation_matrix=264 | strings=12 | support_conversation_messages=2 | support_conversations=2 | user_preference_matrix=192 | users=100 | wallet_transactions=0.

## Grouped reader/writer surfaces

| table/key | ORM source | readers | writers | semantic boundary |
| --- | --- | --- | --- | --- |
| booking_conversations [BC] | backend/app/adapters/persistence/sqlalchemy/models/booking_conversation.py | backend/app/entrypoints/api/routes/booking_conversation_routes.py; backend/app/entrypoints/api/routes/notification_routes.py | backend/app/entrypoints/api/routes/booking_conversation_routes.py | booking-linked support state |
| booking_feedback [F] | backend/app/adapters/persistence/sqlalchemy/models/racket_feedback.py | backend/app/entrypoints/api/routes/racket_feedback_routes.py; backend/app/entrypoints/api/routes/admin_engagement_routes.py; backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_recommendation_repository.py | backend/app/entrypoints/api/routes/racket_feedback_routes.py; backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_recommendation_repository.py | completed-booking feedback |
| booking_status_history [BH] | backend/app/adapters/persistence/sqlalchemy/models/booking.py | backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_booking_repository.py; backend/app/entrypoints/api/routes/admin_routes.py; backend/app/entrypoints/api/routes/notification_routes.py | backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_booking_repository.py | audit history |
| booking_updates [BU] | backend/app/adapters/persistence/sqlalchemy/models/booking.py | backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_booking_repository.py; backend/app/entrypoints/api/routes/booking_routes.py; backend/app/entrypoints/api/routes/booking_conversation_routes.py; backend/app/entrypoints/api/routes/notification_routes.py | backend/app/use_cases/booking/add_booking_update.py; backend/app/entrypoints/api/routes/booking_routes.py; backend/app/entrypoints/api/routes/admin_routes.py | service/conversation activity |
| bookings [B] | backend/app/adapters/persistence/sqlalchemy/models/booking.py | backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_booking_repository.py; backend/app/entrypoints/api/routes/booking_routes.py; backend/app/entrypoints/api/routes/admin_routes.py; backend/app/entrypoints/api/routes/commerce_routes.py; backend/app/entrypoints/api/routes/notification_routes.py; backend/app/use_cases/agent/tools.py | backend/app/use_cases/booking/create_booking.py; backend/app/use_cases/booking/update_booking_status.py; backend/app/entrypoints/api/routes/admin_routes.py; backend/app/entrypoints/api/routes/commerce_routes.py | booking lifecycle |
| brands [BR] | backend/app/adapters/persistence/sqlalchemy/models/string_catalog_item.py | backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_catalog_repository.py; backend/app/adapters/persistence/sqlalchemy/catalog_seed.py | backend/app/adapters/persistence/sqlalchemy/catalog_seed.py; backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_catalog_repository.py | catalog brand master |
| check_in_tokens [CI] | backend/app/adapters/persistence/sqlalchemy/models/notification.py | backend/app/entrypoints/api/routes/booking_routes.py; backend/app/entrypoints/api/routes/admin_routes.py; backend/app/entrypoints/api/routes/notification_routes.py | backend/app/entrypoints/api/routes/booking_routes.py; backend/app/use_cases/store/confirm_checkin.py; backend/app/use_cases/store/lookup_checkin.py | one-time check-in security |
| inventory_items [I] | backend/app/adapters/persistence/sqlalchemy/models/string_catalog_item.py | backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_catalog_repository.py; backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_recommendation_repository.py; backend/app/dto/catalog.py; backend/app/entrypoints/api/routes/admin_routes.py; mobile/services/backendMappers.ts | backend/app/adapters/persistence/sqlalchemy/catalog_seed.py; backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_catalog_repository.py | sku is the sole removed field |
| inventory_movements [IM] | backend/app/adapters/persistence/sqlalchemy/models/string_catalog_item.py | backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_catalog_repository.py; backend/app/dto/catalog.py; backend/app/entrypoints/api/routes/admin_routes.py; mobile/services/backendMappers.ts | backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_catalog_repository.py | append-only stock history |
| notification_reads [NR] | backend/app/adapters/persistence/sqlalchemy/models/notification.py | backend/app/entrypoints/api/routes/notification_routes.py; mobile/services/backendMappers.ts | backend/app/entrypoints/api/routes/notification_routes.py | per-user read state |
| notifications [N] | backend/app/adapters/persistence/sqlalchemy/models/notification.py | backend/app/entrypoints/api/routes/notification_routes.py; backend/app/adapters/services/openwa.py; mobile/services/backendMappers.ts | backend/app/adapters/services/openwa.py; backend/app/entrypoints/api/routes/admin_routes.py | in-app/provider delivery state |
| password_reset_codes [PR] | backend/app/adapters/persistence/sqlalchemy/models/password_reset_code.py | backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_password_reset_repository.py; backend/app/entrypoints/api/routes/auth_routes.py | backend/app/use_cases/auth/request_password_reset.py; backend/app/use_cases/auth/reset_password.py; backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_password_reset_repository.py | hashed code lifecycle |
| payments [PAY] | backend/app/adapters/persistence/sqlalchemy/models/commerce.py | backend/app/entrypoints/api/routes/commerce_routes.py; backend/app/entrypoints/api/routes/admin_routes.py; backend/app/entrypoints/api/routes/notification_routes.py | backend/app/entrypoints/api/routes/commerce_routes.py; backend/app/entrypoints/api/routes/admin_routes.py | server-owned payments |
| profiles [P] | backend/app/adapters/persistence/sqlalchemy/models/profile.py | backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_profile_repository.py; backend/app/entrypoints/api/routes/profile_routes.py; backend/app/use_cases/recommendation/generate_recommendation.py | backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_profile_repository.py; backend/app/entrypoints/api/routes/profile_routes.py | profile/preferences |
| racket_model_catalog [RMC] | backend/app/adapters/persistence/sqlalchemy/models/racket_feedback.py | backend/app/entrypoints/api/routes/racket_feedback_routes.py; backend/app/entrypoints/api/routes/admin_routes.py; mobile/services/backendApi.ts | backend/app/entrypoints/api/routes/admin_routes.py; backend/app/adapters/persistence/sqlalchemy/seed.py | managed racket selector |
| rackets [R] | backend/app/adapters/persistence/sqlalchemy/models/racket_feedback.py | backend/app/entrypoints/api/routes/racket_feedback_routes.py; backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_recommendation_repository.py; mobile/services/backendMappers.ts | backend/app/entrypoints/api/routes/racket_feedback_routes.py | owned racket passport |
| recommendation_feature_definitions [FD] | backend/app/adapters/persistence/sqlalchemy/models/string_catalog_item.py | backend/app/adapters/persistence/sqlalchemy/recommendation_matrix_import.py; backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_recommendation_repository.py; backend/app/domain/recommendation/scoring.py; backend/app/entrypoints/api/routes/admin_routes.py | backend/app/adapters/persistence/sqlalchemy/recommendation_matrix_import.py; backend/app/adapters/persistence/sqlalchemy/seed.py | canonical feature metadata |
| recommendation_run_items [RI] | backend/app/adapters/persistence/sqlalchemy/models/recommendation_run.py | backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_recommendation_run_repository.py; backend/app/entrypoints/api/routes/admin_routes.py; backend/app/use_cases/agent/tools.py | backend/app/use_cases/recommendation/generate_recommendation.py; backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_recommendation_run_repository.py | immutable ranked output |
| recommendation_runs [RR] | backend/app/adapters/persistence/sqlalchemy/models/recommendation_run.py | backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_recommendation_run_repository.py; backend/app/entrypoints/api/routes/admin_routes.py; backend/app/use_cases/agent/tools.py | backend/app/use_cases/recommendation/generate_recommendation.py; backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_recommendation_run_repository.py | immutable recommendation audit |
| recommendation_score_cache [RC] | backend/app/adapters/persistence/sqlalchemy/models/string_catalog_item.py | backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_recommendation_repository.py; backend/app/use_cases/recommendation/generate_recommendation.py; backend/app/entrypoints/api/routes/admin_routes.py; backend/app/use_cases/agent/tools.py | backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_recommendation_repository.py | current V14 cache |
| store_business_hours [H] | backend/app/adapters/persistence/sqlalchemy/models/store_business_hours.py | backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_store_repository.py; backend/app/entrypoints/api/routes/store_routes.py; backend/app/use_cases/store/list_slots.py | backend/app/use_cases/store/update_business_hours.py; backend/app/entrypoints/api/routes/store_routes.py; backend/app/adapters/persistence/sqlalchemy/seed.py | single-store schedule |
| store_settings [SS] | backend/app/adapters/persistence/sqlalchemy/models/store_settings.py | backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_store_repository.py; backend/app/entrypoints/api/routes/store_routes.py; backend/app/use_cases/agent/tools.py | backend/app/use_cases/store/update_store_settings.py; backend/app/entrypoints/api/routes/admin_routes.py; backend/app/adapters/persistence/sqlalchemy/seed.py | single-store settings |
| string_catalog_metrics [CM] | backend/app/adapters/persistence/sqlalchemy/models/string_catalog_item.py | backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_catalog_repository.py; backend/app/entrypoints/api/routes/admin_engagement_routes.py | backend/app/adapters/persistence/sqlalchemy/catalog_seed.py; backend/app/entrypoints/api/routes/admin_engagement_routes.py | feedback-derived metrics |
| string_catalog_tags [CT] | backend/app/adapters/persistence/sqlalchemy/models/string_catalog_item.py | backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_catalog_repository.py; backend/app/entrypoints/api/routes/admin_engagement_routes.py | backend/app/adapters/persistence/sqlalchemy/catalog_seed.py; backend/app/entrypoints/api/routes/admin_engagement_routes.py | feedback-derived tags |
| string_official_performance [OP] | backend/app/adapters/persistence/sqlalchemy/models/string_catalog_item.py | backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_catalog_repository.py; backend/app/dto/catalog.py; backend/app/entrypoints/api/routes/admin_routes.py; backend/app/use_cases/agent/tools.py | backend/app/adapters/persistence/sqlalchemy/catalog_seed.py; backend/app/use_cases/catalog/update_official_performance.py; backend/app/entrypoints/api/routes/admin_routes.py | manual/official evidence |
| string_recommendation_matrix [RM] | backend/app/adapters/persistence/sqlalchemy/models/string_catalog_item.py | backend/app/adapters/persistence/sqlalchemy/recommendation_matrix_import.py; backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_recommendation_repository.py; backend/app/domain/recommendation/scoring.py; backend/app/entrypoints/api/routes/admin_routes.py; backend/app/use_cases/agent/tools.py | backend/app/adapters/persistence/sqlalchemy/recommendation_matrix_import.py; backend/app/adapters/persistence/sqlalchemy/catalog_seed.py | source-layered item matrix |
| strings [S] | backend/app/adapters/persistence/sqlalchemy/models/string_catalog_item.py | backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_catalog_repository.py; backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_recommendation_repository.py; backend/app/dto/catalog.py; backend/app/entrypoints/api/routes/catalog_routes.py; backend/app/entrypoints/api/routes/admin_routes.py; mobile/services/backendMappers.ts | backend/app/adapters/persistence/sqlalchemy/catalog_seed.py; backend/app/entrypoints/api/routes/admin_routes.py; backend/app/adapters/persistence/sqlalchemy/recommendation_matrix_import.py | catalog master/provenance |
| support_conversation_messages [SM] | backend/app/adapters/persistence/sqlalchemy/models/support_conversation.py | backend/app/entrypoints/api/routes/booking_conversation_routes.py; backend/app/entrypoints/api/routes/notification_routes.py | backend/app/entrypoints/api/routes/booking_conversation_routes.py | booking-free messages |
| support_conversations [SC] | backend/app/adapters/persistence/sqlalchemy/models/support_conversation.py | backend/app/entrypoints/api/routes/booking_conversation_routes.py; backend/app/entrypoints/api/routes/notification_routes.py | backend/app/entrypoints/api/routes/booking_conversation_routes.py | booking-free support state |
| user_preference_matrix [UP] | backend/app/adapters/persistence/sqlalchemy/models/string_catalog_item.py | backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_recommendation_repository.py; backend/app/domain/recommendation/scoring.py; backend/app/use_cases/profile/upsert_my_profile.py | backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_recommendation_repository.py; backend/app/use_cases/profile/upsert_my_profile.py | user-side vector |
| users [U] | backend/app/adapters/persistence/sqlalchemy/models/user.py | backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_user_repository.py; backend/app/use_cases/auth/login.py; backend/app/entrypoints/api/routes/auth_routes.py; backend/app/adapters/persistence/sqlalchemy/repositories/mappers.py; backend/app/dto/auth.py | backend/app/use_cases/auth/register.py; backend/app/adapters/persistence/sqlalchemy/seed.py; backend/app/adapters/persistence/sqlalchemy/repositories/sqlalchemy_user_repository.py | phone-first auth; provider fields are compatibility-only |
| wallet_transactions [WT] | backend/app/adapters/persistence/sqlalchemy/models/commerce.py | backend/app/entrypoints/api/routes/commerce_routes.py; backend/app/dto/commerce.py; mobile/services/backendMappers.ts | backend/app/entrypoints/api/routes/commerce_routes.py | append-only wallet ledger |

## Exhaustive baseline column coverage

### booking_conversations - 7 columns; 4 live rows

| # | column | PostgreSQL type | nullable | populated/rows | reader/writer evidence | constraints/indexes | disposition |
| ---: | --- | --- | :---: | ---: | --- | --- | --- |
| 1 | booking_id | character varying | no | 4/4 | R/W: surface BC; ORM present | booking_conversations_booking_id_fkey: FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE; booking_conversations_pkey: PRIMARY KEY (booking_id); index: booking_conversations_pkey | RETAIN; no removal selected |
| 2 | state | character varying | no | 4/4 | R/W: surface BC; ORM present | ck_booking_conversations_state: CHECK (((state)::text = ANY ((ARRAY['waiting_admin'::character varying, 'admin_joined'::character varying, 'resolved'::character varying, 'closed'::character varying])::text[]))); index: ix_booking_conversations_state | RETAIN; no removal selected |
| 3 | support_requested_at | timestamp with time zone | no | 4/4 | R/W: surface BC; ORM present | none recorded | RETAIN; no removal selected |
| 4 | player_last_read_at | timestamp with time zone | yes | 2/4 | R/W: surface BC; ORM present | none recorded | RETAIN; no removal selected |
| 5 | admin_last_read_at | timestamp with time zone | yes | 3/4 | R/W: surface BC; ORM present | none recorded | RETAIN; no removal selected |
| 6 | created_at | timestamp with time zone | no | 4/4 | R/W: surface BC; ORM present | none recorded | RETAIN; no removal selected |
| 7 | updated_at | timestamp with time zone | no | 4/4 | R/W: surface BC; ORM present | none recorded | RETAIN; no removal selected |

### booking_feedback - 16 columns; 362 live rows

| # | column | PostgreSQL type | nullable | populated/rows | reader/writer evidence | constraints/indexes | disposition |
| ---: | --- | --- | :---: | ---: | --- | --- | --- |
| 1 | id | character varying | no | 362/362 | R/W: surface F; ORM present | booking_feedback_pkey: PRIMARY KEY (id); index: booking_feedback_pkey | RETAIN; no removal selected |
| 2 | booking_id | character varying | no | 362/362 | R/W: surface F; ORM present | booking_feedback_booking_id_fkey: FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE; index: ix_booking_feedback_booking_id | RETAIN; no removal selected |
| 3 | user_id | character varying | no | 362/362 | R/W: surface F; ORM present | booking_feedback_user_id_fkey: FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE; index: ix_booking_feedback_user_id | RETAIN; no removal selected |
| 4 | rating | integer | no | 362/362 | R/W: surface F; ORM present | ck_booking_feedback_rating: CHECK (((rating >= 1) AND (rating <= 5))) | RETAIN; no removal selected |
| 5 | string_feedback | text | yes | 362/362 | R/W: surface F; ORM present | none recorded | RETAIN; no removal selected |
| 6 | service_feedback | text | yes | 2/362 | R/W: surface F; ORM present | none recorded | RETAIN; no removal selected |
| 8 | created_at | timestamp with time zone | no | 362/362 | R/W: surface F; ORM present | none recorded | RETAIN; no removal selected |
| 9 | updated_at | timestamp with time zone | no | 362/362 | R/W: surface F; ORM present | none recorded | RETAIN; no removal selected |
| 10 | recommendation_relevance | integer | yes | 361/362 | R/W: surface F; ORM present | ck_booking_feedback_detail_ratings: CHECK ((((recommendation_relevance IS NULL) OR ((recommendation_relevance >= 1) AND (recommendation_relevance <= 5))) AND ((string_satisfaction IS NULL) OR ((string_satisfaction >= 1) AND (string_satisfaction <= 5))) AND ((tension_satisfaction IS NULL) OR ((tension_satisfaction >= 1) AND (tension_satisfaction <= 5))) AND ((comfort IS NULL) OR ((comfort >= 1) AND (comfort <= 5))) AND ((control IS NULL) OR ((control >= 1) AND (control <= 5))) AND ((repulsion IS NULL) OR ((repulsion >= 1) AND (repulsion <= 5))))) | RETAIN; no removal selected |
| 11 | string_satisfaction | integer | yes | 361/362 | R/W: surface F; ORM present | ck_booking_feedback_detail_ratings: CHECK ((((recommendation_relevance IS NULL) OR ((recommendation_relevance >= 1) AND (recommendation_relevance <= 5))) AND ((string_satisfaction IS NULL) OR ((string_satisfaction >= 1) AND (string_satisfaction <= 5))) AND ((tension_satisfaction IS NULL) OR ((tension_satisfaction >= 1) AND (tension_satisfaction <= 5))) AND ((comfort IS NULL) OR ((comfort >= 1) AND (comfort <= 5))) AND ((control IS NULL) OR ((control >= 1) AND (control <= 5))) AND ((repulsion IS NULL) OR ((repulsion >= 1) AND (repulsion <= 5))))) | RETAIN; no removal selected |
| 12 | tension_satisfaction | integer | yes | 361/362 | R/W: surface F; ORM present | ck_booking_feedback_detail_ratings: CHECK ((((recommendation_relevance IS NULL) OR ((recommendation_relevance >= 1) AND (recommendation_relevance <= 5))) AND ((string_satisfaction IS NULL) OR ((string_satisfaction >= 1) AND (string_satisfaction <= 5))) AND ((tension_satisfaction IS NULL) OR ((tension_satisfaction >= 1) AND (tension_satisfaction <= 5))) AND ((comfort IS NULL) OR ((comfort >= 1) AND (comfort <= 5))) AND ((control IS NULL) OR ((control >= 1) AND (control <= 5))) AND ((repulsion IS NULL) OR ((repulsion >= 1) AND (repulsion <= 5))))) | RETAIN; no removal selected |
| 13 | comfort | integer | yes | 361/362 | R/W: surface F; ORM present | ck_booking_feedback_detail_ratings: CHECK ((((recommendation_relevance IS NULL) OR ((recommendation_relevance >= 1) AND (recommendation_relevance <= 5))) AND ((string_satisfaction IS NULL) OR ((string_satisfaction >= 1) AND (string_satisfaction <= 5))) AND ((tension_satisfaction IS NULL) OR ((tension_satisfaction >= 1) AND (tension_satisfaction <= 5))) AND ((comfort IS NULL) OR ((comfort >= 1) AND (comfort <= 5))) AND ((control IS NULL) OR ((control >= 1) AND (control <= 5))) AND ((repulsion IS NULL) OR ((repulsion >= 1) AND (repulsion <= 5))))) | RETAIN; no removal selected |
| 14 | control | integer | yes | 361/362 | R/W: surface F; ORM present | ck_booking_feedback_detail_ratings: CHECK ((((recommendation_relevance IS NULL) OR ((recommendation_relevance >= 1) AND (recommendation_relevance <= 5))) AND ((string_satisfaction IS NULL) OR ((string_satisfaction >= 1) AND (string_satisfaction <= 5))) AND ((tension_satisfaction IS NULL) OR ((tension_satisfaction >= 1) AND (tension_satisfaction <= 5))) AND ((comfort IS NULL) OR ((comfort >= 1) AND (comfort <= 5))) AND ((control IS NULL) OR ((control >= 1) AND (control <= 5))) AND ((repulsion IS NULL) OR ((repulsion >= 1) AND (repulsion <= 5))))) | RETAIN; no removal selected |
| 15 | repulsion | integer | yes | 361/362 | R/W: surface F; ORM present | ck_booking_feedback_detail_ratings: CHECK ((((recommendation_relevance IS NULL) OR ((recommendation_relevance >= 1) AND (recommendation_relevance <= 5))) AND ((string_satisfaction IS NULL) OR ((string_satisfaction >= 1) AND (string_satisfaction <= 5))) AND ((tension_satisfaction IS NULL) OR ((tension_satisfaction >= 1) AND (tension_satisfaction <= 5))) AND ((comfort IS NULL) OR ((comfort >= 1) AND (comfort <= 5))) AND ((control IS NULL) OR ((control >= 1) AND (control <= 5))) AND ((repulsion IS NULL) OR ((repulsion >= 1) AND (repulsion <= 5))))) | RETAIN; no removal selected |
| 17 | would_use_again | boolean | yes | 361/362 | R/W: surface F; ORM present | none recorded | RETAIN; no removal selected |
| 18 | comment | text | yes | 361/362 | R/W: surface F; ORM present | none recorded | RETAIN; no removal selected |

### booking_status_history - 6 columns; 400 live rows

| # | column | PostgreSQL type | nullable | populated/rows | reader/writer evidence | constraints/indexes | disposition |
| ---: | --- | --- | :---: | ---: | --- | --- | --- |
| 1 | id | character varying | no | 400/400 | R/W: surface BH; ORM present | booking_status_history_pkey: PRIMARY KEY (id); index: booking_status_history_pkey | RETAIN; no removal selected |
| 2 | booking_id | character varying | no | 400/400 | R/W: surface BH; ORM present | booking_status_history_booking_id_fkey: FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE; index: ix_booking_status_history_booking_id | RETAIN; no removal selected |
| 4 | new_status | character varying | no | 400/400 | R/W: surface BH; ORM present | none recorded | RETAIN; no removal selected |
| 5 | changed_by_user_id | character varying | yes | 397/400 | R/W: surface BH; ORM present | booking_status_history_changed_by_user_id_fkey: FOREIGN KEY (changed_by_user_id) REFERENCES users(id) | RETAIN; no removal selected |
| 6 | changed_at | timestamp with time zone | no | 400/400 | R/W: surface BH; ORM present | none recorded | RETAIN; no removal selected |
| 7 | note | text | yes | 371/400 | R/W: surface BH; ORM present | none recorded | RETAIN; no removal selected |

### booking_updates - 11 columns; 17 live rows

| # | column | PostgreSQL type | nullable | populated/rows | reader/writer evidence | constraints/indexes | disposition |
| ---: | --- | --- | :---: | ---: | --- | --- | --- |
| 1 | id | character varying | no | 17/17 | R/W: surface BU; ORM present | booking_updates_pkey: PRIMARY KEY (id); index: booking_updates_pkey | RETAIN; no removal selected |
| 2 | booking_id | character varying | no | 17/17 | R/W: surface BU; ORM present | booking_updates_booking_id_fkey: FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE; index: ix_booking_updates_booking_id | RETAIN; no removal selected |
| 3 | author_user_id | character varying | no | 17/17 | R/W: surface BU; ORM present | booking_updates_author_user_id_fkey: FOREIGN KEY (author_user_id) REFERENCES users(id); index: ix_booking_updates_author_user_id | RETAIN; no removal selected |
| 4 | author_role | character varying | no | 17/17 | R/W: surface BU; ORM present | none recorded | RETAIN; no removal selected |
| 5 | comment | text | yes | 17/17 | R/W: surface BU; ORM present | none recorded | RETAIN; no removal selected |
| 6 | photo_path | text | yes | 1/17 | R/W: surface BU; ORM present | none recorded | RETAIN; no removal selected |
| 7 | photo_original_name | character varying | yes | 1/17 | R/W: surface BU; ORM present | none recorded | RETAIN; no removal selected |
| 8 | photo_content_type | character varying | yes | 1/17 | R/W: surface BU; ORM present | none recorded | RETAIN; no removal selected |
| 9 | created_at | timestamp with time zone | no | 17/17 | R/W: surface BU; ORM present | none recorded | RETAIN; no removal selected |
| 10 | photo_type | character varying | yes | 1/17 | R/W: surface BU; ORM present | none recorded | RETAIN; no removal selected |
| 11 | channel | character varying | no | 17/17 | R/W: surface BU; ORM present | none recorded | RETAIN; no removal selected |

### bookings - 17 columns; 373 live rows

| # | column | PostgreSQL type | nullable | populated/rows | reader/writer evidence | constraints/indexes | disposition |
| ---: | --- | --- | :---: | ---: | --- | --- | --- |
| 1 | id | character varying | no | 373/373 | R/W: surface B; ORM present | bookings_pkey: PRIMARY KEY (id); index: bookings_pkey | RETAIN; no removal selected |
| 2 | user_id | character varying | no | 373/373 | R/W: surface B; ORM present | bookings_user_id_fkey: FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE; index: ix_bookings_user_id | RETAIN; no removal selected |
| 3 | string_id | character varying | no | 373/373 | R/W: surface B; ORM present | bookings_string_id_fkey: FOREIGN KEY (string_id) REFERENCES strings(catalog_id); index: ix_bookings_string_id | RETAIN; no removal selected |
| 4 | racket_brand | character varying | yes | 373/373 | R/W: surface B; ORM present | none recorded | RETAIN; no removal selected |
| 5 | racket_model | character varying | yes | 373/373 | R/W: surface B; ORM present | none recorded | RETAIN; no removal selected |
| 6 | requested_tension | numeric | yes | 373/373 | R/W: surface B; ORM present | none recorded | RETAIN; no removal selected |
| 7 | drop_off_datetime | timestamp with time zone | yes | 373/373 | R/W: surface B; ORM present | none recorded | RETAIN; no removal selected |
| 8 | notes | text | yes | 365/373 | R/W: surface B; ORM present | none recorded | RETAIN; no removal selected |
| 9 | status | character varying | no | 373/373 | R/W: surface B; ORM present | index: ix_bookings_status | RETAIN; no removal selected |
| 10 | created_at | timestamp with time zone | no | 373/373 | R/W: surface B; ORM present | none recorded | RETAIN; no removal selected |
| 11 | updated_at | timestamp with time zone | no | 373/373 | R/W: surface B; ORM present | none recorded | RETAIN; no removal selected |
| 12 | expected_completion_datetime | timestamp with time zone | yes | 362/373 | R/W: surface B; ORM present | none recorded | RETAIN; no removal selected |
| 13 | collection_datetime | timestamp with time zone | yes | 360/373 | R/W: surface B; ORM present | none recorded | RETAIN; no removal selected |
| 14 | cancellation_reason | text | yes | 0/373 | R/W: surface B; ORM present | none recorded | RETAIN; no removal selected |
| 15 | completion_summary | text | yes | 360/373 | R/W: surface B; ORM present | none recorded | RETAIN; no removal selected |
| 16 | racket_id | character varying | yes | 362/373 | R/W: surface B; ORM present | fk_bookings_racket_id_rackets: FOREIGN KEY (racket_id) REFERENCES rackets(id) ON DELETE SET NULL; index: ix_bookings_racket_id | RETAIN; no removal selected |
| 17 | service_method | character varying | no | 373/373 | R/W: surface B; ORM present | none recorded | RETAIN; no removal selected |

### brands - 4 columns; 6 live rows

| # | column | PostgreSQL type | nullable | populated/rows | reader/writer evidence | constraints/indexes | disposition |
| ---: | --- | --- | :---: | ---: | --- | --- | --- |
| 1 | brand_code | character varying | no | 6/6 | R/W: surface BR; ORM present | brands_pkey: PRIMARY KEY (brand_code); index: brands_pkey | RETAIN; no removal selected |
| 2 | brand_name | character varying | no | 6/6 | R/W: surface BR; ORM present | index: ix_brands_brand_name | RETAIN; no removal selected |
| 3 | created_at | timestamp with time zone | no | 6/6 | R/W: surface BR; ORM present | none recorded | RETAIN; no removal selected |
| 4 | updated_at | timestamp with time zone | no | 6/6 | R/W: surface BR; ORM present | none recorded | RETAIN; no removal selected |

### check_in_tokens - 7 columns; 10 live rows

| # | column | PostgreSQL type | nullable | populated/rows | reader/writer evidence | constraints/indexes | disposition |
| ---: | --- | --- | :---: | ---: | --- | --- | --- |
| 1 | id | character varying | no | 10/10 | R/W: surface CI; ORM present | check_in_tokens_pkey: PRIMARY KEY (id); index: check_in_tokens_pkey | RETAIN; no removal selected |
| 2 | booking_id | character varying | no | 10/10 | R/W: surface CI; ORM present | check_in_tokens_booking_id_fkey: FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE; index: ix_check_in_tokens_booking_id; index: uq_check_in_tokens_one_active_booking | RETAIN; no removal selected |
| 3 | token_hash | character varying | no | 10/10 | R/W: surface CI; ORM present | index: ix_check_in_tokens_token_hash | RETAIN; no removal selected |
| 4 | expires_at | timestamp with time zone | no | 10/10 | R/W: surface CI; ORM present | index: ix_check_in_tokens_expires_at | RETAIN; no removal selected |
| 5 | used_at | timestamp with time zone | yes | 0/10 | R/W: surface CI; ORM present | none recorded | RETAIN; no removal selected |
| 6 | revoked_at | timestamp with time zone | yes | 8/10 | R/W: surface CI; ORM present | none recorded | RETAIN; no removal selected |
| 7 | created_at | timestamp with time zone | no | 10/10 | R/W: surface CI; ORM present | none recorded | RETAIN; no removal selected |

### inventory_items - 14 columns; 12 live rows

| # | column | PostgreSQL type | nullable | populated/rows | reader/writer evidence | constraints/indexes | disposition |
| ---: | --- | --- | :---: | ---: | --- | --- | --- |
| 1 | inventory_id | character varying | no | 12/12 | R/W: surface I; ORM present | inventory_items_pkey: PRIMARY KEY (inventory_id); index: inventory_items_pkey | RETAIN; no removal selected |
| 2 | catalog_id | character varying | no | 12/12 | R/W: surface I; ORM present | inventory_items_catalog_id_fkey: FOREIGN KEY (catalog_id) REFERENCES strings(catalog_id) ON DELETE CASCADE; index: ix_inventory_items_catalog_id | RETAIN; no removal selected |
| 3 | sku | character varying | yes | 12/12 | R: none; W: legacy seed removed; H: migration 0008 only; ORM removed | inventory_items_sku_key: UNIQUE (sku); index: inventory_items_sku_key | REMOVE via 0046 |
| 4 | current_stock | integer | no | 12/12 | R/W: surface I; ORM present | none recorded | RETAIN; no removal selected |
| 5 | reserved_stock | integer | no | 12/12 | R/W: surface I; ORM present | none recorded | RETAIN; no removal selected |
| 6 | available_stock | integer | no | 12/12 | R/W: surface I; ORM present | none recorded | RETAIN; no removal selected |
| 7 | reorder_level | integer | no | 12/12 | R/W: surface I; ORM present | none recorded | RETAIN; no removal selected |
| 8 | reorder_quantity | integer | no | 12/12 | R/W: surface I; ORM present | none recorded | RETAIN; no removal selected |
| 9 | cost_price | numeric | yes | 0/12 | R/W: surface I; ORM present | none recorded | RETAIN; no removal selected |
| 10 | selling_price | numeric | yes | 12/12 | R/W: surface I; ORM present | none recorded | RETAIN; no removal selected |
| 11 | is_active | boolean | no | 12/12 | R/W: surface I; ORM present | index: ix_inventory_items_is_active | RETAIN; no removal selected |
| 12 | updated_at | timestamp with time zone | no | 12/12 | R/W: surface I; ORM present | none recorded | RETAIN; no removal selected |
| 13 | pricing_mode | character varying | no | 12/12 | R/W: surface I; ORM present | none recorded | RETAIN; no removal selected |
| 14 | availability_status | character varying | no | 12/12 | R/W: surface I; ORM present | index: ix_inventory_items_availability_status | RETAIN; no removal selected |

### inventory_movements - 8 columns; 16 live rows

| # | column | PostgreSQL type | nullable | populated/rows | reader/writer evidence | constraints/indexes | disposition |
| ---: | --- | --- | :---: | ---: | --- | --- | --- |
| 1 | movement_id | character varying | no | 16/16 | R/W: surface IM; ORM present | inventory_movements_pkey: PRIMARY KEY (movement_id); index: inventory_movements_pkey | RETAIN; no removal selected |
| 2 | inventory_id | character varying | no | 16/16 | R/W: surface IM; ORM present | inventory_movements_inventory_id_fkey: FOREIGN KEY (inventory_id) REFERENCES inventory_items(inventory_id) ON DELETE CASCADE; index: ix_inventory_movements_inventory_id | RETAIN; no removal selected |
| 3 | movement_type | character varying | no | 16/16 | R/W: surface IM; ORM present | index: ix_inventory_movements_movement_type | RETAIN; no removal selected |
| 4 | quantity | integer | no | 16/16 | R/W: surface IM; ORM present | none recorded | RETAIN; no removal selected |
| 5 | reference_type | character varying | yes | 3/16 | R/W: surface IM; ORM present | none recorded | RETAIN; no removal selected |
| 6 | reference_id | character varying | yes | 0/16 | R/W: surface IM; ORM present | none recorded | RETAIN; no removal selected |
| 7 | note | text | yes | 0/16 | R/W: surface IM; ORM present | none recorded | RETAIN; no removal selected |
| 8 | created_at | timestamp with time zone | no | 16/16 | R/W: surface IM; ORM present | index: ix_inventory_movements_created_at | RETAIN; no removal selected |

### notification_reads - 4 columns; 18 live rows

| # | column | PostgreSQL type | nullable | populated/rows | reader/writer evidence | constraints/indexes | disposition |
| ---: | --- | --- | :---: | ---: | --- | --- | --- |
| 1 | id | character varying | no | 18/18 | R/W: surface NR; ORM present | notification_reads_pkey: PRIMARY KEY (id); index: notification_reads_pkey | RETAIN; no removal selected |
| 2 | user_id | character varying | no | 18/18 | R/W: surface NR; ORM present | notification_reads_user_id_fkey: FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE; uq_notification_reads_user_event: UNIQUE (user_id, event_id); index: ix_notification_reads_user_id; index: uq_notification_reads_user_event | RETAIN; no removal selected |
| 3 | event_id | character varying | no | 18/18 | R/W: surface NR; ORM present | uq_notification_reads_user_event: UNIQUE (user_id, event_id); index: uq_notification_reads_user_event | RETAIN; no removal selected |
| 4 | read_at | timestamp with time zone | no | 18/18 | R/W: surface NR; ORM present | none recorded | RETAIN; no removal selected |

### notifications - 11 columns; 10 live rows

| # | column | PostgreSQL type | nullable | populated/rows | reader/writer evidence | constraints/indexes | disposition |
| ---: | --- | --- | :---: | ---: | --- | --- | --- |
| 1 | id | character varying | no | 10/10 | R/W: surface N; ORM present | notifications_pkey: PRIMARY KEY (id); index: notifications_pkey | RETAIN; no removal selected |
| 2 | user_id | character varying | no | 10/10 | R/W: surface N; ORM present | notifications_user_id_fkey: FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE; index: ix_notifications_user_id | RETAIN; no removal selected |
| 4 | category | character varying | no | 10/10 | R/W: surface N; ORM present | index: ix_notifications_category | RETAIN; no removal selected |
| 5 | title | character varying | no | 10/10 | R/W: surface N; ORM present | none recorded | RETAIN; no removal selected |
| 6 | body | text | no | 10/10 | R/W: surface N; ORM present | none recorded | RETAIN; no removal selected |
| 7 | route | character varying | yes | 9/10 | R/W: surface N; ORM present | none recorded | RETAIN; no removal selected |
| 8 | status | character varying | no | 10/10 | R/W: surface N; ORM present | index: ix_notifications_status | RETAIN; no removal selected |
| 9 | provider_message | text | yes | 10/10 | R/W: surface N; ORM present | none recorded | RETAIN; no removal selected |
| 10 | attempts | integer | no | 10/10 | R/W: surface N; ORM present | none recorded | RETAIN; no removal selected |
| 11 | created_at | timestamp with time zone | no | 10/10 | R/W: surface N; ORM present | none recorded | RETAIN; no removal selected |
| 12 | last_attempt_at | timestamp with time zone | yes | 10/10 | R/W: surface N; ORM present | none recorded | RETAIN; no removal selected |

### password_reset_codes - 8 columns; 4 live rows

| # | column | PostgreSQL type | nullable | populated/rows | reader/writer evidence | constraints/indexes | disposition |
| ---: | --- | --- | :---: | ---: | --- | --- | --- |
| 1 | id | character varying | no | 4/4 | R/W: surface PR; ORM present | password_reset_codes_pkey: PRIMARY KEY (id); index: password_reset_codes_pkey | RETAIN; no removal selected |
| 2 | user_id | character varying | no | 4/4 | R/W: surface PR; ORM present | password_reset_codes_user_id_fkey: FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE; index: ix_password_reset_codes_user_id | RETAIN; no removal selected |
| 3 | phone_number | character varying | no | 4/4 | R/W: surface PR; ORM present | index: ix_password_reset_codes_phone_number; index: uq_password_reset_codes_one_active_phone | RETAIN; no removal selected |
| 4 | code_hash | character varying | no | 4/4 | R/W: surface PR; ORM present | none recorded | RETAIN; no removal selected |
| 5 | attempt_count | integer | no | 4/4 | R/W: surface PR; ORM present | none recorded | RETAIN; no removal selected |
| 6 | expires_at | timestamp with time zone | no | 4/4 | R/W: surface PR; ORM present | none recorded | RETAIN; no removal selected |
| 7 | used_at | timestamp with time zone | yes | 2/4 | R/W: surface PR; ORM present | none recorded | RETAIN; no removal selected |
| 8 | created_at | timestamp with time zone | no | 4/4 | R/W: surface PR; ORM present | none recorded | RETAIN; no removal selected |

### payments - 12 columns; 0 live rows

| # | column | PostgreSQL type | nullable | populated/rows | reader/writer evidence | constraints/indexes | disposition |
| ---: | --- | --- | :---: | ---: | --- | --- | --- |
| 1 | id | character varying | no | 0/0 | R/W: surface PAY; ORM present | payments_pkey: PRIMARY KEY (id); index: payments_pkey | RETAIN; no removal selected |
| 2 | booking_id | character varying | yes | 0/0 | R/W: surface PAY; ORM present | payments_booking_id_fkey: FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE; index: ix_payments_booking_id | RETAIN; no removal selected |
| 3 | user_id | character varying | no | 0/0 | R/W: surface PAY; ORM present | payments_user_id_fkey: FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE; index: ix_payments_user_id | RETAIN; no removal selected |
| 4 | method | character varying | no | 0/0 | R/W: surface PAY; ORM present | ck_payments_current_method: CHECK (((method)::text = ANY ((ARRAY['qr_transfer'::character varying, 'cash'::character varying, 'wallet_balance'::character varying])::text[]))); ck_payments_qr_transfer_proof: CHECK ((((method)::text <> 'qr_transfer'::text) OR (proof_path IS NOT NULL))) | RETAIN; no removal selected |
| 5 | status | character varying | no | 0/0 | R/W: surface PAY; ORM present | index: ix_payments_status | RETAIN; no removal selected |
| 6 | amount | numeric | no | 0/0 | R/W: surface PAY; ORM present | none recorded | RETAIN; no removal selected |
| 7 | payment_type | character varying | no | 0/0 | R/W: surface PAY; ORM present | index: ix_payments_payment_type | RETAIN; no removal selected |
| 8 | reference | character varying | no | 0/0 | R/W: surface PAY; ORM present | index: ix_payments_reference | RETAIN; no removal selected |
| 9 | note | text | yes | 0/0 | R/W: surface PAY; ORM present | none recorded | RETAIN; no removal selected |
| 10 | created_at | timestamp with time zone | no | 0/0 | R/W: surface PAY; ORM present | none recorded | RETAIN; no removal selected |
| 11 | updated_at | timestamp with time zone | no | 0/0 | R/W: surface PAY; ORM present | none recorded | RETAIN; no removal selected |
| 12 | proof_path | text | yes | 0/0 | R/W: surface PAY; ORM present | ck_payments_qr_transfer_proof: CHECK ((((method)::text <> 'qr_transfer'::text) OR (proof_path IS NOT NULL))) | RETAIN; no removal selected |

### profiles - 22 columns; 94 live rows

| # | column | PostgreSQL type | nullable | populated/rows | reader/writer evidence | constraints/indexes | disposition |
| ---: | --- | --- | :---: | ---: | --- | --- | --- |
| 1 | id | character varying | no | 94/94 | R/W: surface P; ORM present | profiles_pkey: PRIMARY KEY (id); index: profiles_pkey | RETAIN; no removal selected |
| 2 | user_id | character varying | no | 94/94 | R/W: surface P; ORM present | profiles_user_id_fkey: FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE; index: ix_profiles_user_id | RETAIN; no removal selected |
| 3 | skill_level | character varying | yes | 94/94 | R/W: surface P; ORM present | none recorded | RETAIN; no removal selected |
| 4 | playing_style | character varying | yes | 94/94 | R/W: surface P; ORM present | none recorded | RETAIN; no removal selected |
| 7 | preferred_tension | numeric | yes | 94/94 | R/W: surface P; ORM present | none recorded | RETAIN; no removal selected |
| 9 | frequency_per_week | integer | yes | 94/94 | R/W: surface P; ORM present | none recorded | RETAIN; no removal selected |
| 10 | pref_attack | integer | yes | 94/94 | R/W: surface P; ORM present | none recorded | RETAIN; no removal selected |
| 11 | pref_comfort | integer | yes | 94/94 | R/W: surface P; ORM present | none recorded | RETAIN; no removal selected |
| 12 | pref_control | integer | yes | 94/94 | R/W: surface P; ORM present | none recorded | RETAIN; no removal selected |
| 13 | pref_durability | integer | yes | 94/94 | R/W: surface P; ORM present | none recorded | RETAIN; no removal selected |
| 14 | pref_elasticity | integer | yes | 94/94 | R/W: surface P; ORM present | none recorded | RETAIN; no removal selected |
| 15 | pref_sound | integer | yes | 94/94 | R/W: surface P; ORM present | none recorded | RETAIN; no removal selected |
| 16 | pref_string_movement | integer | yes | 94/94 | R/W: surface P; ORM present | none recorded | RETAIN; no removal selected |
| 17 | pref_tension_retention | integer | yes | 94/94 | R/W: surface P; ORM present | none recorded | RETAIN; no removal selected |
| 18 | pref_value_for_money | integer | yes | 94/94 | R/W: surface P; ORM present | none recorded | RETAIN; no removal selected |
| 19 | created_at | timestamp with time zone | no | 94/94 | R/W: surface P; ORM present | none recorded | RETAIN; no removal selected |
| 20 | updated_at | timestamp with time zone | no | 94/94 | R/W: surface P; ORM present | none recorded | RETAIN; no removal selected |
| 22 | preferred_feel | character varying | yes | 94/94 | R/W: surface P; ORM present | none recorded | RETAIN; no removal selected |
| 23 | recent_goal | character varying | yes | 94/94 | R/W: surface P; ORM present | none recorded | RETAIN; no removal selected |
| 24 | notification_preferences | json | no | 94/94 | R/W: surface P; ORM present | none recorded | RETAIN; no removal selected |
| 25 | privacy_settings | json | no | 94/94 | R/W: surface P; ORM present | none recorded | RETAIN; no removal selected |
| 26 | preferred_gauge | character varying | yes | 94/94 | R/W: surface P; ORM present | none recorded | RETAIN; no removal selected |

### racket_model_catalog - 7 columns; 6 live rows

| # | column | PostgreSQL type | nullable | populated/rows | reader/writer evidence | constraints/indexes | disposition |
| ---: | --- | --- | :---: | ---: | --- | --- | --- |
| 1 | id | character varying | no | 6/6 | R/W: surface RMC; ORM present | racket_model_catalog_pkey: PRIMARY KEY (id); index: racket_model_catalog_pkey | RETAIN; no removal selected |
| 2 | model_key | character varying | no | 6/6 | R/W: surface RMC; ORM present | index: ix_racket_model_catalog_model_key | RETAIN; no removal selected |
| 3 | brand | character varying | no | 6/6 | R/W: surface RMC; ORM present | none recorded | RETAIN; no removal selected |
| 4 | model | character varying | no | 6/6 | R/W: surface RMC; ORM present | none recorded | RETAIN; no removal selected |
| 5 | is_active | boolean | no | 6/6 | R/W: surface RMC; ORM present | index: ix_racket_model_catalog_is_active | RETAIN; no removal selected |
| 6 | created_at | timestamp with time zone | no | 6/6 | R/W: surface RMC; ORM present | none recorded | RETAIN; no removal selected |
| 7 | updated_at | timestamp with time zone | no | 6/6 | R/W: surface RMC; ORM present | none recorded | RETAIN; no removal selected |

### rackets - 12 columns; 78 live rows

| # | column | PostgreSQL type | nullable | populated/rows | reader/writer evidence | constraints/indexes | disposition |
| ---: | --- | --- | :---: | ---: | --- | --- | --- |
| 1 | id | character varying | no | 78/78 | R/W: surface R; ORM present | rackets_pkey: PRIMARY KEY (id); index: rackets_pkey | RETAIN; no removal selected |
| 2 | user_id | character varying | no | 78/78 | R/W: surface R; ORM present | rackets_user_id_fkey: FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE; index: ix_rackets_user_id | RETAIN; no removal selected |
| 3 | nickname | character varying | no | 78/78 | R/W: surface R; ORM present | none recorded | RETAIN; no removal selected |
| 4 | brand | character varying | no | 78/78 | R/W: surface R; ORM present | none recorded | RETAIN; no removal selected |
| 5 | model | character varying | no | 78/78 | R/W: surface R; ORM present | none recorded | RETAIN; no removal selected |
| 6 | weight_class | character varying | yes | 4/78 | R/W: surface R; ORM present | none recorded | RETAIN; no removal selected |
| 7 | balance_point | character varying | yes | 4/78 | R/W: surface R; ORM present | none recorded | RETAIN; no removal selected |
| 8 | grip_size | character varying | yes | 4/78 | R/W: surface R; ORM present | none recorded | RETAIN; no removal selected |
| 9 | preferred_use | character varying | yes | 76/78 | R/W: surface R; ORM present | none recorded | RETAIN; no removal selected |
| 10 | notes | text | yes | 76/78 | R/W: surface R; ORM present | none recorded | RETAIN; no removal selected |
| 11 | created_at | timestamp with time zone | no | 78/78 | R/W: surface R; ORM present | none recorded | RETAIN; no removal selected |
| 12 | updated_at | timestamp with time zone | no | 78/78 | R/W: surface R; ORM present | none recorded | RETAIN; no removal selected |

### recommendation_feature_definitions - 10 columns; 26 live rows

| # | column | PostgreSQL type | nullable | populated/rows | reader/writer evidence | constraints/indexes | disposition |
| ---: | --- | --- | :---: | ---: | --- | --- | --- |
| 1 | feature_key | character varying | no | 26/26 | R/W: surface FD; ORM present | recommendation_feature_definitions_pkey: PRIMARY KEY (feature_key); index: recommendation_feature_definitions_pkey | RETAIN; no removal selected |
| 2 | feature_label | character varying | no | 26/26 | R/W: surface FD; ORM present | none recorded | RETAIN; no removal selected |
| 3 | feature_group | character varying | no | 26/26 | R/W: surface FD; ORM present | index: ix_recommendation_feature_definitions_feature_group | RETAIN; no removal selected |
| 4 | data_type | character varying | no | 26/26 | R/W: surface FD; ORM present | none recorded | RETAIN; no removal selected |
| 5 | min_value | numeric | yes | 26/26 | R/W: surface FD; ORM present | none recorded | RETAIN; no removal selected |
| 6 | max_value | numeric | yes | 26/26 | R/W: surface FD; ORM present | none recorded | RETAIN; no removal selected |
| 7 | description | text | yes | 26/26 | R/W: surface FD; ORM present | none recorded | RETAIN; no removal selected |
| 8 | is_active | boolean | no | 26/26 | R/W: surface FD; ORM present | index: ix_recommendation_feature_definitions_is_active | RETAIN; no removal selected |
| 9 | created_at | timestamp with time zone | no | 26/26 | R/W: surface FD; ORM present | none recorded | RETAIN; no removal selected |
| 10 | updated_at | timestamp with time zone | no | 26/26 | R/W: surface FD; ORM present | none recorded | RETAIN; no removal selected |

### recommendation_run_items - 11 columns; 152 live rows

| # | column | PostgreSQL type | nullable | populated/rows | reader/writer evidence | constraints/indexes | disposition |
| ---: | --- | --- | :---: | ---: | --- | --- | --- |
| 1 | id | character varying | no | 152/152 | R/W: surface RI; ORM present | recommendation_run_items_pkey: PRIMARY KEY (id); index: recommendation_run_items_pkey | RETAIN; no removal selected |
| 2 | run_id | character varying | no | 152/152 | R/W: surface RI; ORM present | recommendation_run_items_run_id_fkey: FOREIGN KEY (run_id) REFERENCES recommendation_runs(id) ON DELETE CASCADE; index: ix_recommendation_run_items_run_id | RETAIN; no removal selected |
| 3 | catalog_id | character varying | no | 152/152 | R/W: surface RI; ORM present | index: ix_recommendation_run_items_catalog_id | RETAIN; no removal selected |
| 4 | rank_position | integer | no | 152/152 | R/W: surface RI; ORM present | none recorded | RETAIN; no removal selected |
| 5 | final_score | numeric | no | 152/152 | R/W: surface RI; ORM present | none recorded | RETAIN; no removal selected |
| 6 | preference_match_score | numeric | yes | 152/152 | R/W: surface RI; ORM present | none recorded | RETAIN; no removal selected |
| 7 | rule_fit_score | numeric | yes | 152/152 | R/W: surface RI; ORM present | none recorded | RETAIN; no removal selected |
| 10 | nlp_review_score | numeric | yes | 152/152 | R/W: surface RI; ORM present | none recorded | RETAIN; no removal selected |
| 11 | score_breakdown | json | no | 152/152 | R/W: surface RI; ORM present | none recorded | RETAIN; no removal selected |
| 12 | rationale | json | no | 152/152 | R/W: surface RI; ORM present | none recorded | RETAIN; no removal selected |
| 13 | value_for_money_score | numeric | yes | 122/152 | R/W: surface RI; ORM present | none recorded | RETAIN; no removal selected |

### recommendation_runs - 6 columns; 44 live rows

| # | column | PostgreSQL type | nullable | populated/rows | reader/writer evidence | constraints/indexes | disposition |
| ---: | --- | --- | :---: | ---: | --- | --- | --- |
| 1 | id | character varying | no | 44/44 | R/W: surface RR; ORM present | recommendation_runs_pkey: PRIMARY KEY (id); index: recommendation_runs_pkey | RETAIN; no removal selected |
| 2 | user_id | character varying | yes | 44/44 | R/W: surface RR; ORM present | recommendation_runs_user_id_fkey: FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL; index: ix_recommendation_runs_user_id | RETAIN; no removal selected |
| 3 | algorithm_version | character varying | no | 44/44 | R/W: surface RR; ORM present | index: ix_recommendation_runs_algorithm_version | RETAIN; no removal selected |
| 6 | request_snapshot | json | no | 44/44 | R/W: surface RR; ORM present | none recorded | RETAIN; no removal selected |
| 7 | profile_snapshot | json | no | 44/44 | R/W: surface RR; ORM present | none recorded | RETAIN; no removal selected |
| 8 | generated_at | timestamp with time zone | no | 44/44 | R/W: surface RR; ORM present | index: ix_recommendation_runs_generated_at | RETAIN; no removal selected |

### recommendation_score_cache - 11 columns; 0 live rows

| # | column | PostgreSQL type | nullable | populated/rows | reader/writer evidence | constraints/indexes | disposition |
| ---: | --- | --- | :---: | ---: | --- | --- | --- |
| 1 | user_id | character varying | no | 0/0 | R/W: surface RC; ORM present | recommendation_score_cache_pkey: PRIMARY KEY (user_id, catalog_id, algorithm_version); recommendation_score_cache_user_id_fkey: FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE; index: recommendation_score_cache_pkey | RETAIN; no removal selected |
| 2 | catalog_id | character varying | no | 0/0 | R/W: surface RC; ORM present | recommendation_score_cache_catalog_id_fkey: FOREIGN KEY (catalog_id) REFERENCES strings(catalog_id) ON DELETE CASCADE; recommendation_score_cache_pkey: PRIMARY KEY (user_id, catalog_id, algorithm_version); index: recommendation_score_cache_pkey | RETAIN; no removal selected |
| 3 | algorithm_version | character varying | no | 0/0 | R/W: surface RC; ORM present | recommendation_score_cache_pkey: PRIMARY KEY (user_id, catalog_id, algorithm_version); index: recommendation_score_cache_pkey | RETAIN; no removal selected |
| 8 | final_score | numeric | no | 0/0 | R/W: surface RC; ORM present | none recorded | RETAIN; no removal selected |
| 9 | rank_position | integer | no | 0/0 | R/W: surface RC; ORM present | none recorded | RETAIN; no removal selected |
| 10 | rationale | json | no | 0/0 | R/W: surface RC; ORM present | none recorded | RETAIN; no removal selected |
| 11 | generated_at | timestamp with time zone | no | 0/0 | R/W: surface RC; ORM present | index: ix_recommendation_score_cache_generated_at | RETAIN; no removal selected |
| 12 | preference_match_score | numeric | yes | 0/0 | R/W: surface RC; ORM present | none recorded | RETAIN; no removal selected |
| 13 | rule_fit_score | numeric | yes | 0/0 | R/W: surface RC; ORM present | none recorded | RETAIN; no removal selected |
| 15 | nlp_review_score | numeric | yes | 0/0 | R/W: surface RC; ORM present | none recorded | RETAIN; no removal selected |
| 19 | value_for_money_score | numeric | yes | 0/0 | R/W: surface RC; ORM present | none recorded | RETAIN; no removal selected |

### store_business_hours - 5 columns; 1 live rows

| # | column | PostgreSQL type | nullable | populated/rows | reader/writer evidence | constraints/indexes | disposition |
| ---: | --- | --- | :---: | ---: | --- | --- | --- |
| 1 | id | character varying | no | 1/1 | R/W: surface H; ORM present | store_business_hours_pkey: PRIMARY KEY (id); index: store_business_hours_pkey | RETAIN; no removal selected |
| 2 | days_json | json | no | 1/1 | R/W: surface H; ORM present | none recorded | RETAIN; no removal selected |
| 3 | special_closed_dates | json | no | 1/1 | R/W: surface H; ORM present | none recorded | RETAIN; no removal selected |
| 4 | created_at | timestamp with time zone | no | 1/1 | R/W: surface H; ORM present | none recorded | RETAIN; no removal selected |
| 5 | updated_at | timestamp with time zone | no | 1/1 | R/W: surface H; ORM present | none recorded | RETAIN; no removal selected |

### store_settings - 13 columns; 1 live rows

| # | column | PostgreSQL type | nullable | populated/rows | reader/writer evidence | constraints/indexes | disposition |
| ---: | --- | --- | :---: | ---: | --- | --- | --- |
| 1 | id | character varying | no | 1/1 | R/W: surface SS; ORM present | store_settings_pkey: PRIMARY KEY (id); index: store_settings_pkey | RETAIN; no removal selected |
| 2 | store_name | character varying | no | 1/1 | R/W: surface SS; ORM present | none recorded | RETAIN; no removal selected |
| 3 | store_contact | character varying | no | 1/1 | R/W: surface SS; ORM present | none recorded | RETAIN; no removal selected |
| 4 | support_text | text | no | 1/1 | R/W: surface SS; ORM present | none recorded | RETAIN; no removal selected |
| 5 | payment_notes | text | no | 1/1 | R/W: surface SS; ORM present | none recorded | RETAIN; no removal selected |
| 6 | booking_notes | text | no | 1/1 | R/W: surface SS; ORM present | none recorded | RETAIN; no removal selected |
| 7 | store_policy_text | text | no | 1/1 | R/W: surface SS; ORM present | none recorded | RETAIN; no removal selected |
| 8 | address | text | no | 1/1 | R/W: surface SS; ORM present | none recorded | RETAIN; no removal selected |
| 9 | created_at | timestamp with time zone | no | 1/1 | R/W: surface SS; ORM present | none recorded | RETAIN; no removal selected |
| 10 | updated_at | timestamp with time zone | no | 1/1 | R/W: surface SS; ORM present | none recorded | RETAIN; no removal selected |
| 11 | trending_string_ids | json | no | 1/1 | R/W: surface SS; ORM present | none recorded | RETAIN; no removal selected |
| 13 | notification_settings | json | no | 1/1 | R/W: surface SS; ORM present | none recorded | RETAIN; no removal selected |
| 14 | payment_qr_path | text | yes | 1/1 | R/W: surface SS; ORM present | none recorded | RETAIN; no removal selected |

### string_catalog_metrics - 6 columns; 12 live rows

| # | column | PostgreSQL type | nullable | populated/rows | reader/writer evidence | constraints/indexes | disposition |
| ---: | --- | --- | :---: | ---: | --- | --- | --- |
| 1 | catalog_id | character varying | no | 12/12 | R/W: surface CM; ORM present | string_catalog_metrics_catalog_id_fkey: FOREIGN KEY (catalog_id) REFERENCES strings(catalog_id) ON DELETE CASCADE; string_catalog_metrics_pkey: PRIMARY KEY (catalog_id); index: string_catalog_metrics_pkey | RETAIN; no removal selected |
| 2 | feedback_rating | numeric | yes | 12/12 | R/W: surface CM; ORM present | none recorded | RETAIN; no removal selected |
| 3 | want_count | integer | no | 12/12 | R/W: surface CM; ORM present | none recorded | RETAIN; no removal selected |
| 4 | used_count | integer | no | 12/12 | R/W: surface CM; ORM present | none recorded | RETAIN; no removal selected |
| 5 | review_count | integer | no | 12/12 | R/W: surface CM; ORM present | none recorded | RETAIN; no removal selected |
| 6 | updated_at | timestamp with time zone | no | 12/12 | R/W: surface CM; ORM present | none recorded | RETAIN; no removal selected |

### string_catalog_tags - 4 columns; 48 live rows

| # | column | PostgreSQL type | nullable | populated/rows | reader/writer evidence | constraints/indexes | disposition |
| ---: | --- | --- | :---: | ---: | --- | --- | --- |
| 1 | catalog_id | character varying | no | 48/48 | R/W: surface CT; ORM present | string_catalog_tags_catalog_id_fkey: FOREIGN KEY (catalog_id) REFERENCES strings(catalog_id) ON DELETE CASCADE; string_catalog_tags_pkey: PRIMARY KEY (catalog_id, tag_key); index: string_catalog_tags_pkey | RETAIN; no removal selected |
| 2 | tag_key | character varying | no | 48/48 | R/W: surface CT; ORM present | string_catalog_tags_pkey: PRIMARY KEY (catalog_id, tag_key); index: string_catalog_tags_pkey | RETAIN; no removal selected |
| 3 | tag_label | character varying | no | 48/48 | R/W: surface CT; ORM present | none recorded | RETAIN; no removal selected |
| 4 | tag_count | integer | no | 48/48 | R/W: surface CT; ORM present | none recorded | RETAIN; no removal selected |

### string_official_performance - 15 columns; 12 live rows

| # | column | PostgreSQL type | nullable | populated/rows | reader/writer evidence | constraints/indexes | disposition |
| ---: | --- | --- | :---: | ---: | --- | --- | --- |
| 1 | catalog_id | character varying | no | 12/12 | R/W: surface OP; ORM present | string_official_performance_catalog_id_fkey: FOREIGN KEY (catalog_id) REFERENCES strings(catalog_id) ON DELETE CASCADE; string_official_performance_pkey: PRIMARY KEY (catalog_id); index: string_official_performance_pkey | RETAIN; no removal selected |
| 2 | source_type | character varying | yes | 12/12 | R/W: surface OP; ORM present | none recorded | RETAIN; no removal selected |
| 3 | source_name | character varying | yes | 12/12 | R/W: surface OP; ORM present | none recorded | RETAIN; no removal selected |
| 5 | source_region | character varying | yes | 0/12 | R/W: surface OP; ORM present | none recorded | RETAIN; no removal selected |
| 6 | category | numeric | yes | 0/12 | R/W: surface OP; ORM present | none recorded | RETAIN; no removal selected |
| 7 | feature | numeric | yes | 0/12 | R/W: surface OP; ORM present | none recorded | RETAIN; no removal selected |
| 8 | feel | numeric | yes | 12/12 | R/W: surface OP; ORM present | none recorded | RETAIN; no removal selected |
| 9 | repulsion_power | numeric | yes | 12/12 | R/W: surface OP; ORM present | none recorded | RETAIN; no removal selected |
| 10 | durability | numeric | yes | 12/12 | R/W: surface OP; ORM present | none recorded | RETAIN; no removal selected |
| 11 | hitting_sound | numeric | yes | 12/12 | R/W: surface OP; ORM present | none recorded | RETAIN; no removal selected |
| 12 | shock_absorption | numeric | yes | 12/12 | R/W: surface OP; ORM present | none recorded | RETAIN; no removal selected |
| 13 | control | numeric | yes | 12/12 | R/W: surface OP; ORM present | none recorded | RETAIN; no removal selected |
| 14 | notes | text | yes | 3/12 | R/W: surface OP; ORM present | none recorded | RETAIN; no removal selected |
| 15 | status | character varying | no | 12/12 | R/W: surface OP; ORM present | index: ix_string_official_performance_status | RETAIN; no removal selected |
| 16 | updated_at | timestamp with time zone | no | 12/12 | R/W: surface OP; ORM present | none recorded | RETAIN; no removal selected |

### string_recommendation_matrix - 7 columns; 264 live rows

| # | column | PostgreSQL type | nullable | populated/rows | reader/writer evidence | constraints/indexes | disposition |
| ---: | --- | --- | :---: | ---: | --- | --- | --- |
| 1 | catalog_id | character varying | no | 264/264 | R/W: surface RM; ORM present | string_recommendation_matrix_catalog_id_fkey: FOREIGN KEY (catalog_id) REFERENCES strings(catalog_id) ON DELETE CASCADE; string_recommendation_matrix_pkey: PRIMARY KEY (catalog_id, feature_key, source_layer); index: string_recommendation_matrix_pkey | RETAIN; no removal selected |
| 2 | feature_key | character varying | no | 264/264 | R/W: surface RM; ORM present | string_recommendation_matrix_feature_key_fkey: FOREIGN KEY (feature_key) REFERENCES recommendation_feature_definitions(feature_key) ON DELETE CASCADE; string_recommendation_matrix_pkey: PRIMARY KEY (catalog_id, feature_key, source_layer); index: string_recommendation_matrix_pkey | RETAIN; no removal selected |
| 3 | source_layer | character varying | no | 264/264 | R/W: surface RM; ORM present | string_recommendation_matrix_pkey: PRIMARY KEY (catalog_id, feature_key, source_layer); index: string_recommendation_matrix_pkey | RETAIN; no removal selected |
| 4 | raw_value | numeric | yes | 264/264 | R/W: surface RM; ORM present | none recorded | RETAIN; no removal selected |
| 5 | normalized_score | numeric | yes | 264/264 | R/W: surface RM; ORM present | index: ix_string_recommendation_matrix_normalized_score | RETAIN; no removal selected |
| 7 | evidence_note | text | yes | 156/264 | R/W: surface RM; ORM present | none recorded | RETAIN; no removal selected |
| 9 | updated_at | timestamp with time zone | no | 264/264 | R/W: surface RM; ORM present | none recorded | RETAIN; no removal selected |

### strings - 30 columns; 12 live rows

| # | column | PostgreSQL type | nullable | populated/rows | reader/writer evidence | constraints/indexes | disposition |
| ---: | --- | --- | :---: | ---: | --- | --- | --- |
| 1 | catalog_id | character varying | no | 12/12 | R/W: surface S; ORM present | strings_pkey: PRIMARY KEY (catalog_id); index: strings_pkey | RETAIN; no removal selected |
| 2 | brand_code | character varying | no | 12/12 | R/W: surface S; ORM present | fk_strings_brand_code_brands: FOREIGN KEY (brand_code) REFERENCES brands(brand_code); index: ix_strings_brand_code | RETAIN; no removal selected |
| 3 | display_name | character varying | no | 12/12 | R/W: surface S; ORM present | index: ix_strings_display_name | RETAIN; no removal selected |
| 4 | model_name | character varying | no | 12/12 | R/W: surface S; ORM present | index: ix_strings_model_name | RETAIN; no removal selected |
| 5 | series_key | character varying | yes | 12/12 | R/W: surface S; ORM present | index: ix_strings_series_key | RETAIN; no removal selected |
| 6 | series_label | character varying | yes | 12/12 | R/W: surface S; ORM present | none recorded | RETAIN; no removal selected |
| 7 | is_hybrid | boolean | no | 12/12 | R/W: surface S; ORM present | none recorded | RETAIN; no removal selected |
| 8 | gauge_main_mm | numeric | yes | 12/12 | R/W: surface S; ORM present | none recorded | RETAIN; no removal selected |
| 9 | gauge_cross_mm | numeric | yes | 9/12 | R/W: surface S; ORM present | none recorded | RETAIN; no removal selected |
| 10 | gauge_label | character varying | yes | 12/12 | R/W: surface S; ORM present | none recorded | RETAIN; no removal selected |
| 11 | material_summary_en | text | yes | 12/12 | R/W: surface S; ORM present | none recorded | RETAIN; no removal selected |
| 12 | color_options_en | json | no | 12/12 | R/W: surface S; ORM present | none recorded | RETAIN; no removal selected |
| 13 | short_description | text | no | 12/12 | R/W: surface S; ORM present | none recorded | RETAIN; no removal selected |
| 14 | full_description | text | no | 12/12 | R/W: surface S; ORM present | none recorded | RETAIN; no removal selected |
| 15 | official_performance_status | character varying | no | 12/12 | R/W: surface S; ORM present | index: ix_strings_official_performance_status | RETAIN; no removal selected |
| 16 | source_dataset_url | text | yes | 12/12 | R/W: surface S; ORM present | none recorded | RETAIN; no removal selected |
| 17 | source_language | character varying | yes | 12/12 | R/W: surface S; ORM present | none recorded | RETAIN; no removal selected |
| 18 | original_name | character varying | yes | 12/12 | R/W: surface S; ORM present | none recorded | RETAIN; no removal selected |
| 19 | original_brand_label | character varying | yes | 12/12 | R/W: surface S; ORM present | none recorded | RETAIN; no removal selected |
| 20 | original_series | character varying | yes | 10/12 | R/W: surface S; ORM present | none recorded | RETAIN; no removal selected |
| 21 | original_material | text | yes | 12/12 | R/W: surface S; ORM present | none recorded | RETAIN; no removal selected |
| 22 | original_color | text | yes | 12/12 | R/W: surface S; ORM present | none recorded | RETAIN; no removal selected |
| 23 | is_active | boolean | no | 12/12 | R/W: surface S; ORM present | index: ix_strings_is_active | RETAIN; no removal selected |
| 24 | created_at | timestamp with time zone | no | 12/12 | R/W: surface S; ORM present | none recorded | RETAIN; no removal selected |
| 25 | updated_at | timestamp with time zone | no | 12/12 | R/W: surface S; ORM present | none recorded | RETAIN; no removal selected |
| 26 | category | character varying | yes | 9/12 | R/W: surface S; ORM present | index: ix_strings_category | RETAIN; no removal selected |
| 27 | main_trait | character varying | yes | 9/12 | R/W: surface S; ORM present | none recorded | RETAIN; no removal selected |
| 28 | tension_min_lbs | integer | yes | 12/12 | R/W: surface S; ORM present | none recorded | RETAIN; no removal selected |
| 29 | tension_max_lbs | integer | yes | 12/12 | R/W: surface S; ORM present | none recorded | RETAIN; no removal selected |
| 30 | image_url | text | yes | 12/12 | R/W: surface S; ORM present | none recorded | RETAIN; no removal selected |

### support_conversation_messages - 6 columns; 2 live rows

| # | column | PostgreSQL type | nullable | populated/rows | reader/writer evidence | constraints/indexes | disposition |
| ---: | --- | --- | :---: | ---: | --- | --- | --- |
| 1 | id | character varying | no | 2/2 | R/W: surface SM; ORM present | support_conversation_messages_pkey: PRIMARY KEY (id); index: support_conversation_messages_pkey | RETAIN; no removal selected |
| 2 | conversation_id | character varying | no | 2/2 | R/W: surface SM; ORM present | support_conversation_messages_conversation_id_fkey: FOREIGN KEY (conversation_id) REFERENCES support_conversations(id) ON DELETE CASCADE; index: ix_support_conversation_messages_conversation_id | RETAIN; no removal selected |
| 3 | author_user_id | character varying | no | 2/2 | R/W: surface SM; ORM present | support_conversation_messages_author_user_id_fkey: FOREIGN KEY (author_user_id) REFERENCES users(id); index: ix_support_conversation_messages_author_user_id | RETAIN; no removal selected |
| 4 | author_role | character varying | no | 2/2 | R/W: surface SM; ORM present | none recorded | RETAIN; no removal selected |
| 5 | body | text | no | 2/2 | R/W: surface SM; ORM present | none recorded | RETAIN; no removal selected |
| 6 | created_at | timestamp with time zone | no | 2/2 | R/W: surface SM; ORM present | index: ix_support_conversation_messages_created_at | RETAIN; no removal selected |

### support_conversations - 8 columns; 2 live rows

| # | column | PostgreSQL type | nullable | populated/rows | reader/writer evidence | constraints/indexes | disposition |
| ---: | --- | --- | :---: | ---: | --- | --- | --- |
| 1 | id | character varying | no | 2/2 | R/W: surface SC; ORM present | support_conversations_pkey: PRIMARY KEY (id); index: support_conversations_pkey | RETAIN; no removal selected |
| 2 | player_id | character varying | no | 2/2 | R/W: surface SC; ORM present | support_conversations_player_id_fkey: FOREIGN KEY (player_id) REFERENCES users(id) ON DELETE CASCADE; uq_support_conversations_player: UNIQUE (player_id); index: ix_support_conversations_player_id; index: uq_support_conversations_player | RETAIN; no removal selected |
| 3 | state | character varying | no | 2/2 | R/W: surface SC; ORM present | ck_support_conversations_state: CHECK (((state)::text = ANY ((ARRAY['waiting_admin'::character varying, 'admin_joined'::character varying, 'resolved'::character varying, 'closed'::character varying])::text[]))); index: ix_support_conversations_state | RETAIN; no removal selected |
| 4 | support_requested_at | timestamp with time zone | no | 2/2 | R/W: surface SC; ORM present | none recorded | RETAIN; no removal selected |
| 5 | player_last_read_at | timestamp with time zone | yes | 0/2 | R/W: surface SC; ORM present | none recorded | RETAIN; no removal selected |
| 6 | admin_last_read_at | timestamp with time zone | yes | 1/2 | R/W: surface SC; ORM present | none recorded | RETAIN; no removal selected |
| 7 | created_at | timestamp with time zone | no | 2/2 | R/W: surface SC; ORM present | none recorded | RETAIN; no removal selected |
| 8 | updated_at | timestamp with time zone | no | 2/2 | R/W: surface SC; ORM present | none recorded | RETAIN; no removal selected |

### user_preference_matrix - 8 columns; 192 live rows

| # | column | PostgreSQL type | nullable | populated/rows | reader/writer evidence | constraints/indexes | disposition |
| ---: | --- | --- | :---: | ---: | --- | --- | --- |
| 1 | user_id | character varying | no | 192/192 | R/W: surface UP; ORM present | user_preference_matrix_pkey: PRIMARY KEY (user_id, feature_key, source_layer); user_preference_matrix_user_id_fkey: FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE; index: user_preference_matrix_pkey | RETAIN; no removal selected |
| 2 | feature_key | character varying | no | 192/192 | R/W: surface UP; ORM present | user_preference_matrix_feature_key_fkey: FOREIGN KEY (feature_key) REFERENCES recommendation_feature_definitions(feature_key) ON DELETE CASCADE; user_preference_matrix_pkey: PRIMARY KEY (user_id, feature_key, source_layer); index: user_preference_matrix_pkey | RETAIN; no removal selected |
| 3 | source_layer | character varying | no | 192/192 | R/W: surface UP; ORM present | user_preference_matrix_pkey: PRIMARY KEY (user_id, feature_key, source_layer); index: user_preference_matrix_pkey | RETAIN; no removal selected |
| 4 | preference_weight | numeric | yes | 192/192 | R/W: surface UP; ORM present | none recorded | RETAIN; no removal selected |
| 5 | preferred_min | numeric | yes | 2/192 | R/W: surface UP; ORM present | none recorded | RETAIN; no removal selected |
| 6 | preferred_max | numeric | yes | 2/192 | R/W: surface UP; ORM present | none recorded | RETAIN; no removal selected |
| 7 | updated_at | timestamp with time zone | no | 192/192 | R/W: surface UP; ORM present | none recorded | RETAIN; no removal selected |
| 8 | raw_score | numeric | yes | 181/192 | R/W: surface UP; ORM present | none recorded | RETAIN; no removal selected |

### users - 11 columns; 100 live rows

| # | column | PostgreSQL type | nullable | populated/rows | reader/writer evidence | constraints/indexes | disposition |
| ---: | --- | --- | :---: | ---: | --- | --- | --- |
| 1 | id | character varying | no | 100/100 | R/W: surface U; ORM present | users_pkey: PRIMARY KEY (id); index: users_pkey | RETAIN; no removal selected |
| 2 | username | character varying | no | 100/100 | R/W: surface U; ORM present | index: ix_users_username | RETAIN; no removal selected |
| 3 | phone_number | character varying | no | 100/100 | R/W: surface U; ORM present | index: ix_users_phone_number | RETAIN; no removal selected |
| 4 | password_hash | character varying | no | 100/100 | R/W: surface U; ORM present | none recorded | RETAIN; no removal selected |
| 5 | role | character varying | no | 100/100 | R/W: surface U; ORM present | none recorded | RETAIN; no removal selected |
| 6 | auth_provider | character varying | no | 100/100 | R: compatibility mapper -> UserAccount -> UserOut; W: legacy 0001/register/seed only; ORM removed | none recorded | REMOVE STORAGE via 0047; retain wire projection |
| 7 | external_auth_id | character varying | yes | 0/100 | R: compatibility mapper -> UserAccount -> UserOut; W: legacy 0001/register/seed only; ORM removed | users_external_auth_id_key: UNIQUE (external_auth_id); index: users_external_auth_id_key | REMOVE STORAGE via 0047; retain wire projection |
| 8 | created_at | timestamp with time zone | no | 100/100 | R/W: surface U; ORM present | none recorded | RETAIN; no removal selected |
| 9 | updated_at | timestamp with time zone | no | 100/100 | R/W: surface U; ORM present | none recorded | RETAIN; no removal selected |
| 10 | is_active | boolean | no | 100/100 | R/W: surface U; ORM present | index: ix_users_is_active | RETAIN; no removal selected |
| 11 | auth_version | integer | no | 100/100 | R/W: surface U; ORM present | none recorded | RETAIN; no removal selected |

### wallet_transactions - 10 columns; 0 live rows

| # | column | PostgreSQL type | nullable | populated/rows | reader/writer evidence | constraints/indexes | disposition |
| ---: | --- | --- | :---: | ---: | --- | --- | --- |
| 1 | id | character varying | no | 0/0 | R/W: surface WT; ORM present | wallet_transactions_pkey: PRIMARY KEY (id); index: wallet_transactions_pkey | RETAIN; no removal selected |
| 2 | user_id | character varying | no | 0/0 | R/W: surface WT; ORM present | wallet_transactions_user_id_fkey: FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE; index: ix_wallet_transactions_user_id | RETAIN; no removal selected |
| 3 | payment_id | character varying | no | 0/0 | R/W: surface WT; ORM present | wallet_transactions_payment_id_fkey: FOREIGN KEY (payment_id) REFERENCES payments(id) ON DELETE CASCADE; index: ix_wallet_transactions_payment_id | RETAIN; no removal selected |
| 4 | transaction_type | character varying | no | 0/0 | R/W: surface WT; ORM present | none recorded | RETAIN; no removal selected |
| 5 | direction | character varying | no | 0/0 | R/W: surface WT; ORM present | none recorded | RETAIN; no removal selected |
| 6 | amount | numeric | no | 0/0 | R/W: surface WT; ORM present | none recorded | RETAIN; no removal selected |
| 7 | description | text | no | 0/0 | R/W: surface WT; ORM present | none recorded | RETAIN; no removal selected |
| 8 | method_label | character varying | yes | 0/0 | R/W: surface WT; ORM present | none recorded | RETAIN; no removal selected |
| 9 | related_booking_id | character varying | yes | 0/0 | R/W: surface WT; ORM present | wallet_transactions_related_booking_id_fkey: FOREIGN KEY (related_booking_id) REFERENCES bookings(id) ON DELETE SET NULL | RETAIN; no removal selected |
| 10 | created_at | timestamp with time zone | no | 0/0 | R/W: surface WT; ORM present | none recorded | RETAIN; no removal selected |

## SKU proof

- Full repository search found current active references only in the pre-patch inventory ORM declaration and catalog seed/helper. The remaining matches are immutable 20260412_0008 migration creation/backfill history, the new 0046 migration, and one generated snapshot phrase saying string SKUs; there is no current DTO, admin payload, API response, mobile type/mapper, repository query, dynamic ORM serializer, trigger, view, or database function using the field.
- Dynamic serialization is explicit: inventory API routes call inventory_string_to_dto(), which calls string_to_dto() and reads StringItem/InventorySnapshot fields; sku is absent. jsonable_encoder is used for validation errors only. OpenAPI contains no sku property.
- Live impact is 12/12 populated rows. The only live dependency is the inventory_items_sku_key unique constraint/btree index. No FK, trigger, view, or function references the column.

## Auth storage compatibility decision

- LoginUseCase uses phone_number, password_hash, is_active, and role. It does not branch on stored provider or external ID. Registration/seed previously wrote local; Firebase is not implemented. Live baseline counts are auth_provider 100/100 populated and all local; external_auth_id 0/100 populated.
- The patch removes persistence and current writers while retaining UserAccount, UserOut, BackendAuthUser, and mobile response shape. to_user_account() projects constant local and None, preserving deployed response compatibility without claiming external authentication exists.
- 0047 fails closed before DDL if any row has a null/non-local provider or non-null external ID. Downgrade can recreate empty columns but cannot restore deleted values; the backup is the recovery source.

## Live application result

- Fresh backup: backend/var/backups/stringsense-pre-0046-0047-20260907.dump, 204766 bytes, pg_restore --list passed, SHA-256 2aeb2ef8e3c3bfc007e74491901c99fa4624b61dd45a0799f8e3f58ae0775db5.
- Isolated PostgreSQL 16.15 restore and migration rehearsal passed from the same archive: 0045 -> 0047, 32 tables, 327 -> 324 columns, and all row counts unchanged. The rehearsal database was task-created and then dropped.
- Backend image was rebuilt as stringsense-backend:local (image ID fb44b079e27d) before the live migration. The old backend was already exited; only the rebuilt backend was restarted. Frontend and BERT were not rebuilt.
- Main stringsense received only 0046 and 0047 while backend traffic was quiesced. Final live state is head 20260907_0047, 32 application tables, 324 columns, unchanged row counts, absent target columns/constraints, and no startup row-count delta.
- Final runtime checks passed: alembic check, backend health with recommendation artifact rows=108, OpenAPI with sku absent and auth_provider/external_auth_id response fields present, and unauthenticated GET /api/auth/me returning 401. Restore the custom dump to recover discarded values.

## Validation boundary

- Pre-edit evidence: live schema/counts/constraints, full-token SKU scan, explicit serializer/API inspection, ORM shape comparison, and Graphify pre-edit query.
- Post-edit validation passed: Ruff check/format, mypy on 199 source files, and 188 tests with 2 skips. The live database is now at 0047 after the backed-up application operation.
