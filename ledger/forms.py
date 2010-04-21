# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# $Id: forms.py 473 2009-11-17 02:40:08Z copelco $
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

import datetime

from django import forms
from django.forms.models import inlineformset_factory, BaseInlineFormSet, save_instance
from django.forms.formsets import DELETION_FIELD_NAME

from caktus.decorators import requires_kwarg
from caktus.django.forms import RequestModelForm, RequestForm
from caktus.django.widgets import MooDate

import ledger.models as ledger

from crm import models as crm
from crm.forms import DateInput


class DateForm(RequestForm):
    from_date = forms.DateField(label="From", widget=MooDate(), required=False)
    to_date = forms.DateField(label="To", widget=MooDate(), required=False)
    
    def save(self):
        return (
            self.cleaned_data.get('from_date', ''),
            self.cleaned_data.get('to_date', ''),
        )


class SingleDateForm(RequestForm):
    date = forms.DateField(
        label='Date',
        widget=MooDate(),
        required=False,
    )

    def save(self):
        return self.cleaned_data.get('date', '')


class RepeatPeriodForm(RequestModelForm):
    class Meta:
        model = ledger.RepeatPeriod
        fields = ('active', 'count', 'interval',)
    
    def __init__(self, *args, **kwargs):
        super(RepeatPeriodForm, self).__init__(*args, **kwargs)
    
    def _clean_optional(self, name):
        active = self.cleaned_data.get(name, False)
        value = self.cleaned_data.get(name, '')
        if active and not value:
            raise forms.ValidationError('This field is required.')
        return self.cleaned_data[name]
    
    def clean_count(self):
        return self._clean_optional('count')
    
    def clean_interval(self):
        return self._clean_optional('interval')

    def save(self, commit=True):
        instance = super(RepeatPeriodForm, self).save(commit=False)
        instance.editor = self.user
        instance.save()
        return instance

class ExchangeTypeForm(RequestModelForm):
    class Meta:
        model = ledger.Exchange
        fields = ('type',)
    
    def __init__(self, *args, **kwargs):
        super(ExchangeTypeForm, self).__init__(*args, **kwargs)
        self.fields['type'] = forms.ModelChoiceField(
            queryset=ledger.ExchangeType.objects.filter(editor=self.request.user).exclude(
                id=self.instance.type.id
            )
        )


class ExchangeForm(RequestModelForm):
    
    class Meta:
        model = ledger.Exchange
        fields = ('business', 'memo', 'date', 'date_due', 'delivered',)
    
    @requires_kwarg('exchange_type')
    def __init__(self, *args, **kwargs):
        self.exchange_type = kwargs.pop('exchange_type')

        super(ExchangeForm, self).__init__(*args, **kwargs)
        
        self.fields.keyOrder = []
        if self.request.business:
            self.fields.pop('business')
            business_types = self.request.business.business_types.all()
        else:
            self.fields.keyOrder.append('business')
            business_types = crm.BusinessType.objects.filter(
                exchange_types=self.exchange_type
            )
            self.fields['business'].queryset = crm.Contact.objects.filter(
                type='business',
                business_types__in=business_types,
            )
            #TODO: only show business type that make sense of exchange type
            self.fields['business'].queryset = crm.Contact.objects.filter(
                type='business',
                editor=self.request.user,
            )
            if business_types.count() == 1:
                self.fields['business'].label = business_types[0].name
        
        
        self.fields['memo'].widget = forms.Textarea(
            attrs={'rows': 4, 'cols': 25},
        )
        self.fields['date'].initial = datetime.date.today()
        self.fields['date'].widget = DateInput()
        self.fields['date_due'].widget = DateInput()
        self.fields['date_due'].required = False
        self.fields.keyOrder += ['memo', 'date', 'date_due',]
        
        if self.exchange_type.deliverable:
            self.fields.keyOrder.append('delivered')
        else:
            self.fields.pop('delivered')
        
        debit_or_credit = self.exchange_type.debit_or_credit()
        if self.exchange_type.common_account:
            if self.exchange_type.common_accounts:
                common_account_querset = self.exchange_type.common_accounts.filter(editor=self.user)
            else:
                common_account_querset = self.exchange_type.common_accounts #it's actually []

            self.fields[debit_or_credit] = forms.ModelChoiceField(
                queryset=common_account_querset,
                initial=self.exchange_type.common_account.id,
            )
        if self.instance.id and self.instance.transactions.count() > 0:
            first_transaction = self.instance.transactions.all()[0]
            value = getattr(first_transaction, debit_or_credit)
            self.fields[debit_or_credit].initial = value.id
            
    def save(self, commit=True):
        instance = super(ExchangeForm, self).save(commit=False)
        if self.request.business:
            instance.business = self.request.business
        instance.type = self.exchange_type
        instance.editor = self.user
        instance.save(commit)        
        return instance


