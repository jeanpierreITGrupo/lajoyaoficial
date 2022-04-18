# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api
from openerp.osv import osv
from datetime import date, timedelta

class table_international_price(models.Model):
	_name = 'table.international.price'
	_order = 'id desc'

	mineral_type = fields.Selection([('oro','Oro'),('plata','Plata')], "Tipo")
	employee = fields.Many2one('hr.employee',"Personal", readonly=1)
	date_price = fields.Date("Fecha Precio", readonly=0)
	price = fields.Float("P Inter",digits=(10,2))

	@api.model
	def create(self,vals):
		employee = self.env['hr.employee'].search([('user_id','=',self.env.uid)])
		vals['employee'] = employee.id
		#vals['date_price'] = date.today() - timedelta(days=1)
		return super(table_international_price,self).create(vals)
