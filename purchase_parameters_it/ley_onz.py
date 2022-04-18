# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api
from openerp.osv import osv
from datetime import date, timedelta

class table_ley_onz(models.Model):
	_name = 'table.ley.onz'
	_order = 'id desc'

	mineral_type = fields.Selection([('oro','Oro'),('plata','Plata')], "Tipo")
	employee = fields.Many2one('hr.employee',"Personal", readonly=1)
	zone_id = fields.Many2one('table.zone',u'Zona')
	date = fields.Date("Fecha", readonly=0)
	param1 = fields.Float("Desde",digits=(10,3))
	param2 = fields.Float("Hasta",digits=(10,3))
	percentage = fields.Float("%_A_ley",digits=(10,1))

	_sql_constraints = [
        ('ley_uniq', 'unique(mineral_type, zone_id, date, param1, param2)', u'La ley no puede tener misma zona, fecha y parámetros.'),
    ]

	@api.model
	def create(self,vals):
		employee = self.env['hr.employee'].search([('user_id','=',self.env.uid)])
		vals['employee'] = employee.id
		vals['date'] = date.today()
		return super(table_ley_onz,self).create(vals)
