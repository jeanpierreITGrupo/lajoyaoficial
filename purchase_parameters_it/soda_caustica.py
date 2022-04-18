# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api
from openerp.osv import osv
from datetime import date, timedelta

class table_soda(models.Model):
	_name = 'table.soda'
	_order = 'date desc, param1'

	mineral_type = fields.Selection([('oro','Oro'),('plata','Plata')], "Tipo")
	employee = fields.Many2one('hr.employee',"Personal", readonly=1)
	date =	fields.Date("Fecha", readonly=0)
	param1 = fields.Float("Desde (kg)",digits=(10,2))
	param2 = fields.Float("Hasta (kg)",digits=(10,2))
	unit = fields.Float("Unidad")
	value_unit = fields.Float("Valor Und")
	value_consumed = fields.Float("Consumo Valorado")

	_sql_constraints = [
        ('soda_uniq', 'unique(mineral_type, date, param1, param2)', u'La ley no puede tener misma fecha y parámetros.'),
    ]

	@api.model
	def create(self,vals):
		employee = self.env['hr.employee'].search([('user_id','=',self.env.uid)])
		vals['employee'] = employee.id
		vals['date'] = date.today()
		return super(table_soda,self).create(vals)
