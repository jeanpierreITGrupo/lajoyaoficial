# -*- encoding: utf-8 -*-
from openerp.osv import osv, fields

class kardex_saldos(osv.osv):
	_name='kardex.saldos'
	_auto = False
	_columns={
		'codigo': fields.char('Codigo', size=64),
		'producto': fields.char('Producto', size=64),
		'grupo': fields.char('Grupo', size=64),
		'subgrupo': fields.char('Sub Grupo', size=64),
		'calidad': fields.char('Grupo', size=64),
		'entrada': fields.float('Entrada', digits=(12,6)),
		'salida': fields.float('Salida', digits=(12,6)),
		'saldo': fields.float('Saldo', digits=(12,6)),
	}

	
	
kardex_saldos()
