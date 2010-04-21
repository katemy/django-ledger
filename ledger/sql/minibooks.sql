-- -*- coding: utf-8 -*-
-- ----------------------------------------------------------------------------
-- $Id: minibooks.sql 456 2009-10-09 17:28:43Z tobias $
-- ----------------------------------------------------------------------------
--
--    Copyright (C) 2008 Caktus Consulting Group, LLC
--
--    This file is part of minibooks.
--
--    minibooks is free software: you can redistribute it and/or modify
--    it under the terms of the GNU Affero General Public License as
--    published by the Free Software Foundation, either version 3 of 
--    the License, or (at your option) any later version.
--    
--    minibooks is distributed in the hope that it will be useful,
--    but WITHOUT ANY WARRANTY; without even the implied warranty of
--    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
--    GNU Affero General Public License for more details.
--    
--    You should have received a copy of the GNU Affero General Public License
--    along with minibooks.  If not, see <http://www.gnu.org/licenses/>.
--


DROP VIEW ordered_transaction CASCADE;
CREATE OR REPLACE VIEW ordered_transaction AS
SELECT
	id,
	credit_id,
	debit_id,
	ROUND(amount * quantity, 2) AS total
FROM ledger_transaction
ORDER BY date, exchange_id, id;

DROP FUNCTION running_balance() CASCADE;
CREATE FUNCTION running_balance(
	OUT account_id integer,
	OUT transaction_id integer,
	OUT credit_balance numeric(10,2),
	OUT debit_balance numeric(10,2)
) RETURNS SETOF record AS $$
DECLARE
	transaction		record;
	account			record;
BEGIN
	FOR account IN SELECT id FROM ledger_account LOOP
		account_id := account.id;
		credit_balance := 0;
		debit_balance := 0;
		FOR transaction IN (SELECT * FROM ordered_transaction t WHERE t.debit_id=account_id OR t.credit_id=account_id) LOOP
			transaction_id = transaction.id;
			IF transaction.debit_id = account_id THEN
				debit_balance := debit_balance + transaction.total;
			ELSE
				credit_balance := credit_balance + transaction.total;
			END IF;
			RETURN NEXT;
		END LOOP;
	END LOOP;
	RETURN;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE VIEW ledger_account_balance AS
SELECT * FROM running_balance();
	
