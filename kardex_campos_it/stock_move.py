# -*- encoding: utf-8 -*-
from openerp.osv import fields, osv
class stock_move(osv.osv):
	_name='stock.move'
	_inherit='stock.move'
	_columns={
		'precio_unitario_manual':fields.float('P.U. Manual'),
	}
stock_move()
