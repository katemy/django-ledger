# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# $Id: businesstype.sql 308 2008-10-02 14:56:48Z tobias $
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


CREATE TABLE "ledger_exchangetype_business_types" (
    "id" serial NOT NULL PRIMARY KEY,
    "exchangetype_id" integer NOT NULL REFERENCES "ledger_exchangetype" ("id") DEFERRABLE INITIALLY DEFERRED,
    "businesstype_id" integer NOT NULL REFERENCES "crm_businesstype" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("exchangetype_id", "businesstype_id")
);

CREATE TABLE "crm_business_business_types" (
    "id" serial NOT NULL PRIMARY KEY,
    "business_id" integer NOT NULL REFERENCES "crm_business" ("id") DEFERRABLE INITIALLY DEFERRED,
    "businesstype_id" integer NOT NULL REFERENCES "crm_businesstype" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("business_id", "businesstype_id")
);

