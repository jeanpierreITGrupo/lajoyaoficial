# -*- coding: utf-8 -*-

from openerp import models, fields, api

class analisis_cuenta(models.Model):

	_name='analisis.cuenta'
	_auto = False


	periodo = fields.Text(string='Periodo')
	period_code = fields.Text(string='Periodo')
	diario = fields.Text(string='Diario')
	voucher = fields.Text(string='Voucher')
	rubro = fields.Text(string='Rubro')
	cuenta = fields.Text(string='Cuenta')
	debe = fields.Float(string='Debe', digits=(12,2))
	haber = fields.Float(string='Haber', digits=(12,2))
	saldo = fields.Float(string='Saldo', digits=(12,2))

	def init(self,cr):
		cr.execute("""
			DROP VIEW IF EXISTS analisis_cuenta;
			create or replace view analisis_cuenta as (

select row_number() OVER () AS id,* from
(
	select account_period.name as periodo,account_journal.name as diario,account_move.name as voucher,account_account_type.name as rubro,account_account.code as cuenta, account_move_line.debit as debe, account_move_line.credit AS haber,
account_period.code as period_code, account_move_line.debit - account_move_line.credit as saldo
 from account_move_line
left join account_move on account_move.id= account_move_line.move_id 
left join account_account on account_account.id = account_move_line.account_id 
left join account_account_type on account_account_type.id = account_account.user_type
left join account_period on account_period.id = account_move.period_id
left join account_journal on account_journal.id = account_move.journal_id

WHERE account_move.state='posted'

order by account_period.code, cuenta, voucher) T

						)""")

