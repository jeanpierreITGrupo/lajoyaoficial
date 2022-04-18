# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp import models, fields, api
import os.path
import base64

class sale_cost_journal(models.TransientModel):
	_name = "sale.cost.journal"

	out_account = fields.Many2one('account.account', "Cuenta Salida")
	valued_account = fields.Many2one('account.account', "Cuenta Valoración")
	product_id = fields.Many2one('product.product', "Producto")
	valued_rest = fields.Float("Saldo Valorado")
	period_id = fields.Many2one('account.period', "Periodo")

	@api.multi
	def make_sale_journal(self):
		locations = self.env['stock.location'].search([('usage','=','internal')])
		products = self.env['product.product'].search([])
		period_id = self.env['sale.cost.journal'].search([])[0].period_id
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		lst_locations = []
		lst_products = []
		for location in locations:
			lst_locations.append(location.id)
		for product in products:
			lst_products.append(product.id)
		productos='{'
		almacenes='{'
		for producto in lst_products:
			productos=productos+str(producto)+','
		productos=productos[:-1]+'}'
		for location in lst_locations:
			almacenes=almacenes+str(location)+','
		almacenes=almacenes[:-1]+'}'

		#Obteniendo líneas de débito
		cadf = "select out_account, sum(saldov) as saldo from get_moves_cost("+period_id.date_start.replace('-','') + "," + period_id.date_stop.replace('-','') + ",'" + productos + "'::INT[], '" + almacenes + "'::INT[], 'customer') group by out_account"
		self.env.cr.execute(cadf)
		debit_lines = self.env.cr.dictfetchall()


		#Obteniendo líneas de crédito
		cadf = "select valued_account, sum(saldov) as saldo from get_moves_cost("+period_id.date_start.replace('-','') + "," + period_id.date_stop.replace('-','') + ",'" + productos + "'::INT[], '" + almacenes + "'::INT[], 'customer') group by valued_account"
		self.env.cr.execute(cadf)
		credit_lines = self.env.cr.dictfetchall()

		#CREANDO ASIENTO
		move_obj = self.env['account.move']
		move_line_obj = self.env['account.move.line']
		journal_id = self.env['main.parameter'].search([]).diario_destino
		name = period_id.name.replace('/','-')
		vals = {
			'journal_id'	: journal_id.id,
			'period_id'		: period_id.id,
			'ref'			: 'CV-' + name,
			'date'			: period_id.date_stop,
		}
		move_id = move_obj.create(vals)

		#Creando lineas de credit
		for line in credit_lines:
			vals = {
				'move_id'			: move_id.id,
				'name'				: 'COSTO DE VENTAS ' + name,
				'nro_comprobante'	: 'CV-' + name,
				'account_id'		: int(line['valued_account'].split(',')[1]) if line['valued_account'] else None,
				'debit'				: 0.0,
				'credit'			: line['saldo'],	
			}
			move_line_obj.create(vals)

		#Creando lineas de debit
		for line in debit_lines:
			vals = {
				'move_id'			: move_id.id,
				'name'				: 'COSTO DE VENTAS ' + name,
				'nro_comprobante'	: 'CV-' + name,
				'account_id'		: int(line['out_account'].split(',')[1]) if line['out_account'] else None,
				'debit'				: line['saldo'],	
				'credit'			: 0.0,
			}
			move_line_obj.create(vals)

		return {
			"type"		: "ir.actions.act_window",
			"res_model"	: "account.move",
			"view_type"	: "form",
			"view_mode"	: "form",
			"res_id"	: move_id.id,
			"target"	: "current",
		}
