# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
# Copyright (c) 2011 Cubic ERP - Teradata SAC. (http://cubicerp.com).
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import string

from openerp.osv import osv, fields
from openerp.tools.translate import _

class res_partner(osv.osv):
    _inherit = 'res.partner'
        
    def check_vat_pe(self, vat):
        ruc = str(vat)
        if not ruc.isdigit():
            return False
        if (len (ruc) <> 11):
            return  False
        control = str(5432765432)
        n = 0
        for i, j in enumerate(ruc[:-1]):
            n += int(control[i]) * int(j)
        r = 11 - n%11
        if r == 11:
            n = 1
        elif r == 10:
            n = 0
        else:
            n = r
        return n == int(ruc[-1])

res_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
