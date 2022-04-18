# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp import models, fields, api

class product_template(models.Model):
	_inherit = 'product.template'
	
	analytic_account_id = fields.Many2one('account.analytic.account', 'Cuenta Analitica')