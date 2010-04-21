ALTER TABLE ledger_transaction ADD COLUMN date date;
UPDATE ledger_transaction SET date = ledger_exchange.date FROM ledger_exchange WHERE ledger_transaction.exchange_id = ledger_exchange.id;
ALTER TABLE ledger_transaction ALTER COLUMN date SET NOT NULL;

DROP VIEW ordered_transaction CASCADE;
CREATE OR REPLACE VIEW ordered_transaction AS
SELECT
	id,
	credit_id,
	debit_id,
	ROUND(amount * quantity, 2) AS total
FROM ledger_transaction
ORDER BY date, exchange_id, id;
