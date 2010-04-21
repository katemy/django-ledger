# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# $Id: admin.py 437 2009-09-18 16:17:58Z copelco $
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


from django import forms
from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth import admin as admin_app
from crm import models as crm
from ledger import models as ledger

books_admin = admin.AdminSite()

class UserAdmin(admin_app.UserAdmin):
    list_display = ('id', 'last_name', 'first_name', 'email', 'last_login', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name',)
    list_filter = ('groups','is_staff')
    ordering = ('last_name',)
books_admin.register(User, UserAdmin)


class GroupAdmin(admin_app.GroupAdmin):
    fields = ('name', 'permissions',)
books_admin.register(Group, GroupAdmin)


class ExchangeTypeAdmin(admin.ModelAdmin):
    list_display = ('label', 'debit', 'credit', 'common_account')
books_admin.register(ledger.ExchangeType, ExchangeTypeAdmin)
    

class BusinessTypeAdmin(admin.ModelAdmin):
    pass
books_admin.register(crm.BusinessType, BusinessTypeAdmin)
