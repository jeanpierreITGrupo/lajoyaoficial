# -*- coding: utf-8 -*-

from openerp import models, fields, api

class account_expense_rep(models.Model):
	_name='account.expense.rep'
	_auto = False

	divisa = fields.Char(string='Divisa', size=30)
	period = fields.Char(string='Periodo',size=30)
	libro = fields.Char(string='Libro',size=30)
	voucher = fields.Char('Voucher',size=30)
	fecha = fields.Date('Fecha')
	tipo = fields.Char('Tipo',size=30)
	comprobante = fields.Char('Numero Comprobante',size=30)
	ruc = fields.Char('RUC',size=20)
	proveedor = fields.Char(string='Proveedor',size=100)
	producto = fields.Char(string='Producto',size=100)
	debe = fields.Float('Debe',digits=(12,2))
	haber = fields.Float('Haber',digits=(12,2))
	existencias = fields.Char('Cta_Var Existencias',size=32)
	existenciasid = fields.Integer('ExistenciaID')
	valuacion = fields.Char('Cuenta Valuacion',size=32)
	start = fields.Date('Fecha Inicio')
	stop = fields.Date('Fecha Fin')
	tipoproducto = fields.Char('Tipo de Producto',size=32)

	def init(self,cr):
		cr.execute("""
			create or replace view account_expense_rep as (

select row_number() OVER() as id,* from (
	select 
rc.name as divisa,
ap.name as period,
aer.date as fecha,
aj.code as libro,
ai.internal_number as voucher,
itd.description as tipo,
ai.supplier_invoice_number as comprobante,
rp.type_number as ruc,
rp.name as proveedor,
product_product.name_template as producto,
aa1.code as existencias,
aa1.id as existenciasid,
aa2.code as valuacion,
ap.date_start as start,
ap.date_stop as stop,
aerl.equivalence as debe,
CASE WHEN product_template.type = 'product' THEN 'Almacenable' 
WHEN product_template.type = 'consu' THEN 'Consumible' 
WHEN product_template.type = 'service' THEN 'Servicio'  END as tipoproducto,
0 as haber
from account_expense_related aer
inner join account_expense_related_line aerl on aerl.expense_related_id=aer.id
inner join account_invoice ai on ai.id = aer.invoice_id
inner join product_product on aerl.product_id = product_product.id
inner join product_template on product_template.id = product_product.product_tmpl_id
inner join product_category on product_category.id = product_template.categ_id
inner join ir_property ip1 on ip1.res_id = 'product.category,' || product_category.id
inner join account_account aa1 on aa1.id = substring(ip1.value_reference from 17)::int8
inner join ir_property ip2 on ip2.res_id = 'product.category,' || product_category.id
inner join account_account aa2 on aa2.id = substring(ip2.value_reference from 17)::int8
inner join account_period ap on ap.id = aer.period_id
inner join account_journal aj on aj.id = ai.journal_id
left join it_type_document itd on itd.id = ai.type_document_id
left join res_currency rc on rc.id= aer.currency_id
left join res_partner rp on rp.id = ai.partner_id
where ip1.name = 'property_stock_account_input_categ' and ip2.name = 'property_stock_valuation_account_id' and product_category.type = 'normal'
and product_template.type = 'product'  and ai.state!='draft'
order by fecha,tipo,comprobante

) AS T
						)""")






