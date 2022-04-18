# -*- encoding: utf-8 -*-

from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
import pprint

class account_move(models.Model):
	_inherit = 'account.move'

	asiento_apertura = fields.Boolean('Asiento Apertura')


	@api.multi
	def desconciliar_lineas(selfs):
		id_list = []
		for self in selfs:
			for lineas in self.line_id:
				if lineas.reconcile_id.id and lineas.reconcile_id.opening_reconciliation:
					self.env.cr.execute("""update account_move_line set reconcile_id= null where id = """ + str(lineas.id))

				else:
					id_list.append(lineas.id)
		
		return {
				'context' : {'active_ids':id_list},
				'type': 'ir.actions.act_window',
				'res_model': 'account.unreconcile',
				'view_mode': 'form',
				'view_type': 'form',
				'target': 'new',
				'views': [(False, 'form')],
			}


class account_fiscalyear_close_wizard_it(osv.TransientModel):
	_name='account.fiscalyear.close.wizard.it'

	cuenta_debe = fields.Many2one('account.account','Cuenta Contrapartida para Debe')
	cuenta_haber = fields.Many2one('account.account','Cuenta Contrapartida para Haber')

	tipo_cambio_compra = fields.Float('Tipo de Cambio Compra',digits=(12,3))
	tipo_cambio_venta = fields.Float('Tipo de Cambio Venta',digits=(12,3))

	diario = fields.Many2one('account.journal','Diario')
	fiscalyear_id = fields.Many2one('account.fiscalyear','Año Fiscal de Cierre')
	periodo = fields.Many2one('account.period','Periodo de Apertura')



	@api.multi
	def do_rebuild(self):

		asientoselim = self.env['account.move'].search([('period_id','=',self.periodo.id),('journal_id','=',self.diario.id),('ref','=','Asiento de Saldo Inicial'),('asiento_apertura','=',True)])
		for mlo in asientoselim:
			for amm in mlo.line_id:
				self.env.cr.execute("""update account_move_line set reconcile_id= null where id = """ + str(amm.id))
				amm.refresh()
				amm.unlink()
			mlo.unlink()

		dataC = {
			'period_id':self.periodo.id,
			'journal_id':self.diario.id,
			'ref':'Asiento de Saldo Inicial',
			'date':self.periodo.date_start,
			'asiento_apertura': True,
		}
		t = self.env['account.move'].create(dataC)

		sumdebe= 0
		sumcredit = 0

		self.env.cr.execute("""  
	select 
ap.name as periodo,
am.date as fecha_emision,
rp.id as empresa,
CASE WHEN aa.type= 'payable' THEN 'A pagar'  ELSE 'A cobrar' END as tipo_cuenta,
aa.id,
itd.id as tipo,
aml.nro_comprobante as nro_comprobante,
T.debe,
T.haber,
T.saldo,
rc.name as divisa,
T.amount_currency,
facturas.date_due as fechavencimiento
from (
select concat(account_move_line.partner_id,account_id,type_document_id,nro_comprobante) as identifica,min(account_move_line.id),sum(debit)as debe,sum(credit) as haber, sum(debit)-sum(credit) as saldo, sum(amount_currency) as amount_currency from account_move_line
inner join account_move ami on ami.id = account_move_line.move_id
inner join account_period api on api.id = ami.period_id
left join account_account on account_account.id=account_move_line.account_id
where account_account.reconcile = true and (account_account.type='receivable' or account_account.type='payable' ) and ami.state != 'draft'
and periodo_num(api.code) >= periodo_num('00/""" + str(self.fiscalyear_id.name) + """') and periodo_num(api.code) <= periodo_num('13/""" + str(self.fiscalyear_id.name) + """')
group by identifica) as T
inner join account_move_line aml on aml.id = T.min
inner join account_move am on am.id = aml.move_id
inner join account_period ap on ap.id = am.period_id
left join res_partner rp on rp.id = aml.partner_id
left join it_type_document itd on itd.id = aml.type_document_id
left join res_currency rc on rc.id = aml.currency_id
left join account_account aa on aa.id = aml.account_id
left join (select concat(partner_id,account_id,type_document_id,supplier_invoice_number) as identifica,date,date_due from account_invoice) facturas on facturas.identifica=T.identifica
where T.debe != T.haber
order by empresa, itd.code, nro_comprobante

						""")
		for i in self.env.cr.fetchall():
			dataL = {}
			opppp = self.env['res.currency'].search([('name','=','USD')])[0]

			if i[10] == 'USD':
				dataL = {
					'name':'Asiento de Apertura',
					'partner_id':i[2],
					'account_id':i[4],
					'nro_comprobante':i[6],
					'debit':( (i[11]*self.tipo_cambio_venta) if i[3] == 'A pagar' else (i[11]*self.tipo_cambio_compra)  ) if (i[11]) >0 else 0,
					'credit':( (-i[11]*self.tipo_cambio_venta) if i[3] == 'A pagar' else (-i[11]*self.tipo_cambio_compra)  ) if (i[11]) <0 else 0,
					'type_document_id':i[5],
					'move_id': t.id,
					'amount_currency':i[11],
					'date_maturity':i[12],
					'currency_id': opppp.id,
				} 
				sumdebe+= ( (i[11]*self.tipo_cambio_venta) if i[3] == 'A pagar' else (i[11]*self.tipo_cambio_compra)  ) if (i[11]) >0 else 0
				sumcredit+= ( (-i[11]*self.tipo_cambio_venta) if i[3] == 'A pagar' else (-i[11]*self.tipo_cambio_compra)  ) if (i[11]) <0 else 0
			else:
				dataL = {
					'name':'Asiento de Apertura',
					'partner_id':i[2],
					'account_id':i[4],
					'nro_comprobante':i[6],
					'debit':(i[7] - i[8]) if (i[7] - i[8]) >0 else 0,
					'credit':(i[8] - i[7]) if (i[8] - i[7]) >0 else 0,
					'type_document_id':i[5],
					'date_maturity':i[12],
					'move_id': t.id,
				}				
				sumdebe+=(i[7] - i[8]) if (i[7] - i[8]) >0 else 0
				sumcredit+=(i[8] - i[7]) if (i[8] - i[7]) >0 else 0

			self.env['account.move.line'].create(dataL)

		dataL = {					
			'name':'Asiento de Apertura',
			'account_id':self.cuenta_haber.id,
			'nro_comprobante':'',
			'debit':sumcredit,
			'credit':0,
			'move_id': t.id,
		}
		print dataL,'DataL'
		self.env['account.move.line'].create(dataL)

		dataL = {					
			'name':'Asiento de Apertura',
			'account_id':self.cuenta_debe.id,
			'nro_comprobante':'',
			'debit':0,
			'credit':sumdebe,
			'move_id': t.id,
		}
		print dataL,'DataL'
		self.env['account.move.line'].create(dataL)

		t.refresh()
		r_id = self.env['account.move.reconcile'].create({'type': 'auto', 'opening_reconciliation': True})

		for elem_f in t.line_id:
			self.env.cr.execute('update account_move_line set reconcile_id = %s where id = %s',(r_id.id, elem_f.id,))