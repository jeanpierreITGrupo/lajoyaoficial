# -*- encoding: utf-8 -*-
{
	'name': 'Extracto Bancario IT',
	'category': 'account',
	'author': 'ITGrupo',
	'depends': ['partner_name_it','account_contable_book_it','account_account_bankdetail_it','account_voucher'],
	'version': '1.0',
	'description':"""
	Crea Trazabilidad para Pedidos de Compra o Venta,
	Arregla Casos para Pedidos de Compra
	
	""",
	'auto_install': False,
	'demo': [],
	'js':[],
	'data':	[
	'extracto_bancario_view.xml',
	# 'account_asset_alter_view.xml'
	],
	'installable': True
}
