ALTER TABLE ledger_exchangetype ADD COLUMN "deliverable" boolean;
UPDATE ledger_exchangetype SET deliverable = false;
ALTER TABLE ledger_exchangetype ALTER COLUMN deliverable SET NOT NULL;
UPDATE ledger_exchangetype SET deliverable = true WHERE label IN ('Invoice', 'Receipt', 'Paycheck');

ALTER TABLE ledger_exchange ADD COLUMN "delivered" boolean;
UPDATE ledger_exchange SET delivered = false;
ALTER TABLE ledger_exchange ALTER COLUMN delivered SET NOT NULL;

-- UPDATE
--     ledger_exchange exchange
-- SET
--     delivered = true
-- FROM
--     ledger_exchangetype type
-- WHERE
--     type.deliverable = true
--     AND exchange.date < '2009-01-01'
--     AND (exchange.type_id = type.id);