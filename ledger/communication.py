# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# $Id: communication.py 422 2009-07-14 03:14:17Z tobias $
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


from django.core.mail import EmailMessage
from django.template import RequestContext, Context, loader
from django.conf import settings

def send_caktus_email(exchange_slug=None, exchange_label=None, recipients=None, subject=None, context=None, attachment=None):
    """
        send_caktus_email('invoice', context, recipients, attachment)
    """
    
    if not context:
        context = {}
    
    # prepare email message
    template = loader.get_template("books/ledger/exchange/email/%s.txt" % exchange_slug)
    template_context = Context(context)
    
    # generate email message
    body = template.render(template_context)
    
    if subject is None:
        subject = exchange_label
    
    sender = settings.DEFAULT_FROM_EMAIL
    
    try:
        email = EmailMessage(subject, body, sender, recipients, [sender])
    
        if attachment:
            email.attach('%s.pdf' % exchange_slug, attachment)
            
        email.send()
        
        return True
        
    except Exception, err:
        return False

def send_exchange_email(exchange_type=None, recipients=None, subject=None, context=None, attachment=None):
    return send_caktus_email(exchange_slug=exchange_type.slug, exchange_label=exchange_type.label, recipients=recipients, subject=subject, context=context, attachment=attachment)

def send_project_report_email(recipients=None, subject=None, context=None, attachment=None):
    return send_caktus_email(exchange_slug="project_report", exchange_label="Project Report", recipients=recipients, subject=subject, context=context, attachment=attachment)
