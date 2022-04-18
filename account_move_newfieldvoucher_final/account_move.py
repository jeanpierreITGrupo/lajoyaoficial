# -*- coding: utf-8 -*-

from openerp import models, fields, api,exceptions , _
from openerp.osv import osv
import re

class account_move(models.Model):
	_inherit = 'account.move'

	vau_anterior =fields.Char('Voucher Anterior')