class BaseTransactionFormSet(BaseInlineFormSet):
    @requires_kwarg('exchange_type')
    def __init__(self, *args, **kwargs):
        self.exchange_type = kwargs.pop('exchange_type')
        self.user = kwargs.pop('user')
        super(BaseTransactionFormSet, self).__init__(*args, **kwargs)
    
    def save_existing(self, form, instance, commit=True):
        # ignore amount and quantity from POSTed transaction if reconciled
        exclude = [self._pk_field.name]
        if instance.id and instance.reconciled():
            exclude.extend((
                'amount',
                'quantity',
                'debit_reconciled',
                'credit_reconciled',
            ))
        return save_instance(form, instance, exclude=exclude, commit=commit)
    
    def add_fields(self, form, index):
        super(BaseTransactionFormSet, self).add_fields(form, index)
        form.fields.pop('project')
        
        if index == 0:
            form.fields['date'].initial = datetime.date.today()
        form.fields['date'].widget = DateInput()
        form.fields['memo'].widget = forms.TextInput()
        form.fields['debit_reconciled'].widget = forms.CheckboxInput(
            attrs={'disabled':'disabled'}
        )
        form.fields['credit_reconciled'].widget = forms.CheckboxInput(
            attrs={'disabled':'disabled'}
        )
        
        # disable count and rate fields if transaction is reconciled
        attrs = {}
        if form.instance.id and form.instance.reconciled():
            attrs = {'disabled':'disabled'}
            form.fields['quantity'].required = False
            form.fields['amount'].required = False
            form.fields[DELETION_FIELD_NAME].widget = forms.HiddenInput()
        form.fields['quantity'].widget = forms.TextInput(attrs=attrs)
        form.fields['amount'].widget = forms.TextInput(attrs=attrs)
        
        if self.exchange_type.credit:
            credit_accounts = self.exchange_type.credit_accounts.filter(editor=self.user)
            form.fields['credit'].queryset = credit_accounts
            form.fields['credit'].initial = self.exchange_type.credit.id
        else:
            form.fields.pop('credit')
        
        if self.exchange_type.debit:
            debit_accounts = self.exchange_type.debit_accounts.filter(editor=self.user)
            form.fields['debit'].queryset = debit_accounts
            form.fields['debit'].initial = self.exchange_type.debit.id
        else:
            form.fields.pop('debit')


class TransactionForm(forms.ModelForm):
    class Meta:
        model = ledger.Transaction
        exclude = ('editor',)
        
    def clean(self):
        if (self.instance.id
            and self.instance.reconciled()
            and DELETION_FIELD_NAME in self.cleaned_data
            and self.cleaned_data[DELETION_FIELD_NAME]
          ):
            raise forms.ValidationError(
                'Reconciled transactions cannot be deleted'
            )
        return self.cleaned_data


TransactionFormSet = inlineformset_factory(
    ledger.Exchange,
    ledger.Transaction,
    formset=BaseTransactionFormSet,
    form=TransactionForm,
)


class AccountForm(forms.ModelForm):
    """
    Model form for creating and editing ledger accounts.
    """
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(AccountForm, self).__init__(*args, **kwargs)

    class Meta:
        model = ledger.Account
        fields = ('name', 'number', 'type',)

    def save(self, *args, **kwargs):
        instance = super(AccountForm, self).save(commit=False)
        instance.editor = self.user
        instance.save()
        return instance



