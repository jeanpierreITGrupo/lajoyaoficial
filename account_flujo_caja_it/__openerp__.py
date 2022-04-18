# -*- encoding: utf-8 -*-
{
	'name': 'Flujo Caja IT',
	'category': 'account',
	'author': 'ITGrupo',
	'depends': ['base','account_tables_it','voucher_move_line_it','account_state_financial_it','account_transfer_it','deliveries_to_pay_it'],
	'version': '1.0',
	'description':"""
       Flujo de Caja
	""",
	'auto_install': False,
	'demo': [],
	'data':	['it_ht_sunat_view.xml'],
	'installable': True
}
