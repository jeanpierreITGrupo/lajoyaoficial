# -*- encoding: utf-8 -*-

from openerp import models, fields, api
from openerp.osv import osv

class hr_distribucion_gasto(models.Model):
	_name = 'hr.distribucion.gastos'
	_rec_name = 'descripcion'

	codigo             = fields.Char('Código',required=True)
	descripcion        = fields.Char('Descripción',required=True)
	distribucion_lines = fields.One2many('hr.distribucion.gastos.linea','distribucion_gastos_id','Lineas de Distribución')

class hr_distribucion_gastos_linea(models.Model):
	_name = 'hr.distribucion.gastos.linea'

	distribucion_gastos_id = fields.Many2one('hr.distribucion.gastos','Distribución Gastos')
	cuenta                 = fields.Many2one('account.account','Cuenta',required=False)
	porcentaje             = fields.Float('Porcentaje',required=True,digits=(12,2))
	analitica              = fields.Many2one('account.analytic.account','Cuenta Analítica')