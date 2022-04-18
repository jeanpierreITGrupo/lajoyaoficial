# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api
from openerp.osv import osv
from datetime import date, timedelta

class table_humidity(models.Model):
	_name = 'table.humidity'
	_order = 'date desc, h2o'

	mineral_type = fields.Selection([('oro','Oro'),('plata','Plata')], "Tipo")
	employee = fields.Many2one('hr.employee',"Personal", readonly=1)
	date =	fields.Date("Fecha", readonly=0)
	h2o = fields.Float("%_H2O",digits=(10,2))
	increase = fields.Float("Incremento",digits=(10,2))

	_sql_constraints = [
        ('humedad_uniq', 'unique(mineral_type, h2o)', u'La ley no puede tener misma fecha y humedad.'),
    ]

	@api.model
	def create(self,vals):
		employee = self.env['hr.employee'].search([('user_id','=',self.env.uid)])
		vals['employee'] = employee.id
		vals['date'] = date.today()
		return super(table_humidity,self).create(vals)
