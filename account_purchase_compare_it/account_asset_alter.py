# -*- coding: utf-8 -*-

from openerp import models, fields, api
import base64
from openerp.osv import osv
from openerp import netsvc


class stock_invoice_onshipping(models.TransientModel):
	_inherit = 'stock.invoice.onshipping'

	@api.one
	def create_invoice(self):
		t = super(stock_invoice_onshipping,self).create_invoice()
		oml = self.env.context['active_id']
		picking_obj = self.env['stock.picking'].search([('id','=',oml)])[0]
		picking_obj.invoice_id = t[0]
		invoice_obj = self.env['account.invoice'].search([('id','=',t[0])])[0]
		invoice_obj.po_id = picking_obj.po_id.id
		invoice_obj.sale_id = picking_obj.so_id.id
		return t

class stock_picking(models.Model):
	_inherit = 'stock.picking'

	invoice_id = fields.Many2one('account.invoice','Factura',readonly=False,copy=False)
	po_id = fields.Many2one('purchase.order','Pedido de Compra',readonly=True,copy=True)
	so_id = fields.Many2one('sale.order','Pedido de Venta',readonly=True,copy=True)
	
	@api.one
	def write(self,vals):
		if self.sale_id.id:
			vals['so_id']=self.sale_id.id
		return super(stock_picking,self).write(vals)

	@api.model
	def create(self,vals):
		t = super(stock_picking,self).create(vals)
		if t.sale_id.id:
			t.so_id = t.sale_id.id
		return t

	# REOPEN funcion
	@api.one
	def action_revert_done(self):
		t = super(stock_picking,self).action_revert_done()
		if self.po_id.id:
			if self.po_id.invoice_method == 'order':
				pass
			elif self.po_id.invoice_method == 'picking':
				if self.invoice_id.id:
					if self.invoice_id.state == 'draft':
						self.po_id.write({'invoice_ids': [(3, self.invoice_id.id)]})
						self.invoice_id.unlink()
					elif self.invoice_id.state == 'cancel':
						self.po_id.write({'invoice_ids': [(3, self.invoice_id.id)]})
						self.invoice_id.po_id = False
						self.invoice_id= False
					else:
						raise osv.except_osv('Alerta!','No se puede hacer Reopen con una factura abierta o pagada.') 
		if self.sale_id.id:
			if self.sale_id.order_policy == 'prepaid':
				pass
			elif self.sale_id.order_policy == 'picking':
				if self.invoice_id.id:
					if self.invoice_id.state == 'draft':
						self.so_id.write({'invoice_ids': [(3, self.invoice_id.id)]})
						self.invoice_id.unlink()
					elif self.invoice_id.state == 'cancel':
						self.so_id.write({'invoice_ids': [(3, self.invoice_id.id)]})
						self.invoice_id.sale_id = False
						self.invoice_id= False
					else:
						raise osv.except_osv('Alerta!','No se puede hacer Reopen con una factura abierta o pagada.')
		return t



class account_invoice(models.Model):
	_inherit = 'account.invoice'

	po_id = fields.Many2one('purchase.order','Pedido de Compra',readonly=True)
	sale_id = fields.Many2one('sale.order','Pedido de Venta',readonly=True)


	@api.one
	def unlink(self):
		if self.po_id.id:
			for i in self.po_id.picking_ids:
				if i.invoice_id.id == self.id:
					for m in i.move_lines:
						if self.po_id.invoice_method == 'picking':
							m.invoice_state = '2binvoiced'
		if self.sale_id.id:
			for i in self.sale_id.picking_ids:
				if i.invoice_id.id == self.id:
					for m in i.move_lines:
						if self.sale_id.order_policy == 'picking':
							m.invoice_state = '2binvoiced'
			#for i in self.sale_id.picking_ids:
			#	if i.invoice_id.id == self.id:
			#		for m in si.move_lines:
			#			if self.sale_id.invoice_method == 'picking':
			#				m.invoice_state = '2binvoiced'
		return super(account_invoice,self).unlink()

