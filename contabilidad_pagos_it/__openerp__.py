# -*- encoding: utf-8 -*-
{
	'name': 'correccion contabilidad pagos proveedores',
	'category': 'account',
	'author': 'ITGRUPO-COMPATIBLE',
	'depends': ['account'],
	'version': '1',
	'description':"""
    - añade opcion eliminar apuntes con cero
    - elimina filas donde debito y credito es 0
	- se añade en contabilidad pagos 
	""",
	'auto_install': False,
	'demo': [],
	'data':	['views/account_voucher_view.xml'],
	'installable': True
}
