# -*- coding: utf-8 -*-

from openerp import models, fields, api

class account_move_line(models.Model):
	_inherit = 'account.move.line'
	means_payment_id = fields.Many2one('it.means.payment',string ="MPago",index = True,ondelete='restrict')
	