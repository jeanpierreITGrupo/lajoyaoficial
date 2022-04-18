# -*- encoding: utf-8 -*-
{
	'name': 'Account Analytic Book Major IT',
	'category': 'account',
	'author': 'ITGrupo',
	'depends': ['account','account_voucher','account_tables_it','account_type_doc_it','currency_sunat_change_it','partner_name_it','account_contable_book_it'],
	'version': '1.0',
	'description':"""
	Crea el Libro Mayor para contabilidad

	""",
	'auto_install': False,
	'demo': [],
	'data':	['wizard/account_analytic_book_major_wizard_view.xml','account_analytic_book_major_view.xml'],
	'installable': True
}