class account_expense_asiento_contable_unico(models.Model):
	_name='account.expense.asiento.contable.unico'
	_auto = False
	period = fields.Integer(string='Periodo')
	debe = fields.Float('Debe',digits=(12,2))
	haber = fields.Float('Haber',digits=(12,2))
	cuenta = fields.Integer('existencia')

	def init(self,cr):
		cr.execute("""
			create or replace view account_expense_asiento_contable_unico as (



select row_number() OVER() as id,* from
(
select * from (
(select 
aer.period_id as period,
aa2.id as cuenta,
sum(aerl.equivalence) as debe,
0 as haber


from account_expense_related aer
inner join account_expense_related_line aerl on aerl.expense_related_id=aer.id
inner join account_invoice ai on ai.id = aer.invoice_id

inner join product_product on aerl.product_id = product_product.id

inner join product_template on product_template.id = product_product.product_tmpl_id
inner join product_category on product_category.id = product_template.categ_id
inner join ir_property ip1 on ip1.res_id = 'product.category,' || product_category.id
inner join account_account aa1 on aa1.id = substring(ip1.value_reference from 17)::int8
inner join ir_property ip2 on ip2.res_id = 'product.category,' || product_category.id
inner join account_account aa2 on aa2.id = substring(ip2.value_reference from 17)::int8
where ip1.name = 'property_stock_account_input_categ' and ip2.name = 'property_stock_valuation_account_id' and product_category.type = 'normal'
and product_template.type = 'product'  and ai.state!='draft'
group by period, cuenta
order by period, cuenta
)
union all
(
select 
aer.period_id as period,
aa1.id as cuenta,
0 as debe,
sum(aerl.equivalence) as haber


from account_expense_related aer
inner join account_expense_related_line aerl on aerl.expense_related_id=aer.id
inner join account_invoice ai on ai.id = aer.invoice_id

inner join product_product on aerl.product_id = product_product.id

inner join product_template on product_template.id = product_product.product_tmpl_id
inner join product_category on product_category.id = product_template.categ_id
inner join ir_property ip1 on ip1.res_id = 'product.category,' || product_category.id
inner join account_account aa1 on aa1.id = substring(ip1.value_reference from 17)::int8
inner join ir_property ip2 on ip2.res_id = 'product.category,' || product_category.id
inner join account_account aa2 on aa2.id = substring(ip2.value_reference from 17)::int8
where ip1.name = 'property_stock_account_input_categ' and ip2.name = 'property_stock_valuation_account_id' and product_category.type = 'normal'
and product_template.type = 'product'  and ai.state!='draft'
group by period, cuenta
order by period, cuenta)) AS T
order by period,haber,debe


) as T
						)""")





