# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# $Id: businesstype2.sql 308 2008-10-02 14:56:48Z tobias $
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


alter table crm_businesstype add column "can_view_all_projects" boolean;
update crm_businesstype set can_view_all_projects = false;
update crm_businesstype set can_view_all_projects = true where name='Vendor';
alter table crm_businesstype alter COLUMN can_view_all_projects not null;
