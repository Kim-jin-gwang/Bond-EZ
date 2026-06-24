ALTER TABLE "BaseRate"
ADD COLUMN IF NOT EXISTS base_date DATE;

UPDATE "BaseRate"
SET base_date = COALESCE(base_date, CURRENT_DATE)
WHERE base_date IS NULL;

ALTER TABLE "BaseRate"
ALTER COLUMN base_date SET NOT NULL;

ALTER TABLE "BaseRate"
ALTER COLUMN base_date SET DEFAULT CURRENT_DATE;

ALTER TABLE "BaseRate"
DROP CONSTRAINT IF EXISTS base_rate_country_unique;

ALTER TABLE "BaseRate"
DROP CONSTRAINT IF EXISTS base_rate_country_date_unique;

ALTER TABLE "BaseRate"
ADD CONSTRAINT base_rate_country_date_unique UNIQUE(country_id, base_date);
