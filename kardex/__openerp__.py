# -*- encoding: utf-8 -*-
{
	'name': 'Kardex',
	'version': '1.0',
	'author': 'ITGrupo',
	'website': '',
	'category': 'account',
	'depends': ['account', 'stock_account','stock_picking_motive','account_purchase_compare_it'],
	'description': """KARDEX""",
	'demo': [],
	'data': [
		'stock_move_view.xml',
		'stock_picking_view.xml',
		'wizard/make_kardex_view.xml',
		'wizard/kardex_rev_view.xml',
		'wizard/kardex_account_purchase_view.xml',
		'wizard/kardex_vs_account_line_view.xml'
	],
	'auto_install': False,
	'installable': True
}

