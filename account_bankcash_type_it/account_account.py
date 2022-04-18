# -*- encoding: utf-8 -*-

from openerp import models, fields, api

class account_account(models.Model):
	_name='account.account'
	_inherit='account.account'		
	check_liquidity =  fields.Boolean('Es Banco?')
