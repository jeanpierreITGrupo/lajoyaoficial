# -*- encoding: utf-8 -*-
{
	'name': 'Account Type Document',
	'category': 'account',
	'author': 'ITGrupo',
	'depends': ['account','account_voucher','account_tables_it'],
	'version': '1.0',
	'description':"""
		1.- Crea campo tipo de documento SUNAT en facturas de proveedor,  facturas de clientes, facturas rectificativas recibos de compra y recibos 
		de venta.
		2.- Modifica la vista tree de facturas para mostrar el periodo, el libro contable, el voucher, el tipo de documento y número de comprobante.
		3.- Agrega agrupaciones por libro y tipo de documento.
		
	""",
	'auto_install': False,
	'demo': [],
	'data':	['account_invoice_view.xml','account_voucher_view.xml','account_move_line_view.xml','account_journal_view.xml'],
	'installable': True
}
