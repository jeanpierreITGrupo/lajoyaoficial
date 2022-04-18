# -*- coding: utf-8 -*-
from openerp import models, fields, api

class account_invoice(models.Model):
	_inherit = 'account.invoice'

	r_reference = fields.Char("Referencia", size=200)
