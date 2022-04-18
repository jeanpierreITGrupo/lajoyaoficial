# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api
from openerp.osv import osv

class centro_costo_joya(models.Model):
	_name = 'centro.costo.joya'

	name = fields.Char('Nombre',required=True)

class motivo_reparables(models.Model):
	_name = 'motivo.reparables'

	name = fields.Char('Motivo Reparables')
	code = fields.Char('Codigo')

class purchase_order(models.Model):
	_inherit = 'purchase.order'

	centro_costo_id = fields.Many2one('centro.costo.joya','Centro de Costo')

	def _prepare_inv_line(self, cr, uid, account_id, order_line, context=None):
		t = super(purchase_order,self)._prepare_inv_line(cr, uid, account_id, order_line, context)
		if order_line.lot_num.id:
			t['nro_lote']= order_line.lot_num.id
		return t

class account_invoice(models.Model):
	_inherit = 'account.invoice'

	motivo_reparables_id = fields.Many2one('motivo.reparables','Motivo Reparables')
 
 	@api.model
	def line_get_convert(self, line, part, date):
		t = super(account_invoice,self).line_get_convert(line,part,date)
		t['nro_lote']= line.get('nro_lote',False)
		return t

class account_invoice_line(models.Model):
	_inherit = 'account.invoice.line'

	nro_lote = fields.Many2one('purchase.liquidation','Nro de Lote',ondelete="restrict")



	@api.model
	def move_line_get_item(self, line):
		t = super(account_invoice_line,self).move_line_get_item(line)
		t['nro_lote'] = line.nro_lote.id
		return t


class account_move_line(models.Model):
	_inherit = 'account.move.line'

	nro_lote = fields.Many2one('purchase.liquidation','Nro de Lote')