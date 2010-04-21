# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# $Id: $
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

from django.db import transaction
from django.core.urlresolvers import reverse
from django.conf import settings

from ledger import models as ledger

@transaction.commit_on_success
def create_recurring_exchanges():
    messages = []
    for repeat_period in ledger.RepeatPeriod.objects.filter(active=True):
        exchange = repeat_period.exchanges.order_by('-date').select_related()[0]
        transactions = exchange.transactions.all()
        while exchange.date + repeat_period.delta() <= datetime.date.today():
            exchange.id = None
            exchange.date += repeat_period.delta()
            if exchange.date_due:
                exchange.date_due += repeat_period.delta()
            exchange.delivered = False
            exchange.save(force_insert=True)
            url_kwargs = {
                'exchange_id': exchange.id,
                'exchange_type_slug': exchange.type.slug,
            }
            
            messages.append('%s%s' % (
                settings.APP_URL_BASE,
                reverse('edit_exchange', kwargs=url_kwargs),
            ))
            for transaction in transactions:
                transaction.id = None
                transaction.exchange = exchange
                transaction.date = exchange.date
                transaction.debit_reconciled = False
                transaction.credit_reconciled = False
                transaction.save(force_insert=True)
    
    if messages:
        messages.insert(0, 'created the following exchanges:')
    return messages