class sale_order(models.Model):
	_inherit = 'sale.order'

	@api.one
	def action_button_confirm(self):
		t = super(sale_order,self).action_button_confirm()
		jo = self.env['account.sale.compare'].create({'partner_id':self.partner_id.id,'sale_id':self.id})
		jo.actualizar()
		return t

	def action_invoice_create(self, cr, uid, ids, grouped=False, states=['confirmed', 'done', 'exception'], date_invoice = False, context=None):
		res = super(sale_order,self).action_invoice_create(cr, uid, ids, grouped=grouped, states=states, date_invoice = date_invoice, context=context)
		for order in self.browse(cr, uid, ids, context=context):
			if order.order_policy == 'manual':
				for picking in order.picking_ids:
					self.pool.get('stock.picking').write(cr, uid, picking.id, {'invoice_id': res}, context=context)

		self.pool.get('account.invoice').write(cr,uid,res,{'sale_id':ids[0]},context=context)
		return res


class purchase_order(models.Model):
	_inherit = 'purchase.order'

	@api.multi
	def get_temporal(self):
		print "temporal get"
		omg = self.temporal2
		if self.temporal2 != False:
			self.temporal2 = False
		return omg
		

	temporal = fields.Char('Temporal')
	temporal2 = fields.Char('Temporal')
	invoice_method = fields.Selection([('order','Based on generated draft invoice'),('picking','Based on incoming shipments')], 'Invoicing Control', required=True,    readonly=True, states={'draft':[('readonly',False)], 'sent':[('readonly',False)]},
			help="Based on Purchase Order lines: place individual lines in 'Invoice Control / On Purchase Order lines' from where you can selectively create an invoice.\n" \
				"Based on generated invoice: create a draft invoice you can validate later.\n" \
				"Based on incoming shipments: let you create an invoice when receipts are validated."
	   )

	@api.one
	def wkf_confirm_order(self):
		t = super(purchase_order,self).wkf_confirm_order()
		jo = self.env['account.purchase.compare'].create({'partner_id':self.partner_id.id,'purchase_id':self.id})
		jo.actualizar()
		return t
		 
	@api.one
	def cancelar_it(self):
		if len(self.picking_ids) != 0:
			raise osv.except_osv('Alerta!','No se puede cancelar un pedido con Albaranes o Facturas no Canceladas enlazadas.')
		for i in self.invoice_ids:
			if i.state == 'cancel':
				self.write({'invoice_ids': [(3, i.id)]})
				i.write({'origin':False})
			else:
				raise osv.except_osv('Alerta!','No se puede cancelar un pedido con Albaranes o Facturas no Canceladas enlazadas.')

		wf_service = netsvc.LocalService("workflow")
		wf_service.trg_validate(self.env.uid, self._name, self.id, 'view_picking', self.env.cr)
		self.action_cancel()
		self.action_cancel_draft()

	def action_picking_create(self, cr, uid, ids, context=None):
		t = super(purchase_order,self).action_picking_create(cr, uid, ids, context)
		for order in self.browse(cr, uid, ids):
			spai = self.pool.get('stock.picking').search(cr,uid,[('id','=',t)])
			sp = self.pool.get('stock.picking').browse(cr,uid,spai)
			if len(sp)>0:
				sp = sp[0]
				sp.po_id = order.id 
				if order.invoice_method == 'order':
					if len(order.invoice_ids) == 1:
						sp.invoice_id = order.invoice_ids[0].id
		return t


	def action_invoice_create(self, cr, uid, ids, context=None):
		t = super(purchase_order,self).action_invoice_create(cr, uid, ids, context)
		for order in self.browse(cr, uid, ids):
			spai = self.pool.get('account.invoice').search(cr,uid,[('id','=',t)])
			sp = self.pool.get('account.invoice').browse(cr,uid,spai)
			if len(sp)>0:
				sp = sp[0]
				sp.po_id = order.id 
				if order.invoice_method == 'order':
					for i in order.picking_ids:
						i.invoice_id = sp.id
		return t

	@api.multi
	def my_almacen(selfs):
		for self in selfs:

			jo = self.env['account.purchase.compare'].create({'partner_id':self.partner_id.id,'purchase_id':self.id})
			jo.actualizar()


			t= self.action_picking_create()

			sp = self.env['stock.picking'].search([('id','=',t)])[0]

			if self.invoice_method == 'order' and len(self.invoice_ids)==0:			
				pass
			elif self.invoice_method == 'order' and len(self.invoice_ids)==1:
				sp.invoice_id = self.invoice_ids[0].id
			flag = True
			for i in sp.move_lines:
				k_e = self.env['account.pc.alb.line'].search([('padre','=',jo.id),('producto','=',i.product_id.id)])[0]
				i.product_uom_qty = k_e.dif_cantidad
				if k_e.dif_cantidad != 0:
					flag = False

			if flag:
				sp.unlink()
				jo.unlink()
				self.temporal2 = '2\nSe encuentran completo los Albaranes\n'
			
			else:

				self.picking_done()

				jo.unlink()

				self.state = 'approved'
				self.temporal2 = '1\nSe creo exitosamente el Albaran\n'
	
	@api.multi
	def my_factura(selfs):
		for self in selfs:
			if self.invoice_method == 'order' and len(self.invoice_ids)==0:
				jo = self.env['account.purchase.compare'].create({'partner_id':self.partner_id.id,'purchase_id':self.id})
				jo.actualizar()

				t = self.action_invoice_create()
				ai = self.env['account.invoice'].search([('id','=',t)])[0]

				for op in self.picking_ids:
					op.invoice_id = ai.id

				flag = True
				for i in ai.invoice_line:
					k_e = self.env['account.pc.fact.line'].search([('padre','=',jo.id),('producto','=',i.product_id.id)])[0]
					i.quantity = k_e.dif_cantidad
					if k_e.dif_cantidad == 0:
						i.unlink()
					if k_e.dif_cantidad != 0:
						flag = False
				if flag:
					ai.unlink()
					jo.unlink()
					self.temporal2 = '2\nSe encuentran completo las Facturas\n'
				else:
					self.invoice_done()

					jo.unlink()
					self.state = 'approved'
					self.temporal2 = '1\nSe creo exitosamente la Factura\n'
			elif self.invoice_method == 'order' and len(self.invoice_ids)>0:
				self.temporal2 = "2\nPara el metodo de facturación seleccionado solo se puede generar una factura.\n"
			else:
				self.temporal2 = '3\nEl pedido esta configurado para crear facturas basado en recepciones.\n'



