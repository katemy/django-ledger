# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# $Id: arrayutil.py 310 2008-10-02 17:24:23Z copelco $
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

try:
    from dateutil.relativedelta import relativedelta
except ImportError:
    raise ImportError('minibooks was unable to import the dateutil library. Please confirm it is installed and available on your current Python path.')

from django import template
from django.contrib.humanize.templatetags.humanize import intcomma
from django.template.defaultfilters import floatformat

from company.templatetags.currency_symbol import currency_symbol
from company.models import UserProfile
register = template.Library()

def get_user_currency_symbol(user):
    try:
        currency_symbol_type = user.get_profile().currencySymbol
        return currency_symbol(currency_symbol_type)
    except UserProfile.DoesNotExist:
        return currency_symbol('dollar')

@register.filter(name='currency')
def currency(num, user):
    currey_symbol = get_user_currency_symbol(user)
    return  u'%s%s' % (currey_symbol,intcomma(floatformat(num, 2)))


@register.inclusion_tag('books/ledger/_date_filters.html', takes_context=True)
def ledger_date_filters(context):
    request = context['request']
    from_slug = 'from_date'
    to_slug = 'to_date'
    use_range = True
    
    def construct_url(from_date, to_date):
        url = '%s?%s=%s' % (
            request.path,
            to_slug,
            to_date.strftime('%m/%d/%Y'),
        )
        if use_range:
            url += '&%s=%s' % (
                from_slug,
                from_date.strftime('%m/%d/%Y'),
            )
        return url

    filters = {}
    filters['Past 12 Months'] = []
    single_month = relativedelta(months=1)
    from_date = datetime.date.today().replace(day=1) + relativedelta(months=1)
    for x in range(12):
        to_date = from_date
        from_date = to_date - single_month
        url = construct_url(from_date, to_date - relativedelta(days=1))
        filters['Past 12 Months'].append((from_date.strftime("%b '%y"), url))
    filters['Past 12 Months'].reverse()
    
    start = datetime.date.today().year - 3
    
    filters['Years'] = []
    for year in range(start, start + 3):
        from_date = datetime.datetime(year, 1, 1)
        to_date = from_date + relativedelta(years=1)
        url = construct_url(from_date, to_date - relativedelta(days=1))
        filters['Years'].append((str(from_date.year), url))

    filters['Quaters (Calendar Year)'] = []
    to_date = datetime.date(datetime.date.today().year - 1, 1, 1)
    for x in range(8):
        from_date = to_date
        to_date = from_date + relativedelta(months=3)
        url = construct_url(from_date, to_date - relativedelta(days=1))
        filters['Quaters (Calendar Year)'].append(
            ('Q%s %s' % ((x % 4) + 1, from_date.year), url)
        )

    return {'filters': filters}
