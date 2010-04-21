# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# $Id: models.py 460 2009-11-02 14:09:00Z copelco $
# ----------------------------------------------------------------------------
#
#    Copyright (C) 2008 Caktus Consulting Group, LLC
#
#    This file is part of minibooks.
#
#    minibooks is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of 
#    the License, or (at your option) any later version.
#    
#    minibooks is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#    
#    You should have received a copy of the GNU Affero General Public License
#    along with minibooks.  If not, see <http://www.gnu.org/licenses/>.
#



try:
    from dateutil.relativedelta import relativedelta
except ImportError:
    raise ImportError('minibooks was unable to import the dateutil library. Please confirm it is installed and available on your current Python path.')

from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User 

from caktus.django.db.util import slugify_uniquely

from crm import models as crm

from timepiece import models as timepiece

class Account(models.Model):
    """
    Accounts for use in your business chart of accounts
    
    There will normally be far more expense accounts than any other type of account.
    
    The information which you collect in your income accounts will be used to prepare your profit and loss statements periodically.
    Profit and loss statement = income and expense statement
    
    phone - Telephone expenses
    google - Advertising expenses
    celito - 
    business meals and lodging
    business insurance
    charitable contributions
    auto expenses
    server expenses
    
    Asset and liability accounts are collectively referred to as balance sheet accounts
        Accounts receivable (current asset)
        Bank checking account (current asset)
        
        Accounts payable (current debt)
        Equipement (fixed asset)
    """
    
    ACCOUNT_TYPES = (
        ('income', 'Income' ),
        ('expense', 'Expense' ),
        ('asset','Asset'),
        ('liability', 'Liability'),
        ('equity', 'Equity'),
    )
    
    name = models.CharField(max_length=255)
    number = models.IntegerField() # how do I unique this per user? per company? per ,menbership
    type = models.CharField(max_length=15, choices=ACCOUNT_TYPES)
    editor = models.ForeignKey(User)
    edited_at = models.DateTimeField(editable=False, auto_now=True)

    class Meta:
        #FIXME: should apply this to menbership or company level?
        #unique_together = (('name','number','editor'),
                           #('name','number','updated_by'))
        pass


    @property
    def debit_total(self):
        related_transactions = self.debits.all()
        total = sum([t.amount * t.quantity for t in related_transactions])
        return total

    @property
    def credit_total(self):
        related_transactions = self.credits.all()
        total = sum([t.amount * t.quantity for t in related_transactions])
        return total


    def balance(self):
        if self.type in ('asset', 'expense', 'equity',):
            return self.debit_total - self.credit_total
        else:
            return self.credit_total - self.debit_total
    
    def _difference(self, debit_amt, credit_amt):
        if self.type in ('asset', 'expense', 'equity',):
            return debit_amt - credit_amt
        else:
            return credit_amt - debit_amt
        
    def _total(self, type=None, reconciled=None, **kwargs):
        if type in ('credit', 'debit'):
            kwargs[type] = self
            if reconciled is not None:
                kwargs['%s_reconciled' % type] = reconciled
        else:
            raise Exception('Invalid type %s' % type)
        kwargs['editor'] = self.editor
        
        return Transaction.sum(**kwargs)
    
    def reconciled_balance(self, to_date=None):
        debit_total = self._total('debit', reconciled=True, to_date=to_date)
        credit_total = self._total('credit', reconciled=True, to_date=to_date)
        return self._difference(debit_total, credit_total)
    
    def debit_total_for_project(self, project_id=None):
        return self._total('debit', project_id=project_id)
        
    def credit_total_for_project(self, project_id=None):
        return self._total('credit', project_id=project_id)    
    
    def total_for_date_range(self, from_date=None, to_date=None):
        debit_total = self._total('debit', from_date=from_date, to_date=to_date)
        credit_total = self._total('credit', from_date=from_date, to_date=to_date)
        return self._difference(debit_total, credit_total)
    
    def get_transaction_views(self, from_date=None, to_date=None):
        debits = self.debits.all()
        credits = self.credits.all()
        if from_date:
            debits = debits.filter(date__gte=from_date)
            credits = credits.filter(date__gte=from_date)
        if to_date:
            debits = debits.filter(date__lte=to_date)
            credits = credits.filter(date__lte=to_date)

        all_debits = [TranscationView(t, as_debit=True) for t in debits]
        all_credits = [TranscationView(t, as_debit=False) for t in credits]
        transaction_views = (all_debits + all_credits)
        transaction_views.sort()

        balance = 0

        if self.type in ('asset', 'expense', 'equity',):
            for i,tv in enumerate(transaction_views):
                if tv.as_debit:
                    balance += tv.transaction.total
                else:
                    balance -= tv.transaction.total
                transaction_views[i].balance = balance
        else:
            for i,tv in enumerate(transaction_views):
                if tv.as_debit:
                    balance -= tv.transaction.total
                else:
                    balance += tv.transaction.total
                transaction_views[i].balance = balance

        return transaction_views

    
    @classmethod
    def sum_by_type(cls, user_id, account_type, from_date, to_date):
        editor = User.objects.get(pk=user_id)
        type_accounts = Account.objects.filter(type=account_type, editor=editor)

        debit_sum_all = 0
        credit_sum_all = 0
        for account in type_accounts:
            transaction_views =  account.get_transaction_views(from_date=from_date, to_date=to_date)
            debit_sum_in_this_account = 0
            credit_sum_in_this_account = 0
            for tv in transaction_views:
                if tv.as_debit:
                    debit_sum_in_this_account += tv.total
                else:
                    credit_sum_in_this_account += tv.total

            debit_sum_all += debit_sum_in_this_account
            credit_sum_all += credit_sum_in_this_account

        if account_type in ('asset', 'expense', 'equity',):
            result = debit_sum_all - credit_sum_all
        else:
            result = credit_sum_all - debit_sum_all

        return result

    class Meta:
        ordering = ('type', 'name',)
        permissions = (
            ('view_account', 'Can view account'),
            ('view_account_reports', 'Can view account reports'),
            ('transfer_funds', 'Can transfer funds')
        )

    def __unicode__(self):
        return "%i - %s (%s)" % (self.number, self.name, self.type)