class SearchForm(forms.Form):
    search = forms.CharField(required=False)


class ReconcileTransactionForm(forms.Form):
    ACCOUNTS = (
        ('debit', 'Debit',),
        ('credit', 'Credit',),
    )
    account = forms.ChoiceField(choices=ACCOUNTS)
    transaction = forms.ModelChoiceField(
        queryset=ledger.Transaction.objects.all(),
    )
    to_date = forms.DateField(required=False)


class TransferForm(forms.ModelForm):
    class Meta:
        model = ledger.Transaction
        fields = ('credit', 'debit', 'amount', 'date',)
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(TransferForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ('credit', 'debit', 'date', 'amount',)
        self.fields['debit'].label = 'To'
        self.fields['debit'].queryset = ledger.Account.objects.filter(editor=self.user)
        self.fields['credit'].label = 'From'
        self.fields['credit'].queryset = ledger.Account.objects.filter(
            type__in=('asset', 'liability'),
            editor=self.user,
        )
        self.fields['date'].widget = DateInput()
        
        if self.instance.id and self.instance.reconciled():
            self.fields['amount'].required = False
            self.fields['amount'].widget.attrs = {'disabled': 'disabled'}
    
    def clean_debit(self):
        debit = self.cleaned_data['debit']
        credit = self.cleaned_data['credit']
        if debit.type != credit.type or debit.id == credit.id:
            raise forms.ValidationError('Select a valid choice. That choice is not one of the available choices.')
        return debit
    
    def save(self):
        # ignore POSTed amount field if transaction is reconciled
        if self.instance.id and self.instance.reconciled():
            self.cleaned_data.pop('amount')
        instance = super(TransferForm, self).save(commit=False)
        instance.memo = 'Transfer from %s to %s' % (
            instance.credit, 
            instance.debit,
        )
        instance.quantity = 1
        instance.editor = self.user
        instance.save()
        return instance


#class GeneralEntryForm(RequestModelForm):
class GeneralEntryForm(forms.ModelForm):
    class Meta:
        model = ledger.Transaction
        fields = ('date', 'debit', 'credit', 'memo', 'amount',)
    
    def __init__(self, *args, **kwargs):
        super(GeneralEntryForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = (
            'credit',
            'debit',
            'date',
            'amount',
            'memo',
        )
        self.fields['date'].widget = DateInput()
        self.fields['memo'].widget = forms.TextInput()
        if self.instance.id and self.instance.reconciled():
            self.fields['amount'].required = False
            self.fields['amount'].widget.attrs = {'disabled': 'disabled'}
    
    def save(self):
        # ignore POSTed amount field if transaction is reconciled
        if self.instance.id and self.instance.reconciled():
            self.cleaned_data.pop('amount')
        instance = super(GeneralEntryForm, self).save(commit=False)
        instance.quantity = 1
        instance.editor = self.user
        instance.save()
        return instance


from django.forms.models import BaseModelFormSet
class GeneralEntryFormSetBase(BaseModelFormSet):
    def __init__(self, user, transaction, *args, **kwargs):
        super(GeneralEntryFormSetBase, self).__init__(*args, **kwargs)
        self.transaction = transaction
        self.initial_user_data(user)

    def initial_user_data(self, user):
        accounts_belong_to_user = ledger.Account.objects.filter(editor=user)
        for form in self.forms:

            form.fields.keyOrder = (
                'credit',
                'debit',
                'date',
                'amount',
                'memo',
            )
            form.fields['date'].widget = DateInput()
            form.fields['date'].initial = datetime.date.today()
            form.fields['memo'].widget = forms.TextInput()
            accounts_belong_to_user = ledger.Account.objects.filter(editor=user)
            form.fields['debit'].queryset = accounts_belong_to_user
            form.fields['credit'].queryset = accounts_belong_to_user
            if self.transaction:
                form.fields['debit'].initial = self.transaction.debit
                form.fields['credit'].initial = self.transaction.credit
                if self.transaction.reconciled():
                    self.fields['amount'].required = False
                    self.fields['amount'].widget.attrs = {'disabled': 'disabled'}
