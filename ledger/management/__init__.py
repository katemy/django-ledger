# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# $Id: management.py 372 2009-01-13 16:21:01Z copelco $
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


from django.dispatch import dispatcher
from django.db.models import signals
from django.contrib.auth.models import User, Group

from crm import models as crm_models

from ledger import demo
from ledger import models as ledger_models


def post_syncdb(signal, sender, app, created_models, **kwargs):
    # only run when our model got created
    if (signal == signals.post_syncdb) and (app == ledger_models):
        ledger_models.install()
    if (signal == signals.post_syncdb) and (app == crm_models):
        crm_models.install()

#signals.post_syncdb.connect(post_syncdb)


def clean_minibooks_db():
    for g in Group.objects.all():
        g.delete()
    for u in User.objects.all():
        u.delete()
    for b in crm_models.Business.objects.all():
        b.delete()
    for p in crm_models.Project.objects.all():
        p.delete()
    
    demo.setup_demo()
