# -*- coding: utf-8 -*-

from openerp import models, fields, api


class account_sheet_work_simple(models.Model):
	_name = 'account.sheet.work.simple'
	_auto = False

	cuenta= fields.Char('Cuenta', size=200)
	descripcion= fields.Char('Descripción', size=200)
	debe = fields.Float('Debe', digits=(12,2))
	haber = fields.Float('Haber', digits=(12,2))
	saldodeudor = fields.Float('Saldo Deudo', digits=(12,2))
	saldoacredor = fields.Float('Saldo Acreedor', digits=(12,2))

	debec = fields.Float('Debe', digits=(12,2))
	haberc = fields.Float('Haber', digits=(12,2))
	saldodeudorc = fields.Float('Saldo Deudo', digits=(12,2))
	saldoacredorc = fields.Float('Saldo Acreedor', digits=(12,2))