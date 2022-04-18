# -*- encoding: utf-8 -*-
{
	'name': 'Account Contable Book IT',
	'category': 'account',
	'author': 'ITGrupo',
	'depends': ['account','account_voucher','account_tables_it','account_type_doc_it','currency_sunat_change_it','partner_name_it','finantial_convertion_it'],
	'version': '1.0',
	'description':"""

	GENERAR PARA LIBRO DIARIO
	""",
	'auto_install': False,
	'demo': [],
	'data':	['account_move_line_book_view.xml','wizard/account_move_line_book_wizard_view.xml','wizard/account_move_line_book_report_wizard_view.xml','view/report_contable_book.xml'],
	'installable': True
}
