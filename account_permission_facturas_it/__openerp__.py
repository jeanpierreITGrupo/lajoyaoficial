# -*- encoding: utf-8 -*-
{
	'name': 'Account Permission IT',
	'category': 'account',
	'author': 'ITGrupo',
	'depends': ['account','account_voucher','account_type_doc_it','currency_sunat_change_it','exchange_diff_it','voucher_credit_card','product'],
	'version': '1.0',
	'description':"""
		Permisos para cambiar valores de Configuracion/
	""",
	'auto_install': False,
	'demo': [],
	'data':	['security/purchase_national_security.xml',
			'account_journal_view.xml'],
	'installable': True
}
