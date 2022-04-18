# -*- coding: utf-8 -*-

from openerp import models, fields, api


class account_sheet_work_analisis_ht(models.Model):
	_name = 'account.sheet.work.analisis.ht'
	_auto = False


	ee_ff_peru = fields.Char('EE FF Peru')

	nivel1 = fields.Char('Nivel 1')
	nivel2 = fields.Char('Nivel 2')
	nivel3 = fields.Char('Nivel 3')
	nivel4 = fields.Char('Nivel 4')
	cuenta= fields.Char('Cuenta', size=200)
	descripcion= fields.Char('Descripción', size=200)
	debe = fields.Float('Debe', digits=(12,2))
	haber = fields.Float('Haber', digits=(12,2))
	saldodeudor = fields.Float('Saldo Deudo', digits=(12,2))
	saldoacredor = fields.Float('Saldo Acreedor', digits=(12,2))
	activo = fields.Float('Activo', digits=(12,2))
	pasivo = fields.Float('Pasivo', digits=(12,2))
	perdidasnat = fields.Float('Perdidas Nat.', digits=(12,2))
	ganancianat = fields.Float('Ganancia Nat.', digits=(12,2))
	perdidasfun = fields.Float('Perdidas Fun.', digits=(12,2))
	gananciafun = fields.Float('Ganancia Fun.', digits=(12,2))
