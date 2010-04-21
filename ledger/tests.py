from django.test import TestCase
from ledger.demo import setup_demo
from ledger.models import Account, Exchange
import datetime

ledger_account_view_sql="""
CREATE LANGUAGE plpgsql;
CREATE OR REPLACE VIEW ordered_transaction AS
SELECT
	id,
	credit_id,
	debit_id,
	ROUND(amount * quantity, 2) AS total
FROM ledger_transaction
ORDER BY date, exchange_id, id;

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
	
"""

class TestLedgerCalculation(TestCase):
    def setUp(self):
        setup_demo()
        from django.db import connection, transaction
        cursor = connection.cursor()
        # Data modifying operation - commit required
        cursor.execute(ledger_account_view_sql)
        transaction.commit_unless_managed()


    """"
    def testLogin(self):
        assert self.client.login(username='andy', password='andy')
        response = self.client.get('/clients/ledger/account/13/')
        self.assertContains(response, '$43,315.00')
    """

    def calculate_balance(self, **kw):
        a = Account.objects.get(**kw)
        old_balances_result = [t.balance for t in a.get_transactions()]
        new_balances_result = [s.balance for s in a.get_transaction_views()]
        print "*"*100, old_balances_result
        print "x"*100, new_balances_result
        self.assertEqual(old_balances_result,new_balances_result)

    def test_account_receivable_calculation(self):
        self.calculate_balance(name='Accounts Receivable', editor__username='andy')

    def test_counsulting_calculation(self):
        self.calculate_balance(name='Consulting', editor__username='andy')

    def test_income_calulation(self):
        today = datetime.date.today()
        to_date=today
        from_date = today.replace(month=1,day=1)
        from django.contrib.auth.models import User
        user_id = User.objects.get(username='andy').id
        income =  Account.sum_by_type(user_id=user_id, account_type='income', from_date=from_date, to_date=to_date)
        print "i"*100, income
        _income =  Account.sum_by_type_old(user_id=user_id, account_type='income', from_date=from_date, to_date=to_date)
        self.assertEqual(income, _income)

    def test_refactor_exchange(self):
        old_value = [e.old_total for e in Exchange.objects.all()]
        value = [e.total for e in Exchange.objects.all()]
        print "o"*100, old_value
        print "v"*100, value
        self.assertEqual(old_value, value)
