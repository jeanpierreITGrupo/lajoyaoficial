# -*- coding: utf-8 -*-

from openerp import models, fields, api

class account_move_line(models.Model):
	_inherit = 'account.move.line'
	
	codigo_partner = fields.Char(string="Código",store=False, related='partner_id.type_number')