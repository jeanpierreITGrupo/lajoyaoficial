# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp import models, fields, api  , exceptions , _

class stock_picking(models.Model):
	_inherit = 'stock.picking'

	@api.one
	def transferir_picking(self):
		all_groups=self.env['res.groups']
		all_users =self.env['res.users']
		
		g1_ids = all_groups.search([('name','=',u'Puede Transferir')])
				
		if not g1_ids: 
			raise osv.except_osv('Alerta!', "No existe el grupo 'Puede Transferir' creada.") 

		if not g1_ids in all_users.search([('id','=',self.env.uid)])[0].groups_id:
			raise osv.except_osv('Alerta!', "No tiene los permisos para transferir albaranes") 

		return super(stock_picking,self).transferir_picking()