class TranscationView(object):
    def __init__(self, transaction, as_debit=False): #default as credit
        self.transaction = transaction
        self.as_debit = as_debit
        self.balance = 0

    def __cmp__(self, other):
        if self.transaction.exchange and other.transaction.exchange:
            by_exchange = cmp(self.transaction.exchange.id, other.transaction.exchange.id)
        else:
            by_exchange = 0
        return cmp(self.transaction.date, other.transaction.date)\
               or by_exchange\
               or cmp(self.transaction.id, other.transaction.id)

    def __getattr__(self,attr):
        return getattr(self.transaction, attr)



class ExchangeType(models.Model):
    """
    Links exchanges to default accounts
    """
    
    label = models.CharField(max_length=100) #FIXME: unique together with User
    slug = models.CharField(max_length=100) #FIXME: unique ?
    debit = models.ForeignKey(
        Account,
        null=True,
        blank=True,
        related_name='debit_exchange_types',
    )
    credit = models.ForeignKey(
        Account,
        null=True,
        blank=True,
        related_name='credit_exchange_types',
    )
    common_account = models.ForeignKey(
        Account,
        null=True,
        blank=True,
        related_name='common_account_exchange_types',
    )
    deliverable = models.BooleanField(default=False)
    
    business_types = models.ManyToManyField(
        crm.BusinessType,
        related_name='exchange_types',
    )

    editor = models.ForeignKey(User)
    edited_at = models.DateTimeField(editable=False, auto_now=True)

    class Meta:
        ordering = ('label',)
    
    def save(self):
        queryset = ExchangeType.objects.filter(editor=self.editor)
        if self.id:
            queryset = queryset.exclude(id__exact=self.id)
        self.slug = slugify_uniquely(self.label, queryset, 'slug')
        super(ExchangeType, self).save()
    
    def debit_or_credit(self):
        if self.common_account:
            if self.debit is None:
                return 'debit'
            elif self.credit is None:
                return 'credit'
            else:
                raise ValueError('common_account must take the place of the debit or credit account in ExchangeType')
        return None

    @property
    def exchange_count(self):
        return self.exchanges.count()


    def _get_credit_accounts(self, base_account):
        # TODO make this stuff part of the data model
        if base_account and self.slug == 'invoice':
            qs = Account.objects.filter(editor=self.editor).filter(Q(type='income') | Q(type='expense'))
        elif base_account and self.slug == 'purchase':
            qs = Account.objects.filter(editor=self.editor).filter(Q(type='liability') | Q(type='asset'))
        elif base_account:
            qs = Account.objects.filter(editor=self.editor).filter(type=base_account.type)
        else:
            qs = Account.objects.none()
        return qs
    credit_accounts = property(
        lambda self: self._get_credit_accounts(self.credit)
    )

    def _get_debit_accounts(self, base_account):
        if base_account and self.slug == 'purchase-credit':
            qs = Account.objects.filter(editor=self.editor).filter(Q(type='liability') | Q(type='asset'))
        elif base_account:
            qs = Account.objects.filter(editor=self.editor).filter(type=base_account.type)
        else:
            qs = Account.objects.none()
        return qs
    debit_accounts = property(
        lambda self: self._get_debit_accounts(self.debit)
    )
    
    def _get_common_accounts(self):
        if self.debit:
            qs = self._get_credit_accounts(self.common_account)
        elif self.credit:
            qs = self._get_debit_accounts(self.common_account)
        else:
            qs = Account.objects.none()
        return qs
    common_accounts = property(_get_common_accounts)
    
    def __unicode__(self):
        return self.label


