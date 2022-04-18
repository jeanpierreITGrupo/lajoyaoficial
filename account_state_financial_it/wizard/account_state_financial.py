# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.osv import osv

class account_config_efective(models.Model):

	_name='account.config.efective'
	_rec_name='code'
	id = fields.Integer(string='ID')
	concept = fields.Char(string='Concepto', size=50)
	code = fields.Char(string='Código',size=20)
	group = fields.Selection((
									
									('E1','Ingresos de operación'),
									('E2','Egresos de operación'),
									('E3','Ingresos de Inversión'),
									('E4','Egresos de Inversión'),
									('E5','Ingresos de Financiamiento'),
									('E6','Egresos de Financiamiento'),
									('E7','Saldo Inicial'),
									('E8','Diferencia de cambio'),
									
							  ),'Grupo')
	order = fields.Integer(string='Orden')
