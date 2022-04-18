# -*- coding: utf-8 -*-

from openerp import models, fields, api

class account_account(models.Model):
	_inherit = 'account.account'
	clasification_sheet = fields.Selection((('1','Situación Financiera'),
									('2','Resultados por Naturaleza'),
									('3','Resultados por Función'),
									('6','Resultados'),
									('4','Cuenta de Orden'),
									('5','Cuenta de Mayor')
									),'Clasificación Hoja de Trabajo')
	level_sheet = fields.Selection((('1','Cuentas de Balance'),
									('2','Cuentas de Registro')
									),'Nivel')

	
	code_sunat = fields.Char('CODIGO SUNAT')