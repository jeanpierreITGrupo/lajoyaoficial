# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api
from openerp.osv import osv
from datetime import date, timedelta


class table_adjust_factor_security(models.Model):
	_name = 'table.adjust.factor.security'

	employee = fields.Many2one('hr.employee',"Personal", readonly=1)
	date =	fields.Date("Fecha", readonly=0)
	factor = fields.Float("Factor",digits=(10,4))
	mineral_type = fields.Selection([('oro','Oro'),('plata','Plata')], "Tipo")
	fecha_modificacion = fields.Datetime('Fecha Modificación')
	motivo = fields.Char('Razon Registro')


class table_adjust_factor(models.Model):
	_name = 'table.adjust.factor'

	employee = fields.Many2one('hr.employee',"Personal", readonly=1)
	date =	fields.Date("Fecha", readonly=0)
	factor = fields.Float("Factor",digits=(10,4))
	mineral_type = fields.Selection([('oro','Oro'),('plata','Plata')], "Tipo")

	_sql_constraints = [
        ('factor_ajuste_uniq', 'unique(mineral_type, date)', u'La ley no puede tener misma fecha.'),
    ]

	@api.model
	def create(self,vals):
		employee = self.env['hr.employee'].search([('user_id','=',self.env.uid)])
		vals['employee'] = employee.id
		vals['date'] = date.today()
		return super(table_adjust_factor,self).create(vals)
