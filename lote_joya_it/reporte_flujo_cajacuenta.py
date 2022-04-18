# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.osv import osv
import decimal
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import magenta, red , black , blue, gray, Color, white, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Table
from reportlab.lib.units import  cm,mm
from reportlab.lib.utils import simpleSplit
from cgi import escape
import base64


class grilla_lote_terminado(models.Model):
	_name = 'grilla.lote.terminado'

	rubro 		= fields.Char('Rubro')
	monto 		= fields.Float('Monto')
	lote_id 	= fields.Many2one('lote.terminado.tabla','Lote')


class lote_terminado_tabla_linea(models.Model):
	_name = 'lote.terminado.tabla.linea'

	fecha = fields.Date('Fecha')
	escoria = fields.Char('Nro. Escoria')
	amalgama = fields.Char('Nro. Amalgama')
	campana = fields.Char('Nro. Campaña')
	barra = fields.Char('Nro. Barra')
	peso_barra = fields.Float('Peso Barra',digits=(12,3))
	au = fields.Float('% Au',digits=(12,3))
	ag = fields.Float('% Ag',digits=(12,3))
	au_fino = fields.Float('Au Fino Gramos',digits=(12,3))
	ag_fino = fields.Float('Ag Fino Gramos',digits=(12,3))
	costo_und = fields.Float('Costo Und. Gr.',digits=(12,3))
	costo_total = fields.Float('Costo Total',digits=(12,3))

	padre = fields.Many2one('lote.terminado.table','Padre')

	

class lote_terminado_tabla(models.Model):
	_name = 'lote.terminado.tabla'

	lineas = fields.One2many('lote.terminado.tabla.linea','padre','Detalle')
	name = fields.Char('Lote Terminado')


	fecha = fields.Date('Fecha')
	escoria = fields.Char('Nro. Escoria')
	amalgama = fields.Char('Nro. Amalgama')
	campana = fields.Char('Nro. Campaña')
	barra = fields.Char('Nro. Barra')
	peso_barra = fields.Float('Peso Barra',digits=(12,3))
	au = fields.Float('% Au',digits=(12,3))
	ag = fields.Float('% Ag',digits=(12,3))
	au_fino = fields.Float('Au Fino Gramos',digits=(12,3))
	ag_fino = fields.Float('Ag Fino Gramos',digits=(12,3))
	costo_und = fields.Float('Costo Und. Gr.',digits=(12,3))
	costo_total = fields.Float('Costo Total',digits=(12,3))
	period_id = fields.Many2one('account.period','Periodo')


	costo_oro 				= fields.Float('Costo Oro',digits=(12,2)) 
	costo_plata 			= fields.Float('Costo Plata',digits=(12,2))
	costo_chancado 			= fields.Float('Costo Chancado',digits=(12,2))
	costo_zona				= fields.Float('Costo Zona',digits=(12,2))
	costo_expediente 		= fields.Float('Costo Expediente',digits=(12,2))
	gastos_generales 		= fields.Float('Gastos Generales - Chancado - Recepcion - Comercial',digits=(12,2))
	total_mineral 			= fields.Float('Total Costo Mineral',digits=(12,2))

	grilla_id 				= fields.One2many('grilla.lote.terminado','lote_id','Linas')


	factura = fields.Many2one('account.invoice','Factura')
	albaran = fields.Many2one('stock.picking','Albaran')
	valor_venta = fields.Float('Valor Venta')
	diferencia_v_venta = fields.Float('Dif. Valor Venta')

	@api.one
	def valor_ventac(self):
		xio = 0
		self.env.cr.execute(""" 
		 select abs(debit - credit)
		 from account_move_line  aml
		 where  aml.move_id = """ +str(self.factura.move_id.id if self.factura.id and self.factura.move_id.id else 0)+ """
		 and aml.nro_lote_terminado = """ +str(self.id)+ """
		  """)
		for aoe in self.env.cr.fetchall():
			xio += aoe[0]

		self.valor_venta = xio
		self.diferencia_v_venta = self.costo_total - xio

	@api.one
	def actualizar(self):
		rubros = []
		self.env.cr.execute(""" select name from rubro_costo_it """)
		for elem in self.env.cr.fetchall():
			rubros.append(elem[0])
		
		rubros.append('Total Costo Produccion')
		rubros.append('Total Costo')

		for i in self.grilla_id:
			if i.rubro not in rubros:
				i.unlink()


		for i in rubros:
			flag = True
			for l in self.grilla_id:
				if i == l.rubro:
					flag = False
			if flag:
				data = {
					'rubro':i,
					'monto':0,
					'lote_id':self.id,
				}
				self.env['grilla.lote.terminado'].create(data)
	@api.model
	def create(self,vals):
		t = super(lote_terminado_tabla,self).create(vals)
		sequence_obj = self.env['ir.sequence']
		sequence_id = sequence_obj.search([('name','=','Lote Terminado Tabla')])
		if sequence_id and sequence_id.id:
			t.name = sequence_id.next_by_id(sequence_id.id)
		else:
			dic_new_seq = {
				'name': 'Lote Terminado Tabla',
				'padding': 6,
				'number_next_actual': 1,
				'number_increment': 1,
				'implementation': 'no_gap',
				'prefix': 'LT-',
			}
			new_sequence= self.env['ir.sequence'].create(dic_new_seq)
			t.name = new_sequence.next_by_id(new_sequence.id)
		return t


