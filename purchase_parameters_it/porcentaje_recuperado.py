# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api
from openerp.osv import osv
from datetime import date, timedelta

class table_recover_percentage(models.Model):
	_name = 'table.recover.percentage'
	_order = 'date desc, rec_lab'

	mineral_type = fields.Selection([('oro','Oro'),('plata','Plata')], "Tipo")
	employee = fields.Many2one('hr.employee',"Personal", readonly=1)
	zone_id = fields.Many2one('table.zone',u'Zona')
	date = fields.Date("Fecha", readonly=0)
	rec_lab = fields.Float("Rec. Lab.",digits=(10,3))
	adjust = fields.Float("Ajuste",digits=(10,3))
	consider = fields.Float(u"Consideración",digits=(10,3))

	_sql_constraints = [
        ('p_rec_uniq', 'unique(mineral_type, zone_id, date, rec_lab)', u'La ley no puede tener misma zona, fecha y Rec. Lab.'),
    ]

	@api.model
	def create(self,vals):
		employee = self.env['hr.employee'].search([('user_id','=',self.env.uid)])
		vals['employee'] = employee.id
		vals['date'] = date.today()
		return super(table_recover_percentage,self).create(vals)
