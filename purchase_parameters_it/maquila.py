# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api
from openerp.osv import osv
from datetime import date, timedelta

class table_maquila(models.Model):
	_name = 'table.maquila'
	_order = 'date desc, zone_id, ley'

	mineral_type = fields.Selection([('oro','Oro'),('plata','Plata')], "Tipo")
	employee = fields.Many2one('hr.employee',"Personal", readonly=1)
	zone_id = fields.Many2one('table.zone',u'Zona')
	date = fields.Date("Fecha", readonly=0)
	ley = fields.Float("Ley",digits=(10,3))
	maquila = fields.Float("Maquila",digits=(10,3))

	_sql_constraints = [
        ('maquila_uniq', 'unique(mineral_type, zone_id, date, ley)', u'La ley no puede tener misma zona, fecha y ley.'),
    ]

	@api.model
	def create(self,vals):
		employee = self.env['hr.employee'].search([('user_id','=',self.env.uid)])
		vals['employee'] = employee.id
		vals['date'] = date.today()
		return super(table_maquila,self).create(vals)
