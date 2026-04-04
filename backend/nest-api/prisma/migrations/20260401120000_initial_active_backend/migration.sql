CREATE TYPE "UserRole" AS ENUM ('customer', 'admin', 'vendor');
CREATE TYPE "AuthProvider" AS ENUM ('local', 'firebase_future_ready');
CREATE TYPE "BookingStatus" AS ENUM (
  'pending',
  'confirmed',
  'in_progress',
  'ready_for_pickup',
  'picked_up',
  'cancelled',
  'rejected'
);

CREATE TABLE "users" (
  "id" TEXT NOT NULL,
  "phone_number" TEXT NOT NULL,
  "username" TEXT NOT NULL,
  "password_hash" TEXT NOT NULL,
  "role" "UserRole" NOT NULL DEFAULT 'customer',
  "auth_provider" "AuthProvider" NOT NULL DEFAULT 'local',
  "external_auth_id" TEXT,
  "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMP(3) NOT NULL,
  CONSTRAINT "users_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "user_profiles" (
  "id" TEXT NOT NULL,
  "user_id" TEXT NOT NULL,
  "skill_level" TEXT,
  "playing_style" TEXT,
  "budget_min" DECIMAL(10,2),
  "budget_max" DECIMAL(10,2),
  "preferred_tension" DECIMAL(4,1),
  "game_type" TEXT,
  "frequency_per_week" INTEGER,
  "pref_attack" INTEGER,
  "pref_comfort" INTEGER,
  "pref_control" INTEGER,
  "pref_durability" INTEGER,
  "pref_elasticity" INTEGER,
  "pref_sound" INTEGER,
  "pref_string_movement" INTEGER,
  "pref_tension_retention" INTEGER,
  "pref_value_for_money" INTEGER,
  "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMP(3) NOT NULL,
  CONSTRAINT "user_profiles_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "strings" (
  "id" TEXT NOT NULL,
  "brand" TEXT NOT NULL,
  "model_name" TEXT NOT NULL,
  "normalized_name" TEXT NOT NULL,
  "price_rm" DECIMAL(10,2),
  "attack" DECIMAL(4,2),
  "comfort" DECIMAL(4,2),
  "control" DECIMAL(4,2),
  "durability" DECIMAL(4,2),
  "elasticity" DECIMAL(4,2),
  "sound" DECIMAL(4,2),
  "string_movement" DECIMAL(4,2),
  "tension_retention" DECIMAL(4,2),
  "value_for_money" DECIMAL(4,2),
  "beginner_fit_score" DECIMAL(4,2),
  "stability_score" DECIMAL(4,2),
  "all_round_score" DECIMAL(4,2),
  "source_item_id" TEXT,
  "source_url" TEXT,
  "is_active" BOOLEAN NOT NULL DEFAULT true,
  "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMP(3) NOT NULL,
  CONSTRAINT "strings_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "bookings" (
  "id" TEXT NOT NULL,
  "user_id" TEXT NOT NULL,
  "string_id" TEXT NOT NULL,
  "racket_brand" TEXT,
  "racket_model" TEXT,
  "requested_tension" DECIMAL(4,1),
  "drop_off_datetime" TIMESTAMP(3),
  "notes" TEXT,
  "status" "BookingStatus" NOT NULL DEFAULT 'pending',
  "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMP(3) NOT NULL,
  CONSTRAINT "bookings_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "booking_status_history" (
  "id" TEXT NOT NULL,
  "booking_id" TEXT NOT NULL,
  "old_status" "BookingStatus",
  "new_status" "BookingStatus" NOT NULL,
  "changed_by_user_id" TEXT,
  "changed_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "booking_status_history_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "recommendation_logs" (
  "id" TEXT NOT NULL,
  "user_id" TEXT,
  "profile_snapshot_json" JSONB NOT NULL,
  "recommendation_result_json" JSONB NOT NULL,
  "algorithm_version" TEXT NOT NULL,
  "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "recommendation_logs_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX "users_phone_number_key" ON "users"("phone_number");
CREATE UNIQUE INDEX "users_external_auth_id_key" ON "users"("external_auth_id");
CREATE UNIQUE INDEX "user_profiles_user_id_key" ON "user_profiles"("user_id");
CREATE UNIQUE INDEX "strings_normalized_name_key" ON "strings"("normalized_name");

ALTER TABLE "user_profiles"
  ADD CONSTRAINT "user_profiles_user_id_fkey"
  FOREIGN KEY ("user_id") REFERENCES "users"("id")
  ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "bookings"
  ADD CONSTRAINT "bookings_user_id_fkey"
  FOREIGN KEY ("user_id") REFERENCES "users"("id")
  ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "bookings"
  ADD CONSTRAINT "bookings_string_id_fkey"
  FOREIGN KEY ("string_id") REFERENCES "strings"("id")
  ON DELETE RESTRICT ON UPDATE CASCADE;

ALTER TABLE "booking_status_history"
  ADD CONSTRAINT "booking_status_history_booking_id_fkey"
  FOREIGN KEY ("booking_id") REFERENCES "bookings"("id")
  ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "booking_status_history"
  ADD CONSTRAINT "booking_status_history_changed_by_user_id_fkey"
  FOREIGN KEY ("changed_by_user_id") REFERENCES "users"("id")
  ON DELETE SET NULL ON UPDATE CASCADE;

ALTER TABLE "recommendation_logs"
  ADD CONSTRAINT "recommendation_logs_user_id_fkey"
  FOREIGN KEY ("user_id") REFERENCES "users"("id")
  ON DELETE SET NULL ON UPDATE CASCADE;
