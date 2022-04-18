# -*- coding: utf-8 -*-

from openerp import models, fields, api

class account_move_line(models.Model):
	_inherit = 'account.move.line'
	
	codigo_partner = fields.Char(string="Código",store=False, related='partner_id.type_number')

class account_account(models.Model):
	_inherit = 'account.account'

	tipo_adquisicion_diario = fields.Selection([('1','Mercaderia'),('2','Activo Fijo'),('3','Otros Activo'),('4','Gastos de Educacion, Recreación, Salud, Mantenimiento de Activos'),('5','Otros no incluidos en 4')],'Tipo de Adquisición')