class account_move_line_asiento_contable_unico(models.Model):
	_name='account.move.line.asiento.contable.unico'
	_auto = False
	period = fields.Integer(string='Periodo')
	debe = fields.Float('Debe',digits=(12,2))
	haber = fields.Float('Haber',digits=(12,2))
	cuenta = fields.Integer('existencia')

	def init(self,cr):
		cr.execute("""
			drop view if exists account_move_line_asiento_contable_unico;
			create or replace view account_move_line_asiento_contable_unico as (


select row_number() OVER() as id,* from
(
select * from (
(
select period,cuenta, sum(debe) as debe, sum(haber) as haber from (
(select 
aer.period_id as period,
aa2.id as cuenta,
aerl.equivalence as debe,
0 as haber


from account_expense_related aer
inner join account_expense_related_line aerl on aerl.expense_related_id=aer.id
inner join account_invoice ai on ai.id = aer.invoice_id

inner join product_product on aerl.product_id = product_product.id

inner join product_template on product_template.id = product_product.product_tmpl_id
inner join product_category on product_category.id = product_template.categ_id
inner join ir_property ip1 on ip1.res_id = 'product.category,' || product_category.id
inner join account_account aa1 on aa1.id = substring(ip1.value_reference from 17)::int8
inner join ir_property ip2 on ip2.res_id = 'product.category,' || product_category.id
inner join account_account aa2 on aa2.id = substring(ip2.value_reference from 17)::int8
where ip1.name = 'property_stock_account_input_categ' and ip2.name = 'property_stock_valuation_account_id' and product_category.type = 'normal'
and product_template.type = 'product'  and ai.state!='draft')
union all
(
select 
account_period.id as period,
aa2.id as cuenta,
case when (account_move_line.debit) - (account_move_line.credit) > 0 then (account_move_line.debit) - (account_move_line.credit)
else 0 end as debe,
case when (account_move_line.debit) - (account_move_line.credit) > 0 then 0
else -(account_move_line.debit) + (account_move_line.credit) end as haber

from account_move_line
inner join account_account aafinanciera on account_move_line.account_id = aafinanciera.id
inner join account_move on account_move.id = account_move_line.move_id
inner join account_period on account_move_line.period_id = account_period.id
inner join account_journal on account_move_line.journal_id = account_journal.id
inner join res_partner on account_move_line.partner_id  = res_partner.id
inner join product_product on account_move_line.product_id = product_product.id

inner join product_template on product_template.id = product_product.product_tmpl_id
inner join product_category on product_category.id = product_template.categ_id
inner join ir_property ip1 on ip1.res_id = 'product.category,' || product_category.id
inner join account_account aa1 on aa1.id = substring(ip1.value_reference from 17)::int8
inner join ir_property ip2 on ip2.res_id = 'product.category,' || product_category.id
inner join account_account aa2 on aa2.id = substring(ip2.value_reference from 17)::int8
where account_move_line.product_id is not Null and ip1.name = 'property_stock_account_input_categ' and ip2.name = 'property_stock_valuation_account_id' and product_category.type = 'normal'
and account_move_line.account_id != aa2.id and account_move_line.account_id != aa1.id
and account_journal.type != 'sale' and account_journal.type !='sale_refund'
and product_template.type = 'product'  and account_move.state='posted'
)) AS T1
group by period, cuenta
order by period, cuenta
)
union all
(
select period,cuenta,sum(debe) as debe, sum(haber) as haber from
((
select 
aer.period_id as period,
aa1.id as cuenta,
0 as debe,
aerl.equivalence as haber


from account_expense_related aer
inner join account_expense_related_line aerl on aerl.expense_related_id=aer.id
inner join account_invoice ai on ai.id = aer.invoice_id

inner join product_product on aerl.product_id = product_product.id

inner join product_template on product_template.id = product_product.product_tmpl_id
inner join product_category on product_category.id = product_template.categ_id
inner join ir_property ip1 on ip1.res_id = 'product.category,' || product_category.id
inner join account_account aa1 on aa1.id = substring(ip1.value_reference from 17)::int8
inner join ir_property ip2 on ip2.res_id = 'product.category,' || product_category.id
inner join account_account aa2 on aa2.id = substring(ip2.value_reference from 17)::int8
where ip1.name = 'property_stock_account_input_categ' and ip2.name = 'property_stock_valuation_account_id' and product_category.type = 'normal'
and product_template.type = 'product'  and ai.state!='draft')

union all
(
select 
account_period.id as period,
aa1.id as cuenta,
case when (account_move_line.debit) - (account_move_line.credit) > 0 then 0
else -(account_move_line.debit) + (account_move_line.credit) end as debe,
case when (account_move_line.debit) - (account_move_line.credit) > 0 then (account_move_line.debit) - (account_move_line.credit)
else 0 end as haber

from account_move_line
inner join account_account aafinanciera on account_move_line.account_id = aafinanciera.id
inner join account_move on account_move.id = account_move_line.move_id
inner join account_period on account_move_line.period_id = account_period.id
inner join account_journal on account_move_line.journal_id = account_journal.id
inner join res_partner on account_move_line.partner_id  = res_partner.id
inner join product_product on account_move_line.product_id = product_product.id

inner join product_template on product_template.id = product_product.product_tmpl_id
inner join product_category on product_category.id = product_template.categ_id
inner join ir_property ip1 on ip1.res_id = 'product.category,' || product_category.id
inner join account_account aa1 on aa1.id = substring(ip1.value_reference from 17)::int8
inner join ir_property ip2 on ip2.res_id = 'product.category,' || product_category.id
inner join account_account aa2 on aa2.id = substring(ip2.value_reference from 17)::int8
where account_move_line.product_id is not Null and ip1.name = 'property_stock_account_input_categ' and ip2.name = 'property_stock_valuation_account_id' and product_category.type = 'normal'
and account_move_line.account_id != aa2.id and account_move_line.account_id != aa1.id
and account_journal.type != 'sale' and account_journal.type !='sale_refund'
and product_template.type = 'product'  and account_move.state='posted')
) AS TT1
group by period, cuenta
order by period, cuenta)) AS T
order by period,haber,debe ) AS M

						)""")



