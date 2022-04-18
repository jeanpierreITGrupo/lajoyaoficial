# -*- coding: utf-8 -*-

from openerp import models, fields, api
import base64
from openerp.osv import osv
from openerp import netsvc


class account_analiticas_meses(models.Model):
	_name = 'account.analiticas.meses'
	_auto = False

	cuenta = fields.Char('Cuenta')
	descrip = fields.Char('Nomenclatura')
	apertura=fields.Float('Apertura',digits=(12,2))
	enero = fields.Float('Enero',digits=(12,2))
	febrero = fields.Float('Febrero',digits=(12,2))
	marzo = fields.Float('Marzo',digits=(12,2))
	abril = fields.Float('Abril',digits=(12,2))
	mayo = fields.Float('Mayo',digits=(12,2))
	junio = fields.Float('Junio',digits=(12,2))
	julio = fields.Float('Julio',digits=(12,2))
	agosto = fields.Float('Agosto',digits=(12,2))
	setiembre = fields.Float('Septiembre',digits=(12,2))
	octubre = fields.Float('Octubre',digits=(12,2))
	noviembre = fields.Float('Noviembre',digits=(12,2))
	diciembre = fields.Float('Diciembre',digits=(12,2))
	total = fields.Float('Total',digits=(12,2))

	_order = 'cuenta'

