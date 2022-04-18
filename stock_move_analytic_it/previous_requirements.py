# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api
from openerp.osv import osv
from openerp import exceptions


#Movimiento de Almacén
class stock_move(models.Model):
	_inherit = 'stock.move'

	analytic_id = fields.Many2one("account.analytic.account","Cuenta Analítica")
	tipo_destino_analytic = fields.Selection([
                        ('supplier', 'Supplier Location'),
                        ('view', 'View'),
                        ('internal', 'Internal Location'),
                        ('customer', 'Customer Location'),
                        ('inventory', 'Inventory'),
                        ('procurement', 'Procurement'),
                        ('production', 'Production'),
                        ('transit', 'Transit Location')],'Tipo Destino',related='location_dest_id.usage')