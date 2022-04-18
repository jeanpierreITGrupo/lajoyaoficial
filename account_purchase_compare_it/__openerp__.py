# -*- encoding: utf-8 -*-
{
	'name': 'Comparador Trazabilidad Compras Ventas',
	'category': 'account',
	'author': 'ITGrupo',
	'depends': ['stock_cancel','stock_account','web','sale','sale_stock','purchase_requisition','account','account_voucher','account_tables_it','account_type_doc_it','currency_sunat_change_it','partner_name_it','account_contable_book_it','repaccount_move_line_it'],
	'version': '1.0',
	'description':"""
	Crea Trazabilidad para Pedidos de Compra o Venta,
	Arregla Casos para Pedidos de Compra
	
	""",
	'auto_install': False,
	'demo': [],
	'js':['static/src/js/mywidget.js','static/src/js/notify.js','static/src/js/jquery.noty.packaged.js'],
	'data':	['account_asset_alter_view.xml'],
	'installable': True
}
