# -*- coding: utf-8 -*-

from openerp import models, fields, api
import base64
from openerp.osv import osv

import re

class account_move_comprobante_partner(models.Model):
	_name='account.move.comprobante.partner'
	_auto = False

	name = fields.Char('Comprobante')
	partner_id = fields.Many2one('res.partner','Partner')

	def init(self,cr):
		cr.execute(""" 
			drop view if exists account_move_comprobante_partner;
			create or replace view account_move_comprobante_partner as (


select row_number() OVER() as id,* from
(



select distinct
aml.nro_comprobante as name, 
aa.type,
aml.partner_id

from account_move_line aml
inner join account_move am on am.id = aml.move_id
inner join account_account aa on aa.id = aml.account_id
where aa.type in ('payable','receivable')
and aml.nro_comprobante is not null and aml.nro_comprobante !=''
order by aml.nro_comprobante

						) AS T  )

			""")


	def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
		if not args:
			args = []
		if name:
			ids = self.search(cr, user, [('name','=',name)]+ args, limit=limit, context=context)
			if not ids:
				ids = self.search(cr, user, [('name','=',name)]+ args, limit=limit, context=context)
			if not ids:
				# Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
				# on a database with thousands of matching products, due to the huge merge+unique needed for the
				# OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
				# Performing a quick memory merge of ids in Python will give much better performance
				ids = set()
				ids.update(self.search(cr, user, args + [('name',operator,name)], limit=limit, context=context))
				if not limit or len(ids) < limit:
					# we may underrun the limit because of dupes in the results, that's fine
					ids.update(self.search(cr, user, args + [('name',operator,name)], limit=(limit and (limit-len(ids)) or False) , context=context))
					# vivek
					# Purpose  : To filter the product by using part_number
					ids.update(self.search(cr, user, args + [('name',operator,name)], limit=(limit and (limit-len(ids)) or False) , context=context))
					#End
				ids = list(ids)
			if not ids:
				ptrn = re.compile('(\[(.*?)\])')
				res = ptrn.search(name)
				if res:
					ids = self.search(cr, user, [('name','=', res.group(2))] + args, limit=limit, context=context)
		else:
			ids = self.search(cr, user, args, limit=limit, context=context)
		result = self.name_get(cr, user, ids, context=context)
		return result




class analisis_factura(models.Model):
	_name = 'analisis.factura'


	@api.one
	@api.depends('desembolso_lines')
	def saldo_deuda_calculate_dolar(self):
		ele = self
		rpta = 0
		for i in self.desembolso_lines:
			rpta += i.amount_currency

		ele.saldo_deuda_dolar = rpta

	@api.one
	@api.depends('desembolso_lines')
	def saldo_deuda_calculate_soles(self):
		ele = self
		rpta = 0
		for i in self.desembolso_lines:
			rpta += i.debit
			rpta -= i.credit

		ele.saldo_deuda_soles = rpta



	@api.one
	@api.depends('comprobante_auto')
	def desembolso_line_calculate(self):

		ele = self
		rpta = []		
		rpta2 = []
		for i in self.env['account.move.line'].search([('move_id.state','!=','draft'),('account_id.type','in',('payable','receivable')),('partner_id','=',self.personal.id),('nro_comprobante','=',self.comprobante_auto.name)]).sorted(key=lambda r: r.date):
			rpta2.append(i.id)
		ele.desembolso_lines = (rpta2[::-1])[::-1]

	@api.one
	def get_name_personalizado(self):
		if self.id:
			self.name = "Análisis Factura " + str(self.id)
		else:
			self.name = "Análisis Factura"

	saldo_deuda_soles = fields.Float('Saldo Soles',digits=(12,2), compute="saldo_deuda_calculate_soles")
	saldo_deuda_dolar = fields.Float('Saldo Dolar',digits=(12,2), compute="saldo_deuda_calculate_dolar")
	name = fields.Char('Nombre',compute="get_name_personalizado")
	personal = fields.Many2one('res.partner', string='Empresa')
	desembolso_lines = fields.Many2many('account.move.line','Lineas Desembolso',compute='desembolso_line_calculate', readonly="1")
	comprobante_auto = fields.Many2one('account.move.comprobante.partner','Número Comprobante')

	@api.onchange('personal')
	def onchange_personal(self):
		self.comprobante_auto = False

	@api.one
	def unlink(self):
		if len(self.desembolso_lines)>0:
			raise osv.except_osv('Alerta!', 'No puede eliminar este Desembolso porque existen Lineas referenciadas al mismo.')
		return super(desembolso_personal,self).unlink()

	@api.multi
	def conciliacion_button(self):
		ids_lines = []
		for i in self.desembolso_lines:
			ids_lines.append(i.id)
		return {
			'name':'Conciliación',
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'account.move.line.reconcile',
			'views': [(False, 'form')],
			'target': 'new',
			'context': {'active_ids':ids_lines},
		}


	@api.multi
	def desconciliacion_button(self):
		ids_lines = []
		for i in self.desembolso_lines:
			ids_lines.append(i.id)
		return {
			'name':'Conciliación',
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'account.unreconcile',
			'views': [(False, 'form')],
			'target': 'new',
			'context': {'active_ids':ids_lines},
		}