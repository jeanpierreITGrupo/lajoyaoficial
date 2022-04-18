# -*- encoding: utf-8 -*-
{
	'name': 'Stock Transfer Restriction IT',
	'category': 'account',
	'author': 'ITGrupo',
	'depends': ['stock_transferir_it'],
	'version': '1.0',
	'description':"""
		Permisos para transferir albaranes
	""",
	'auto_install': False,
	'demo': [],
	'data':	['security/purchase_national_security.xml',
			'account_journal_view.xml'],
	'installable': True
}
