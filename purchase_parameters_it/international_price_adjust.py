# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api
from openerp.osv import osv
from datetime import date, timedelta

class table_international_price_adjust(models.Model):
	_name = 'table.international.price.adjust'
	_order = 'date_valid desc, zone_id'

	mineral_type = fields.Selection([('oro','Oro'),('plata','Plata')], "Tipo")
	employee = fields.Many2one('hr.employee',"Personal", readonly=1)
	zone_id = fields.Many2one('table.zone',u'Zona')
	date_param = fields.Date("Fecha Param", readonly=0)
	date_valid = fields.Date("Fecha Validez")
	adjustment = fields.Float("Ajuste",digits=(10,2))

	_sql_constraints = [
        ('tabla_internacional_uniq', 'unique(mineral_type, zone_id, date_valid)', u'La ley no puede tener misma zona y fecha validez.'),
    ]

	@api.model
	def create(self,vals):
		employee = self.env['hr.employee'].search([('user_id','=',self.env.uid)])
		vals['employee'] = employee.id
		vals['date_param'] = date.today()
		return super(table_international_price_adjust,self).create(vals)
