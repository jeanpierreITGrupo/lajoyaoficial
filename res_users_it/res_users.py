# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp import models, fields, api

class res_users(models.Model):
	_inherit = 'res.users'
	

	@api.one
	def _get_it_group(self):
		print 'INSIDE IT GRUPO', self.it_group_id
		itgrupo = self.env['ir.module.category'].search([('name', '=', 'IT Grupo')])
		#itgrupo = self.env['ir.module.category'].search(['name','=','IT Grupo'])
		self.it_group_id = itgrupo.id


	
	it_group_id = fields.Many2one('ir.module.category','It Grupo', compute='_get_it_group')

	