class account_analiticas_meses_wizard(models.Model):
	_name = 'account.analiticas.meses.wizard'

	fiscalyear_id = fields.Many2one('account.fiscalyear','Año Fiscal',required=True)
	
	

	@api.multi
	def do_rebuild(self):
		ft = self.env['account.period'].search([('code','=','00/'+ self.fiscalyear_id.name)])
		f0 = str(ft[0].id) if len(ft)>0 else '0'
		ft = self.env['account.period'].search([('code','=','01/'+ self.fiscalyear_id.name)])
		f1 = str(ft[0].id) if len(ft)>0 else '0'
		ft = self.env['account.period'].search([('code','=','02/'+ self.fiscalyear_id.name)])
		f2 = str(ft[0].id) if len(ft)>0 else '0'
		ft = self.env['account.period'].search([('code','=','03/'+ self.fiscalyear_id.name)])
		f3 = str(ft[0].id) if len(ft)>0 else '0'
		ft = self.env['account.period'].search([('code','=','04/'+ self.fiscalyear_id.name)])
		f4 = str(ft[0].id) if len(ft)>0 else '0'
		ft = self.env['account.period'].search([('code','=','05/'+ self.fiscalyear_id.name)])
		f5 = str(ft[0].id) if len(ft)>0 else '0'
		ft = self.env['account.period'].search([('code','=','06/'+ self.fiscalyear_id.name)])
		f6 = str(ft[0].id) if len(ft)>0 else '0'
		ft = self.env['account.period'].search([('code','=','07/'+ self.fiscalyear_id.name)])
		f7 = str(ft[0].id) if len(ft)>0 else '0'
		ft = self.env['account.period'].search([('code','=','08/'+ self.fiscalyear_id.name)])
		f8 = str(ft[0].id) if len(ft)>0 else '0'
		ft = self.env['account.period'].search([('code','=','09/'+ self.fiscalyear_id.name)])
		f9 = str(ft[0].id) if len(ft)>0 else '0'
		ft = self.env['account.period'].search([('code','=','10/'+ self.fiscalyear_id.name)])
		f10 = str(ft[0].id) if len(ft)>0 else '0'
		ft = self.env['account.period'].search([('code','=','11/'+ self.fiscalyear_id.name)])
		f11 = str(ft[0].id) if len(ft)>0 else '0'
		ft = self.env['account.period'].search([('code','=','12/'+ self.fiscalyear_id.name)])
		f12 = str(ft[0].id) if len(ft)>0 else '0'

		

		self.env.cr.execute(""" drop view if exists account_analisis_meses;
			CREATE OR REPLACE view account_analiticas_meses as (
			select
id, 
code as cuenta,
name as descrip,
coalesce(0,0.00) as apertura,
coalesce(ene,0.00) as enero,
coalesce(feb,0.00) as febrero,
coalesce(mar,0.00) as marzo,
coalesce(abr,0.00) as abril,
coalesce(may,0.00) as mayo,
coalesce(jun,0.00) as junio,
coalesce(jul,0.00) as julio,
coalesce(ago,0.00) as agosto,
coalesce(sep,0.00) as setiembre,
coalesce(oct,0.00) as octubre,
coalesce(nov,0.00) as noviembre,
coalesce(dic,0.00) as diciembre,
coalesce(ene,0.00)+coalesce(feb,0.00)+coalesce(mar,0.00)+coalesce(abr,0.00)+coalesce(may,0.00)+coalesce(jun,0.00)+
coalesce(jul,0.00)+coalesce(ago,0.00)+coalesce(sep,0.00)+coalesce(oct,0.00)+coalesce(nov,0.00)+coalesce(dic,0.00) as total
from account_analytic_account t1


--ENERO
left join 
(
select a1.account_id,-(sum(a1.amount)) as ene from account_analytic_line a1
left join account_move_line a2 on a2.id=a1.move_id
left join account_move a3 on a3.id=a2.move_id
where a3.period_id="""+f1+"""
group by a1.account_id
order by a1.account_id) m1 on m1.account_id=t1.id
--FEBRERO
left join 
(
select a1.account_id,-(sum(a1.amount)) as feb from account_analytic_line a1
left join account_move_line a2 on a2.id=a1.move_id
left join account_move a3 on a3.id=a2.move_id
where a3.period_id="""+f2+"""
group by a1.account_id
order by a1.account_id) m2 on m2.account_id=t1.id

-- MARZO

left join 
(
select a1.account_id,-(sum(a1.amount)) as mar from account_analytic_line a1
left join account_move_line a2 on a2.id=a1.move_id
left join account_move a3 on a3.id=a2.move_id
where a3.period_id="""+f3+"""
group by a1.account_id
order by a1.account_id) m3 on m3.account_id=t1.id

--ABRIL

left join 
(
select a1.account_id,-(sum(a1.amount)) as abr from account_analytic_line a1
left join account_move_line a2 on a2.id=a1.move_id
left join account_move a3 on a3.id=a2.move_id
where a3.period_id="""+f4+"""
group by a1.account_id
order by a1.account_id) m4 on m4.account_id=t1.id
--MAYO
left join 
(
select a1.account_id,-(sum(a1.amount)) as may from account_analytic_line a1
left join account_move_line a2 on a2.id=a1.move_id
left join account_move a3 on a3.id=a2.move_id
where a3.period_id="""+f5+"""
group by a1.account_id
order by a1.account_id) m5 on m5.account_id=t1.id

-- junio

left join 
(
select a1.account_id,-(sum(a1.amount)) as jun from account_analytic_line a1
left join account_move_line a2 on a2.id=a1.move_id
left join account_move a3 on a3.id=a2.move_id
where a3.period_id="""+f6+"""
group by a1.account_id
order by a1.account_id) m6 on m6.account_id=t1.id


--JULIO
left join 
(
select a1.account_id,-(sum(a1.amount)) as jul from account_analytic_line a1
left join account_move_line a2 on a2.id=a1.move_id
left join account_move a3 on a3.id=a2.move_id
where a3.period_id="""+f7+"""
group by a1.account_id
order by a1.account_id) m7 on m7.account_id=t1.id
--agosto
left join 
(
select a1.account_id,-(sum(a1.amount)) as ago from account_analytic_line a1
left join account_move_line a2 on a2.id=a1.move_id
left join account_move a3 on a3.id=a2.move_id
where a3.period_id="""+f8+"""
group by a1.account_id
order by a1.account_id) m8 on m8.account_id=t1.id

-- setiembre

left join 
(
select a1.account_id,-(sum(a1.amount)) as sep from account_analytic_line a1
left join account_move_line a2 on a2.id=a1.move_id
left join account_move a3 on a3.id=a2.move_id
where a3.period_id="""+f9+"""
group by a1.account_id
order by a1.account_id) m9 on m9.account_id=t1.id

--octubre

left join 
(
select a1.account_id,-(sum(a1.amount)) as oct from account_analytic_line a1
left join account_move_line a2 on a2.id=a1.move_id
left join account_move a3 on a3.id=a2.move_id
where a3.period_id="""+f10+"""
group by a1.account_id
order by a1.account_id) m10 on m10.account_id=t1.id
--noviembre
left join 
(
select a1.account_id,-(sum(a1.amount)) as nov from account_analytic_line a1
left join account_move_line a2 on a2.id=a1.move_id
left join account_move a3 on a3.id=a2.move_id
where a3.period_id="""+f11+"""
group by a1.account_id
order by a1.account_id) m11 on m11.account_id=t1.id

-- diciembre

left join 
(
select a1.account_id,-(sum(a1.amount)) as dic from account_analytic_line a1
left join account_move_line a2 on a2.id=a1.move_id
left join account_move a3 on a3.id=a2.move_id
where a3.period_id="""+f12+"""54
group by a1.account_id
order by a1.account_id) m12 on m12.account_id=t1.id

where t1.type='normal' and
(ene<>0 or feb<>0 or mar<>0 or abr<>0 or may<>0 or jun<>0 or jul <>0 or ago<>0 or sep<>0 or oct<>0 or nov<>0 or dic<>0)	
		)     """)
		

		return {
			'type': 'ir.actions.act_window',
			'res_model': 'account.analiticas.meses',
			'view_mode': 'tree',
			'view_type': 'form',			
		}

