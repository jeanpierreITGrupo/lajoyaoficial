# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp import models, fields, api  , exceptions , _

class account_invoice(models.Model):
	_inherit = 'account.invoice'

	@api.multi
	def action_date_assign(self):
		all_groups=self.env['res.groups']
		all_users =self.env['res.users']
		
		g1_ids = all_groups.search([('name','=',u'Validar Facturas')])
				
		if not g1_ids: 
			raise osv.except_osv('Alerta!', "No existe el grupo 'Validar Facturas' creada.") 

		if not g1_ids in all_users.search([('id','=',self.env.uid)])[0].groups_id:
			raise osv.except_osv('Alerta!', "No tiene los permisos para validar Facturas") 

		return super(account_invoice,self).action_date_assign()
