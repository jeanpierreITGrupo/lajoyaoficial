# -*- coding: utf-8 -*-

from openerp import models, fields, api

class account_analytic_account(models.Model):
	_inherit = 'account.analytic.account'

	account_account_moorage_id = fields.Many2one('account.account',string ="Amarre al Debe",index = True)
	account_account_moorage_credit_id = fields.Many2one('account.account',string ="Amarre al Haber",index = True)