class account_pc_fact_line(models.Model):
	_name = 'account.pc.fact.line'

	producto = fields.Many2one('product.product','Producto')
	cantidad = fields.Float('Cantidad',digits=(12,2))
	valor = fields.Float('Valor',digits=(12,2))
	factura_can = fields.Float('Cantidad Facturada',digits=(12,2))
	factura_val = fields.Float('Valor Facturado',digits=(12,2))
	dif_cantidad = fields.Float('Diferencia',digits=(12,2))
	dif_valor = fields.Float('Diferencia',digits=(12,2))

	padre = fields.Many2one('account.purchase.compare','Padre')

	madre = fields.Many2one('account.sale.compare','Madre')

class account_pc_alb_line(models.Model):
	_name = 'account.pc.alb.line'

	producto = fields.Many2one('product.product','Producto')
	cantidad = fields.Float('Cantidad',digits=(12,2))
	factura_can = fields.Float('Cantidad Albaran',digits=(12,2))
	dif_cantidad = fields.Float('Diferencia',digits=(12,2))
	
	padre = fields.Many2one('account.purchase.compare','Padre')

	madre = fields.Many2one('account.sale.compare','Madre')

class account_purchase_compare(models.Model):
	_name = 'account.purchase.compare'

	borradores = fields.Boolean('Considerar borradores')
	partner_id = fields.Many2one('res.partner','Proveedor')
	purchase_id = fields.Many2one('purchase.order','Pedido de Compra')

	fac_line = fields.One2many('account.pc.fact.line','padre','Factura')
	alb_line = fields.One2many('account.pc.alb.line','padre','Albaran')

	_rec_name = 'purchase_id'

	@api.one
	def actualizar(self):
		for i in self.fac_line:
			i.unlink()

		for i in self.alb_line:
			i.unlink()

		for k in self.purchase_id.order_line:
			obj = self.env['account.pc.fact.line'].search([('padre','=',self.id),('producto','=',k.product_id.id)])
			if len(obj)>0:
				obj.cantidad += k.product_qty
				obj.valor += k.product_qty * k.price_unit
			else:
				data={
					'producto':k.product_id.id,
					'cantidad':k.product_qty,
					'valor':k.product_qty * k.price_unit,
					'padre':self.id,
				} 
				self.env['account.pc.fact.line'].create(data)
		for l in self.purchase_id.invoice_ids:
			for k in l.invoice_line:
				obj = self.env['account.pc.fact.line'].search([('padre','=',self.id),('producto','=',k.product_id.id)])
				if len(obj)>0 and l.state!= 'cancel':
					if self.borradores:
						obj.factura_can += k.quantity
						obj.factura_val += k.quantity * k.price_unit
					else:
						if l.state != 'draft':							
							obj.factura_can += k.quantity
							obj.factura_val += k.quantity * k.price_unit
			
		self.refresh()	
		for i in self.fac_line:
			i.dif_cantidad = i.cantidad - i.factura_can
			i.dif_valor = i.valor - i.factura_val


		for k in self.purchase_id.order_line:
			#aqui comienza
			obj = self.env['account.pc.alb.line'].search([('padre','=',self.id),('producto','=',k.product_id.id)])
			if len(obj)>0:
				obj.cantidad += k.product_qty
			else:
				data={
					'producto':k.product_id.id,
					'cantidad':k.product_qty,
					'padre':self.id,
				} 
				self.env['account.pc.alb.line'].create(data)

		for l in self.purchase_id.picking_ids:
			for k in l.move_lines:
				obj = self.env['account.pc.alb.line'].search([('padre','=',self.id),('producto','=',k.product_id.id)])
				if len(obj)>0 and l.state != 'cancel':
					if self.borradores:
						obj.factura_can += k.product_uom_qty
					else:
						if l.state != 'draft':
							obj.factura_can += k.product_uom_qty
			
		self.refresh()
		for i in self.alb_line:
			i.dif_cantidad = i.cantidad - i.factura_can