class RepeatPeriod(models.Model):
    INTERVAL_CHOICES = (
        ('day', 'Day(s)'),
        ('week', 'Week(s)'),
        ('month', 'Month(s)'),
        ('year', 'Year(s)'),
    )
    active = models.BooleanField(default=False)
    count = models.PositiveSmallIntegerField(null=True, blank=True, choices=[(x,x) for x in range(1,32)])
    interval = models.CharField(null=True, blank=True, max_length=10, choices=INTERVAL_CHOICES)
    editor = models.ForeignKey(User, related_name='user_ledger_repeateperiod_set')
    edited_at = models.DateTimeField(editable=False, auto_now=True)




    def delta(self):
        return relativedelta(**{str(self.interval + 's'): self.count})


class Exchange(models.Model):
    """ Collection of specific transactions """
    
    business = models.ForeignKey(crm.Contact, related_name="exchanges")
    type = models.ForeignKey(ExchangeType, related_name='exchanges')
    memo = models.TextField(null=True, blank=True)
    date = models.DateField()
    date_due = models.DateField(null=True, blank=True)
    delivered = models.BooleanField(default=False)
    
    repeat_period = models.ForeignKey(RepeatPeriod, null=True, blank=True, related_name='exchanges')
    editor = models.ForeignKey(User)
    edited_at = models.DateTimeField(editable=False, auto_now=True)

    def previous_project_balance(self):
        if self.transactions.all().count() > 0:
            return self.transactions.all()[0].previous_project_balance()
        
    def new_project_balance(self):
        if self.type.slug == 'receipt':
            return self.previous_project_balance() - self.total
        elif self.type.slug == 'invoice':
            return self.previous_project_balance() + self.total
    
    def get_common_account(self):
        if self.transactions.all().count() > 0 and self.type.debit_or_credit():
            return getattr(self.transactions.all()[0], self.type.debit_or_credit())
        else:
            return None
        
    def get_project(self):
        if self.transactions.all().count() > 0:
            return self.transactions.all()[0].project
        else:
            return None
    
    def subtotal(self):
        return self.total

    @property
    def total(self):
        return sum([t.total for t in self.transactions.all()])

    @property
    def reconciled(self):
        rs = [(t.debit_reconciled or t.credit_reconciled) for t in self.transactions.all()]
        for r in rs:
            if r:
                return r
        return False

    class Meta:
        ordering = ('-date', '-id', 'type',)
        permissions = (
            ('view_exchange', 'Can view exchange'),
            ('email_exchange', 'Can email exchange'),
        )

    def __unicode__(self):
        if self.id:
            return "%s: %s" % (self.type, self.memo)
        else:
            return unicode(self.memo)


