# -*- encoding: utf-8 -*-
{
	'name': 'PLE Purchase Register IT',
	'category': 'account',
	'author': 'ITGrupo',
	'depends': ['account','account_voucher','account_contable_book_it','account_type_doc_it','ple_diario_sunat_it','account_parameter_it'],
	'version': '1.0',
	'description':"""
		Registro de Compras para el PLE
	""",
	'auto_install': False,
	'demo': [],
	'data':	['wizard/ple_purchase_register_wizard_view.xml'],
	'installable': True
}
