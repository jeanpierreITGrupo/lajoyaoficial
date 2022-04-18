# -*- encoding: utf-8 -*-
{
	'name': 'Account Move Advance Add IT',
	'category': 'account',
	'author': 'ITGrupo',
	'depends': ['account','account_tables_it','account_type_doc_it','account_contable_book_it','account_move_analytic_it','purchase_order_liquidation_mod_it'],
	'version': '1.0',
	'description':"""
	Agrega lineas a los asientos contables con un wizard dinamico
	Imprime Asientos Contables en Excel
	""",
	'auto_install': False,
	'demo': [],
	'data':	['account_move_view.xml'],
	'installable': True
}
