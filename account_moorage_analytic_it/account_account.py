# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions , _

class account_account(models.Model):
	_inherit = 'account.account'

	account_analytic_account_moorage_id = fields.Many2one('account.account',string ="Amarre al Haber",index = True)
	account_analytic_account_moorage_debit_id = fields.Many2one('account.account',string ="Amarre al Debe",index = True)
	check_moorage = fields.Boolean(string="Tiene Destino")



class account_move_line(models.Model):
	_inherit= 'account.move.line'
