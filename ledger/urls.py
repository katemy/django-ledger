# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# $Id: urls.py 422 2009-07-14 03:14:17Z tobias $
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


from django.conf.urls.defaults import *

import ledger.views as views

urlpatterns = patterns('',
    url(r'^cron/', views.cron, name='cron'),
    
    # exchange
    url(r'^exchange/list/$', views.list_exchanges, name='list_exchanges'),
    url(r'^exchange/list/(?P<exchange_type_slug>\w+)/$', views.list_exchanges, name='list_exchanges_by_type'),
    url(r'^(?:business/(?P<business_id>\d+)/)?(?:project/(?P<project_id>\d+)/)?exchange/create/(?P<exchange_type_slug>.+)/$', views.create_edit_exchange, name='create_exchange'),
    url(r'^exchange/(?P<exchange_id>\d+)/pdf/$', views.view_exchange_as_pdf, name='view_exchange_as_pdf'),
    url(r'^exchange/(?P<exchange_id>\d+)/edit/(?P<exchange_type_slug>\w+)/$', views.create_edit_exchange, name='edit_exchange'),
    url(
        r'^exchange/(?P<exchange_id>\d+)/edit/type/(?P<exchange_type_slug>\w+)/$',
        views.edit_exchange_type,
        name='edit_exchange_type',
    ),
    url(r'^exchange/(?P<exchange_id>\d+)/remove/$', views.remove_exchange, name='remove_exchange'),
    url(r'^exchange/(?P<exchange_id>\d+)/duplicate/$', views.duplicate_exchange, name='duplicate_exchange'),
    
    # transaction
    url(r'^transaction/reconcile/$', views.reconcile_transaction, name='reconcile_transaction'),
    
    # report
    url(r'^project/report/(?P<project_id>\d+)/$', views.show_project_report, name='show_project_report'),
    
    # emails
    url(r'^new/email/exchange/(?P<exchange_id>\d+)/$', views.new_exchange_email, name='email_exchange'),
    url(r'^new/email/project_report/(?P<project_id>\d+)/$', views.new_project_report_email, name='email_project_report'),
    
    # account
    url(r'^account/list/$', views.list_accounts, name='list_accounts'),
    url(r'^account/transfer/$', views.transfer_funds, name='transfer_funds'),
    url(r'^account/transfer/(?P<transaction_id>\d+)/$', views.transfer_funds, name='edit_account_transfer'),
    
    url(
        r'^account/general-entry/$',
        views.general_entry,
        name='create_general_entry',
    ),
    url(
        r'^account/general-entry/(?P<transaction_id>\d+)/$',
        views.general_entry,
        name='edit_general_entry',
    ),
    url(r'^account/transfer/debit/list/$', views.list_transfer_debit_accounts, name='list_transfer_debit_accounts'),
    url(r'^account/print/$', views.account_ledger, name='account_ledger'),
    url(
        r'^account/(?P<account_id>\d+)/$',
        views.account_ledger,
        name='single_account_ledger',
    ),
    url(
        r'^account/(?P<account_id>\d+)/remove/$',
        views.remove_account,
        name='remove_account',
    ),
    url(
        r'^account/(?P<account_id>\d+)/edit/$',
        views.create_edit_account,
        name='edit_account',
    ),
    url(
        r'^account/create/$',
        views.create_edit_account,
        name='create_account',
    ),
    
    url(
        r'^report/$',
        views.list_reports,
        name='list_reports',
    ),
    url(
        r'^report/profit-loss/$',
        views.profit_loss,
        name='profit_loss',
    ),
    url(
        r'^report/balance-sheet/$',
        views.balance_sheet,
        name='balance_sheet',
    ),
)