class Transaction(models.Model):
    date = models.DateField()
    debit = models.ForeignKey(Account, related_name='debits')
    credit = models.ForeignKey(Account, related_name='credits')
    project = models.ForeignKey(timepiece.Project, null=True, related_name='transactions')
    exchange = models.ForeignKey(Exchange, null=True, related_name='transactions')
    
    memo = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    debit_reconciled = models.BooleanField()
    credit_reconciled = models.BooleanField()
    editor = models.ForeignKey(User)
    edited_at = models.DateTimeField(editable=False, auto_now=True)

    @property
    def total(self):
        return self.amount * self.quantity


    def previous_project_balance(self):
        billed = Transaction.sum(
            project_id=self.project.id,
            before=self,
            exchange_type=ExchangeType.objects.get(slug='invoice', editor=self.editor),
        )
        paid = Transaction.sum(
            project_id=self.project.id,
            before=self,
            exchange_type=ExchangeType.objects.get(slug='receipt', editor=self.editor),
        )
        return billed - paid
    
    def new_project_balance(self):
        return self.previous_project_balance() + self.total
    
    @classmethod #it's ok although it's a class method?
    def sum(cls, 
        debit=None, 
        credit=None, 
        project_id=None, 
        debit_reconciled=None, 
        credit_reconciled=None, 
        from_date=None, 
        to_date=None,
        before=None,
        exchange_type=None,
        editor = None
      ):
        args = []
        where = []
        join = []

        if debit:
            q_debit = Q(debit=debit)
        else:
            q_debit = Q()

        if credit:
            q_credit = Q(credit=credit)
        else:
            q_credit = Q()

        if project_id:
            q_project = Q(project__id=project_id)
        else:
            q_project = Q()

        if from_date:
            q_from_date = Q(date__gte=from_date)
        else:
            q_from_date = Q()

        if to_date:
            q_to_date = Q(date__lte=to_date)
        else:
            q_to_date = Q()

        if debit_reconciled:
            q_debit_reconciled = Q(debit_reconciled=debit_reconciled)
        else:
            q_debit_reconciled = Q()

        if credit_reconciled:
            q_credit_reconciled = Q(credit_reconciled=credit_reconciled)
        else:
            q_credit_reconciled = Q()

        if exchange_type:
            q_exchange_type = Q(exchange__type=exchange_type)
        else:
            q_exchange_type = Q()

        if before:
            q1 = Q(exchange__date__lt=before.exchange.date)
            q2 = Q(exchange__date=before.exchange.date) & Q(exchange__id__lt=before.exchange.id)
            q3 = Q(exchange__date=before.exchange.date) & Q(exchange__id=before.exchange.id) & Q(date__lt=before.date)
            q4 = Q(exchange__date=before.exchange.date) & Q(exchange__id=before.exchange.id) & Q(date=before.date) & Q(id__lt=before.id)
            q_before = q1|q2|q3|q4
        else:
            q_before = Q()

        if editor:
            q_editor = Q(editor=editor)
        else:
            q_editor = Q()

        trans = Transaction.objects.filter(q_debit, q_credit, q_project, q_from_date, q_to_date, q_debit_reconciled, q_credit_reconciled,
                                           q_exchange_type, q_before, q_editor
                                          )
        trans_sum = sum([t.amount * t.quantity for t in trans])

        return trans_sum

    def reconciled(self):
        return (self.debit_reconciled or self.credit_reconciled)
    
    def __unicode__(self):
        return '%s: %s (%s)' % (self.date, self.memo, self.amount)
        
    class Meta:
        ordering = ('exchange__date', 'exchange__id', 'date', 'id',)


