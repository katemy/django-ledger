# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# $Id: report.py 445 2009-09-21 17:35:31Z tobias $
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

from django.conf import settings

from ledger.models import Account
from ledger.pdf_latex import render_to_pdf_string


def generate_exchange_pdf(exchange):
    """ invoices, receipts, etc """
    
    try:
        location = exchange.business.locations.all()[0]
    except IndexError:
        location = None
    
    if location:
        try:
            client_address = location.addresses.all()[0]
        except IndexError:
            client_address = None
    else:
        client_address = None

    try:
        user_profile = exchange.editor.get_profile()
    except:
        #TODO: more specific Exception, too bad DoesNotExist does'nt work
        user_profile = None
        
    context = {
        'exchange': exchange,
        'letter_title': '%s \#%d' % (exchange.type, exchange.id),
        'letter_date': exchange.date,
        'client': exchange.business,
        'client_address': client_address,
        'show_project_balance': exchange.type.slug in ('invoice', 'receipt'),
        'MEDIA_ROOT': settings.MEDIA_ROOT,
        'user_profile': user_profile,
    }
    
    return render_to_pdf_string('books/ledger/exchange/view.tex', context)


def generate_project_report_pdf(project):
    """ credits and debits of a Project """
    
    ar = Account.objects.get(number=1200)
    context = {
        'ar'      : ar,
        'credits' : ar.credits.filter(project=project.id),
        'debits'  : ar.debits.filter(project=project.id),
        'client'  : project.business,
        'project' : project,
        'letter_title': 'Project Report',
        'letter_date': datetime.datetime.now(),
        'MEDIA_ROOT': settings.MEDIA_ROOT,
    }
    
    credit_total = ar.credit_total_for_project(project.id)
    debit_total = ar.debit_total_for_project(project.id)
    
    if not credit_total: credit_total = 0
    if not debit_total:   debit_total = 0
    outstanding_balance = debit_total - credit_total

    context.update( { 
                   'credit_total'        : credit_total,
               'debit_total'         : debit_total,
               'outstanding_balance' : outstanding_balance
               })
    
    return render_to_pdf_string('books/report/project.tex', context)
