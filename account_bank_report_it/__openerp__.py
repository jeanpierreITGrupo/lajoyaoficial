# -*- encoding: utf-8 -*-
{
	'name': 'Account Contable Cash and Bank IT',
	'category': 'account',
	'author': 'ITGrupo',
	'depends': ['account_contable_book_it','raw_print_config'],
	'version': '1.0',
	'description':"""
	Libro de caja y Bancos

	Menu: 
		-Libro Caja y Bancos
                -Esto es una prueba
	""",
	'auto_install': False,
	'demo': [],
	'data':	['account_move_line_bank_view.xml','wizard/account_move_line_bank_wizard_view.xml'],
	'installable': True
}