def install_user_initial_fixtures(instance, created, **kwargs):
    #ok, args name here *MUST* be 'instance', 'created', '**kwargs', otherwise it will *NOT* work
    user = instance
    user_created = created
    if not user_created:
        return
    #install accounts and exchange_types after creating user

    
    
    account_list = (
        (1060, 'Checking', 'asset'),
        (1200, 'Accounts Receivable', 'asset'),
        (1300, 'Owner Draws', 'asset'),
        (2100, 'Accounts Payable', 'liability'),
        (2200, 'Credit Card', 'liability'),
        (4020, 'Consulting', 'income'),
        (5020, 'General Expenses', 'expense'),
        (5615, 'Advertising & Promotions', 'expense'),
        (5620, 'Telephone', 'expense'),
        (5685, 'Insurance', 'expense'),
        (5695, 'Internet', 'expense'),
    )    
    
    exchange_type_list = (
        ('Invoice',  None, 4020, 1200),
        ('Receipt',  1060, None, 1200),
        ('Order',    5020, None, 2100),
        ('Payment',  None, 1060, 2100),
        ('Paycheck',  1060, None, 1300),
        ('Purchase', 5020, None, 1060),
        ('Purchase Credit', None, 5020, 2200),
        ('Credit Card Payment', None, 1060, 2200),
    )
    
    for number, name, type in account_list:
        Account(number=number, name=name, type=type, editor=user).save()
    
    for label, debit, credit, common_account in exchange_type_list:
        tt = ExchangeType(label=label, editor=user)
        if debit is not None:
            tt.debit = Account.objects.get(number=debit, editor=user)
        if credit is not None:
            tt.credit = Account.objects.get(number=credit, editor=user)
        if common_account is not None:
            tt.common_account = Account.objects.get(number=common_account, editor=user)
        tt.save()

    business_types = (
        ('Vendor', 
            ('purchase', 'order', 'payment', 'purchase-credit',), 
            True,
        ),
        ('Client', 
            ('invoice', 'receipt',),
            False,
        ),
        ('Member', 
            ('paycheck',),
            False,
        ),
        ('Creditor', 
            ('credit-card-payment',),
            False,
        ),
    )
    
    for name, exchange_type_slugs, view_all_projects in business_types:
        bt = crm.BusinessType.objects.create(
            name=name,
            can_view_all_projects=view_all_projects,
            editor = user
        )
        for slug in exchange_type_slugs:
            bt.exchange_types.add(ExchangeType.objects.get(slug=slug, editor=user))
    
    #print 'Accounts and Exchange Types for %s successfully loaded' % user.username

from django.db.models import signals
signals.post_save.connect(install_user_initial_fixtures, sender=User)

def auto_create_dummy_project(instance, created, **kwargs):
    if not created:
        return None
    contact = instance
    contact_id  = contact.id
    dummy_word = 'dummy_project_%d' % contact.id
    dummy_project = timepiece.Project.objects.create(
        name=dummy_word,
        type='_type',
        status='accepted',
        description=dummy_word,
        business=contact,
        point_person=contact.editor,
        editor=contact.editor
    )

    dummy_relationship_word = 'dummy_project_relationship_%d' % contact.id
    timepiece.ProjectRelationship.objects.create(
        contact=contact,
        project=dummy_project,
        editor=contact.editor
    )
    #TODO edito should have ProjectRelationship automatically?
    return True

signals.post_save.connect(auto_create_dummy_project, sender=crm.Contact)
