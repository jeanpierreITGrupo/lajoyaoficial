# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp import models, fields, api

class account_journal(models.Model):
	_inherit = 'account.journal'
	
	is_fixer = fields.Boolean('Rendiciones')