class account_move_line_rep(models.Model):
	_name='account.move.line.rep'
	_auto = False

	divisa = fields.Char(string='Divisa', size=30)
	importedivisa = fields.Float(string='Importe Divisa', digits=(12,2))
	period = fields.Char(string='Periodo',size=30)
	libro = fields.Char(string='Libro',size=30)
	voucher = fields.Char('Voucher',size=30)
	fecha = fields.Date('Fecha')
	tipo = fields.Char('Tipo',size=30)
	comprobante = fields.Char('Numero Comprobante',size=30)
	ruc = fields.Char('RUC',size=20)
	proveedor = fields.Char(string='Proveedor',size=100)
	producto = fields.Char(string='Producto',size=100)
	financiera = fields.Char(string='Cuenta Financiera',size=100)
	debe = fields.Float('Debe',digits=(12,2))
	haber = fields.Float('Haber',digits=(12,2))
	existencias = fields.Char('Cta_Var Existencias',size=32)
	existenciasid = fields.Integer('ExistenciaID')
	valuacion = fields.Char('Cuenta Valuacion',size=32)
	start = fields.Date('Fecha Inicio')
	stop = fields.Date('Fecha Fin')
	tipoproducto = fields.Char('Tipo de Producto',size=32)
	gastov = fields.Boolean('Gasto Vin.')

	def init(self,cr):
		cr.execute("""
			drop view if exists account_move_line_rep;
			create or replace view account_move_line_rep as (


				select row_number() OVER() as id,* from (
	select row_number() OVER() as id2, 
rc.name as divisa,
Null::numeric as importedivisa,
ap.name as period,
aj.code as libro,
ai.internal_number as voucher,
aer.date as fecha,
itd.description as tipo,
ai.supplier_invoice_number as comprobante,
rp.type_number as ruc,
rp.name as proveedor,
product_product.name_template as producto,
Null::varchar as financiera,
aerl.equivalence as debe,
0 as haber,

aa1.code as existencias,
aa1.id as existenciasid,
aa2.code as valuacion,
ap.date_start as start,
ap.date_stop as stop,
CASE WHEN product_template.type = 'product' THEN 'Almacenable' 
WHEN product_template.type = 'consu' THEN 'Consumible' 
WHEN product_template.type = 'service' THEN 'Servicio'  END as tipoproducto,
true::boolean as gastov
from account_expense_related aer
inner join account_expense_related_line aerl on aerl.expense_related_id=aer.id
inner join account_invoice ai on ai.id = aer.invoice_id
inner join product_product on aerl.product_id = product_product.id
inner join product_template on product_template.id = product_product.product_tmpl_id
inner join product_category on product_category.id = product_template.categ_id
inner join ir_property ip1 on ip1.res_id = 'product.category,' || product_category.id
inner join account_account aa1 on aa1.id = substring(ip1.value_reference from 17)::int8
inner join ir_property ip2 on ip2.res_id = 'product.category,' || product_category.id
inner join account_account aa2 on aa2.id = substring(ip2.value_reference from 17)::int8
inner join account_period ap on ap.id = aer.period_id
inner join account_journal aj on aj.id = ai.journal_id
left join it_type_document itd on itd.id = ai.type_document_id
left join res_currency rc on rc.id= aer.currency_id
left join res_partner rp on rp.id = ai.partner_id
where ip1.name = 'property_stock_account_input_categ' and ip2.name = 'property_stock_valuation_account_id' and product_category.type = 'normal'
and product_template.type = 'product'  and ai.state!='draft'
union all

select * from (
select row_number() OVER() as id2,* from (


select 
res_currency.name as divisa,
account_move_line.amount_currency as importedivisa,
account_period.name as period,
account_journal.code as libro,
account_move.name as voucher,
account_move.date as fecha,
itd.description as tipo,
account_move_line.nro_comprobante as comprobante,
res_partner.type_number as ruc,
res_partner.name as proveedor,
product_product.name_template as producto,  
aafinanciera.code as financiera, 
account_move_line.debit as debe,
account_move_line.credit as haber,
aa1.code as existencias,
aa1.id as existenciasid,
aa2.code as valuacion,
account_period.date_start as start,
account_period.date_stop as stop,
CASE WHEN product_template.type = 'product' THEN 'Almacenable' 
WHEN product_template.type = 'consu' THEN 'Consumible' 
WHEN product_template.type = 'service' THEN 'Servicio'  END as tipoproducto,

false::boolean as gastov
from account_move_line
inner join account_account aafinanciera on account_move_line.account_id = aafinanciera.id
inner join account_move on account_move.id = account_move_line.move_id
inner join account_period on account_move_line.period_id = account_period.id
inner join account_journal on account_move_line.journal_id = account_journal.id
inner join res_partner on account_move_line.partner_id  = res_partner.id

inner join product_product on account_move_line.product_id = product_product.id


inner join product_template on product_template.id = product_product.product_tmpl_id

inner join product_category on product_category.id = product_template.categ_id
left outer join ir_property ip1 on (ip1.res_id = 'product.category,' || COALESCE(product_category.id,-1) or ip1.res_id is Null) and ip1.name = 'property_stock_account_input_categ'
left outer join account_account aa1 on aa1.id = COALESCE( substring(ip1.value_reference from 17)::int8 , -1)
left outer join ir_property ip2 on (ip2.res_id = 'product.category,' || COALESCE(product_category.id,-1) or ip2.res_id is Null) and ip2.name = 'property_stock_valuation_account_id'
left outer join account_account aa2 on aa2.id = COALESCE( substring(ip2.value_reference from 17)::int8, -1)
left outer join res_currency on res_currency.id = account_move_line.currency_id
left outer join it_type_document itd on itd.id = account_move_line.type_document_id
where account_move.state='posted'
and account_journal.type != 'sale' and account_journal.type !='sale_refund'
order by producto,ip1.id, ip2.id ) AS WT ) AS WTR
where id2 in (


select 
max(id) from (
select row_number() OVER() as id,* from (


select 
res_currency.name as divisa,
account_move_line.amount_currency as importedivisa,
account_period.name as period,
account_journal.code as libro,
account_move.name as voucher,
account_move.date as fecha,
itd.description as tipo,
account_move_line.nro_comprobante as comprobante,
res_partner.type_number as ruc,
res_partner.name as proveedor,
product_product.name_template as producto,  
aafinanciera.code as financiera, 
account_move_line.debit as debe,
account_move_line.credit as haber,
aa1.code as existencias,
aa1.id as existenciasid,
aa2.code as valuacion,
account_period.date_start as start,
account_period.date_stop as stop,
CASE WHEN product_template.type = 'product' THEN 'Almacenable' 
WHEN product_template.type = 'consu' THEN 'Consumible' 
WHEN product_template.type = 'service' THEN 'Servicio'  END as tipoproducto
from account_move_line
inner join account_account aafinanciera on account_move_line.account_id = aafinanciera.id
inner join account_move on account_move.id = account_move_line.move_id
inner join account_period on account_move_line.period_id = account_period.id
inner join account_journal on account_move_line.journal_id = account_journal.id
inner join res_partner on account_move_line.partner_id  = res_partner.id

inner join product_product on account_move_line.product_id = product_product.id


inner join product_template on product_template.id = product_product.product_tmpl_id

inner join product_category on product_category.id = product_template.categ_id
left outer join ir_property ip1 on (ip1.res_id = 'product.category,' || COALESCE(product_category.id,-1) or ip1.res_id is Null) and ip1.name = 'property_stock_account_input_categ'
left outer join account_account aa1 on aa1.id = COALESCE( substring(ip1.value_reference from 17)::int8 , -1)
left outer join ir_property ip2 on (ip2.res_id = 'product.category,' || COALESCE(product_category.id,-1) or ip2.res_id is Null) and ip2.name = 'property_stock_valuation_account_id'
left outer join account_account aa2 on aa2.id = COALESCE( substring(ip2.value_reference from 17)::int8, -1)
left outer join res_currency on res_currency.id = account_move_line.currency_id
left outer join it_type_document itd on itd.id = account_move_line.type_document_id
where account_move.state='posted'
and account_journal.type != 'sale' and account_journal.type !='sale_refund'
order by producto,ip1.id, ip2.id ) AS T ) AS W
GROUP BY divisa,importedivisa,period,libro,voucher ,fecha,tipo, comprobante,ruc,proveedor,producto,financiera,debe,haber, start,stop,tipoproducto)

order by fecha,tipo,comprobante

) AS T
		)""")