class account_sale_compare(models.Model):
	_name = 'account.sale.compare'

	borradores = fields.Boolean('Considerar borradores')
	partner_id = fields.Many2one('res.partner','Proveedor')
	sale_id = fields.Many2one('sale.order','Pedido de Venta')

	fac_line = fields.One2many('account.pc.fact.line','madre','Factura')
	alb_line = fields.One2many('account.pc.alb.line','madre','Albaran')

	_rec_name = 'sale_id'

	@api.one
	def actualizar(self):
		for i in self.fac_line:
			i.unlink()

		for i in self.alb_line:
			i.unlink()

		for k in self.sale_id.order_line:
			obj = self.env['account.pc.fact.line'].search([('madre','=',self.id),('producto','=',k.product_id.id)])
			if len(obj)>0:
				obj.cantidad += k.product_uom_qty
				obj.valor += k.product_uom_qty * k.price_unit
			else:
				data={
					'producto':k.product_id.id,
					'cantidad':k.product_uom_qty,
					'valor':k.product_uom_qty * k.price_unit,
					'madre':self.id,
				} 
				self.env['account.pc.fact.line'].create(data)
		for l in self.sale_id.invoice_ids:
			for k in l.invoice_line:
				obj = self.env['account.pc.fact.line'].search([('madre','=',self.id),('producto','=',k.product_id.id)])
				if len(obj)>0 and l.state != 'cancel':
					if self.borradores:
						obj.factura_can += k.quantity
						obj.factura_val += k.quantity * k.price_unit
					else:
						if l.state != 'draft':
							obj.factura_can += k.quantity
							obj.factura_val += k.quantity * k.price_unit
			
		self.refresh()	
		for i in self.fac_line:
			i.dif_cantidad = i.cantidad - i.factura_can
			i.dif_valor = i.valor - i.factura_val


		for k in self.sale_id.order_line:
			#aqui comienza
			obj = self.env['account.pc.alb.line'].search([('madre','=',self.id),('producto','=',k.product_id.id)])
			if len(obj)>0:
				obj.cantidad += k.product_uom_qty
			else:
				data={
					'producto':k.product_id.id,
					'cantidad':k.product_uom_qty,
					'madre':self.id,
				} 
				self.env['account.pc.alb.line'].create(data)

		for l in self.sale_id.picking_ids:
			for k in l.move_lines:
				obj = self.env['account.pc.alb.line'].search([('madre','=',self.id),('producto','=',k.product_id.id)])
				if len(obj)>0 and l.state != 'cancel':
					if self.borradores:
						obj.factura_can += k.product_uom_qty
					else:
						if l.state != 'draft':
							obj.factura_can += k.product_uom_qty
			
		self.refresh()
		for i in self.alb_line:
			i.dif_cantidad = i.cantidad - i.factura_can





