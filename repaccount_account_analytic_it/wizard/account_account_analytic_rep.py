# -*- coding: utf-8 -*-

from openerp import models, fields, api

class account_account_analytic_rep(models.Model):

	_name='account.account.analytic.rep'
	_auto = False

	periodo = fields.Char(string='Periodo',size=30)
	libro = fields.Char(string='Libro',size=30)
	voucher = fields.Char(string='Voucher',size=30)
	fecha = fields.Date('Fecha')
	partner = fields.Char(string='Partner',size=100)
	comprobante = fields.Char(string='Comprobante',size=100)
	tipo = fields.Char(string='TC',size=100)
	cuenta = fields.Char(string='Cuenta Financiera',size=100)
	debe = fields.Float('Debe',digits=(12,2))
	haber = fields.Float('Haber',digits=(12,2))
	divisa = fields.Char(string='Divisa', size=30)
	importedivisa = fields.Float(string='Importe Divisa', digits=(12,2))
	ruc = fields.Char(string='RUC',size=11)
	ctaanalitica = fields.Char(string='Cta. Analítica',size=100)
	destinodebe = fields.Char(string='Destino Debe',size=100)
	destinohaber = fields.Char(string='Destino Haber',size=100)
	glosa = fields.Char(string='Glosa',size=100)
	fecha_ini = fields.Date('Fecha')
	fecha_fin = fields.Date('Fecha')
	
	def init(self,cr):
		cr.execute("""
			create or replace view account_account_analytic_rep as (


select row_number() OVER() as id,* from
(












select 
res_currency.name as divisa,
account_move_line.amount_currency as importedivisa,
res_partner.type_number as ruc,
account_period.name as periodo,
account_move.date as fecha,
account_journal.code as libro,
itd.code as tipo,
account_move.name as voucher,
res_partner.display_name as partner,
account_move_line.nro_comprobante as comprobante,
aa1.code as cuenta,
account_move_line.debit as debe,
account_move_line.credit as haber,
account_analytic_account.code as ctaanalitica,
aa3.code as destinodebe,
aa2.code as destinohaber,
account_move_line.name as glosa,
account_period.date_start as fecha_ini,
account_period.date_stop as fecha_fin

from account_move
inner join account_period on account_move.period_id = account_period.id
inner join account_journal on account_move.journal_id = account_journal.id
inner join account_move_line on account_move_line.move_id = account_move.id   ----154
inner join account_account aa1 on aa1.id = account_move_line.account_id
left join it_type_document itd on itd.id = account_move_line.type_document_id
left join res_currency on res_currency.id = account_move_line.currency_id
left join res_partner on account_move_line.partner_id = res_partner.id
left join account_analytic_account on account_analytic_account.id = account_move_line.analytic_account_id
left join account_account aa2 on aa2.id = (CASE WHEN aa1.account_analytic_account_moorage_id IS NOT NULL THEN aa1.account_analytic_account_moorage_id ELSE account_analytic_account.account_account_moorage_credit_id END )
left join account_account aa3 on aa3.id = (CASE WHEN aa1.account_analytic_account_moorage_debit_id IS NOT NULL THEN aa1.account_analytic_account_moorage_debit_id ELSE  account_analytic_account.account_account_moorage_id END)

where account_move.state = 'posted'
and (aa2.id >0 or aa3.id >0) and aa1.type != 'view' and account_analytic_account.id is null and account_move_line.analytics_id is null


union all

select 

res_currency.name as divisa,
aml.amount_currency as importedivisa,
res_partner.type_number as ruc,
ap.name as periodo,
am.date as fecha,
account_journal.code as libro,
itd.code as tipo,
am.name as voucher,
res_partner.display_name as partner,
aml.nro_comprobante as comprobante,
aa1.code as cuenta,
CASE WHEN aal.amount <0 THEN -1*aal.amount ELSE 0 END as debe,
CASE WHEN aal.amount >0 THEN aal.amount ELSE 0 END as haber,
account_analytic_account.code as ctaanalitica,
aa3.code as destinodebe,
aa2.code as destinohaber,
aml.name as glosa,
ap.date_start as fecha_ini,
ap.date_stop as fecha_fin

from account_analytic_line aal
inner join account_account aa1 on aa1.id = aal.general_account_id
inner join account_move_line aml on aml.id = aal.move_id
inner join account_move am on am.id = aml.move_id
inner join account_journal on am.journal_id = account_journal.id
left join it_type_document itd on itd.id = aml.type_document_id
left join res_currency on res_currency.id = aml.currency_id
left join res_partner on aml.partner_id = res_partner.id
left join account_analytic_account on account_analytic_account.id = aal.account_id
inner join account_account aa2 on aa2.id = (CASE WHEN aa1.account_analytic_account_moorage_id IS NOT NULL THEN aa1.account_analytic_account_moorage_id ELSE account_analytic_account.account_account_moorage_credit_id END )
inner join account_account aa3 on aa3.id = (CASE WHEN aa1.account_analytic_account_moorage_debit_id IS NOT NULL THEN aa1.account_analytic_account_moorage_debit_id ELSE  account_analytic_account.account_account_moorage_id END)
inner join account_period ap on ap.id = am.period_id
where aa1.check_moorage = True  and am.state != 'draft'
order by periodo, libro, voucher

) as T


						)""")





