# -*- coding: utf-8 -*-

from openerp import models, fields, api

class account_account_type(models.Model):
	_inherit = 'account.account.type'
	
	order_balance = fields.Integer(string='Orden')
	group_balance = fields.Selection((('B1','Activo Corriente'),
									('B2','Activo no Corriente'),
									('B3','Pasivo Corriente'),
									('B4','Pasivo no Corriente'),
									('B5','Patrimonio')									
									),'Grupo Balance')

	order_nature = fields.Integer(string='Orden')
	group_nature = fields.Selection((('N1','Grupo 1'),
									('N2','Grupo 2'),
									('N3','Grupo 3'),
									('N4','Grupo 4'),
									('N5','Grupo 5'),
									('N6','Grupo 6'),
									('N7','Grupo 7'),
									('N8','Grupo 8')
									),'Grupo Naturaleza')

	order_function = fields.Integer(string='Orden')
	group_function = fields.Selection((('F1','Grupo 1'),
									('F2','Grupo 2'),
									('F3','Grupo 3'),
									('F4','Grupo 4'),
									('F5','Grupo 5'),
									('F6','Grupo 6')
									),'Grupo Función')