# -*- coding: utf-8 -*-
"""from openerp import models, fields, api
from openerp.osv import osv

class account_move_line(models.Model):
	_name = 'account.move.line'
	_inherit = 'account.move.line'

	grupo_p_neto = fields.Char('Grupo P. Neto', size=50)
	columna_p_neto = fields.Selection((('0','Capital'),
									('1','Acciones Inversion'),
									('2','Capital Adicional'),
									('3','Resultados No Realizados'),
									('4','Excedente Revaluación'),
									('5','Reservas'),
									('6','Resultados Acumulados')
									),'Columna P. Neto')


"""