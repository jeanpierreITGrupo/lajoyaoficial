# -*- coding: utf-8 -*-

from openerp import models, fields, api

class account_move_line(models.Model):
	_inherit = 'account.move.line'
	currency_rate_it = fields.Float('Tipo de Cambio Sunat', digits=(16,3))