class account_account_analytic_rep_contable_unico(models.Model):
	_name='account.account.analytic.rep.contable.unico'
	_auto = False
	period = fields.Integer(string='Periodo')
	debe = fields.Float('Debe',digits=(12,2))
	haber = fields.Float('Haber',digits=(12,2))
	cuenta = fields.Integer('existencia')

	def init(self,cr):
		cr.execute("""
			create or replace view account_account_analytic_rep_contable_unico as (


select row_number() OVER() as id,*
from(
select cuenta, period, 
CASE WHEN sum(debe)-sum(haber)>0 THEN sum(debe)-sum(haber) else 0 END as debe,
CASE WHEN -sum(debe)+sum(haber)>0 THEN -sum(debe)+sum(haber) else 0 END as haber from 
(
select 
aa3.id as cuenta,
account_period.id as period,
case when sum(account_move_line.debit) - sum(account_move_line.credit) > 0 then sum(account_move_line.debit) - sum(account_move_line.credit)
else 0 end as debe,
case when sum(account_move_line.debit) - sum(account_move_line.credit) > 0 then 0
else -sum(account_move_line.debit) + sum(account_move_line.credit) end as haber
from account_move
inner join account_period on account_move.period_id = account_period.id
inner join account_journal on account_move.journal_id = account_journal.id
inner join account_move_line on account_move_line.move_id = account_move.id   ----154
inner join account_account aa1 on aa1.id = account_move_line.account_id
left join account_analytic_account on account_analytic_account.id = account_move_line.analytic_account_id
inner join account_account aa2 on aa2.id = (CASE WHEN aa1.account_analytic_account_moorage_id IS NOT NULL THEN aa1.account_analytic_account_moorage_id ELSE account_analytic_account.account_account_moorage_credit_id END )
inner join account_account aa3 on aa3.id = (CASE WHEN aa1.account_analytic_account_moorage_debit_id IS NOT NULL THEN aa1.account_analytic_account_moorage_debit_id ELSE  account_analytic_account.account_account_moorage_id END)
where account_move.state = 'posted'
and aa2.id is not null and aa3.id is not null and account_analytic_account.id is null and account_move_line.analytics_id is null
and aa1.type != 'view' 
group by account_period.id, aa3.id

union all


select 
aa3.id as cuenta,
ap.id as period,

case when aal.amount > 0 then 0
else -1*aal.amount end as debe,

case when aal.amount > 0 then aal.amount
else 0 end as haber
from account_analytic_line aal
inner join account_account aa1 on aa1.id = aal.general_account_id
inner join account_move_line aml on aml.id = aal.move_id
inner join account_move am on am.id = aml.move_id
left join account_analytic_account on account_analytic_account.id = aal.account_id
inner join account_account aa2 on aa2.id = (CASE WHEN aa1.account_analytic_account_moorage_id IS NOT NULL THEN aa1.account_analytic_account_moorage_id ELSE account_analytic_account.account_account_moorage_credit_id END )
inner join account_account aa3 on aa3.id = (CASE WHEN aa1.account_analytic_account_moorage_debit_id IS NOT NULL THEN aa1.account_analytic_account_moorage_debit_id ELSE  account_analytic_account.account_account_moorage_id END)
inner join account_period ap on ap.id = am.period_id
where aa1.check_moorage = True  and am.state != 'draft'


union all


select 
aa2.id as cuenta,
ap.id as period,

case when aal.amount > 0 then aal.amount
else 0 end as debe,
case when aal.amount > 0 then 0
else -1*aal.amount end as haber
from account_analytic_line aal
inner join account_account aa1 on aa1.id = aal.general_account_id
inner join account_move_line aml on aml.id = aal.move_id
inner join account_move am on am.id = aml.move_id
left join account_analytic_account on account_analytic_account.id = aal.account_id
inner join account_account aa2 on aa2.id = (CASE WHEN aa1.account_analytic_account_moorage_id IS NOT NULL THEN aa1.account_analytic_account_moorage_id ELSE account_analytic_account.account_account_moorage_credit_id END )
inner join account_account aa3 on aa3.id = (CASE WHEN aa1.account_analytic_account_moorage_debit_id IS NOT NULL THEN aa1.account_analytic_account_moorage_debit_id ELSE  account_analytic_account.account_account_moorage_id END)
inner join account_period ap on ap.id = am.period_id
where aa1.check_moorage = True and am.state != 'draft'


union all
select 
aa2.id as cuenta,
account_period.id as period,
case when sum(account_move_line.debit) - sum(account_move_line.credit) > 0 then 0
else -sum(account_move_line.debit) + sum(account_move_line.credit) end as debe,
case when sum(account_move_line.debit) - sum(account_move_line.credit) > 0 then sum(account_move_line.debit) - sum(account_move_line.credit)
else 0 end as haber

from account_move
inner join account_period on account_move.period_id = account_period.id
inner join account_journal on account_move.journal_id = account_journal.id
inner join account_move_line on account_move_line.move_id = account_move.id   ----154
inner join account_account aa1 on aa1.id = account_move_line.account_id
left join account_analytic_account on account_analytic_account.id = account_move_line.analytic_account_id
inner join account_account aa2 on aa2.id = (CASE WHEN aa1.account_analytic_account_moorage_id IS NOT NULL THEN aa1.account_analytic_account_moorage_id ELSE account_analytic_account.account_account_moorage_credit_id END )
inner join account_account aa3 on aa3.id = (CASE WHEN aa1.account_analytic_account_moorage_debit_id IS NOT NULL THEN aa1.account_analytic_account_moorage_debit_id ELSE  account_analytic_account.account_account_moorage_id END)
where account_move.state = 'posted' 
and aa2.id is not null and aa3.id is not null and account_analytic_account.id is null and account_move_line.analytics_id is null
and aa1.type != 'view'
group by account_period.id, aa2.id

order by period,haber,debe
) AS M

group by period, cuenta
order by period,haber,debe
) AS T



)""")