class sale_order_line(models.Model):
	_inherit = 'sale.order.line'

	lote_terminado_tabla_id = fields.Many2one('lote.terminado.tabla','Lote Terminado')


	@api.model
	def _prepare_order_line_invoice_line(self, line, account_id=False):
		print "ejecutandose"
		t = super(sale_order_line,self)._prepare_order_line_invoice_line(line,account_id)
		t['nro_lote_terminado']=line.lote_terminado_tabla_id.id
		return t

class stock_move(models.Model):
	_inherit = 'stock.move'

	lote_terminado_tabla_id = fields.Many2one('lote.terminado.tabla','Lote Terminado')

class procurement_order(models.Model):
	_inherit = 'procurement.order'

	lote_terminado_tabla_id = fields.Many2one('lote.terminado.tabla','Lote Terminado')

	def _run_move_create(self, cr, uid, procurement, context=None):
		t = super(procurement_order,self)._run_move_create(cr,uid,procurement,context)
		t['lote_terminado_tabla_id'] = procurement.lote_terminado_tabla_id.id
		return t
   

class sale_order(models.Model):
 	_inherit = 'sale.order'

	def _prepare_order_line_procurement(self, cr, uid, order, line, group_id=False, context=None):
		t = super(sale_order,self)._prepare_order_line_procurement(cr,uid,order,line,group_id,context)
		t['lote_terminado_tabla_id'] = line.lote_terminado_tabla_id.id
		return t




class account_invoice(models.Model):
	_inherit = 'account.invoice'
 
 	@api.model
	def line_get_convert(self, line, part, date):
		t = super(account_invoice,self).line_get_convert(line,part,date)
		t['nro_lote_terminado']= line.get('nro_lote_terminado',False)
		return t

class account_invoice_line(models.Model):
	_inherit = 'account.invoice.line'

	nro_lote_terminado = fields.Many2one('lote.terminado.tabla','Nro de Lote Terminado')



	@api.model
	def move_line_get_item(self, line):
		t = super(account_invoice_line,self).move_line_get_item(line)
		t['nro_lote_terminado'] = line.nro_lote_terminado.id
		return t


class account_move_line(models.Model):
	_inherit = 'account.move.line'

	nro_lote_terminado = fields.Many2one('lote.terminado.tabla','Nro de Lote Terminado')