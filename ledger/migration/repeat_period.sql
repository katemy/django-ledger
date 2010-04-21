ALTER TABLE ledger_exchange ADD COLUMN "repeat_period_id" integer NULL REFERENCES "ledger_repeatperiod" ("id") DEFERRABLE INITIALLY DEFERRED;
