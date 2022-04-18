# -*- encoding: utf-8 -*-
{
	'name': 'Account Sequence Journal IT',
	'category': 'account',
	'author': 'ITGrupo',
	'depends': ['account','account_voucher','repaccount_move_line_it','account_invoice_sequence_by_period'],
	'version': '1.0',
	'description':"""
		Generar Secuencia a los Diarios
	""",
	'auto_install': False,
	'demo': [],
	'data':	['wizard/account_sequence_journal_wizard_view.xml'],
	'installable': True
}
