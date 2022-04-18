# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api, exceptions , _

from openerp.osv import osv
from openerp import exceptions
#Orden de Compra
class purchase_order(models.Model):
	_inherit = 'purchase.order'

	def _prepare_order_line_move(self, cr, uid, order, order_line, picking_id, group_id, context=None):
		res = super(purchase_order,self)._prepare_order_line_move(cr, uid, order, order_line, picking_id, group_id, context)
		res[0]['gold_expected'] = order_line.gold_expected
		res[0]['lot_num'] = order_line.lot_num.id
		return res



class purchase_order_line(models.Model):
	_inherit = 'purchase.order.line'
	lot_num = fields.Many2one("purchase.liquidation","Lote")
	gold_expected = fields.Float("Expectativa de oro", digits=(10,3))


	@api.one
	@api.constrains('lot_num')
	def constrains_lot_num(self):
		if self.lot_num.id:
			filtro = []
			filtro.append( ('id','!=',self.id) )			
			filtro.append( ('lot_num','=',self.lot_num.id) )

			m = self.env['purchase.order.line'].search( filtro )
			if len(m) > 0:
				raise exceptions.Warning(_("Número de Lote Duplicado de ("+m[0].order_id.name+")."))



	def onchange_lot_num_antigua(self,cr,uid,ids,lot_num,context):
		ttemp = {'value':{}}
		flag = True

		if lot_num:
			lot_num = self.pool.get('purchase.liquidation').browse(cr,uid,lot_num)
			opt = None
			for i in lot_num.lines:
				if i.line_type == 'Negociado':							
					flag = False
					pro_tmp = None
					if lot_num.material.id:
						ttemp['value']['product_id'] = lot_num.material.id
						pro_tmp = lot_num.material

					if pro_tmp == None:
						raise exceptions.Warning(_("El lote no tiene un material asignado."))

					ttemp['value']['product_uom'] = pro_tmp.uom_id.id
					ttemp['value']['product_qty'] = i.tms
					ttemp['value']['price_unit'] =i.cost
					ttemp['value']['gold_expected'] = i.ley_oz * 34.285

		if flag:
			ttemp['value']['product_id'] = False
			ttemp['value']['product_uom'] = False
			ttemp['value']['product_qty'] = 0
			ttemp['value']['price_unit'] =0
			ttemp['value']['gold_expected'] = 0			
		return ttemp

	@api.returns
	def check_lotes(self):
		return self
			
	def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,partner_id, date_order=False, fiscal_position_id=False, date_planned=False,name=False, price_unit=False, state='draft', context=None):
		ttemp = super(purchase_order_line,self).onchange_product_id(cr, uid, ids, pricelist_id, product_id, qty, uom_id,partner_id, date_order, fiscal_position_id, date_planned,name, price_unit, state, context)
		print context,'contextito'
		if 'data_lote' in context:
			if context['data_lote']:
				data_l = self.pool.get('purchase.liquidation').browse(cr,uid,context['data_lote'])
				for i in data_l.lines:
					if i.line_type == 'Negociado':				
						pro_tmp = None
						if data_l.material.id:
							ttemp['value']['product_id'] = data_l.material.id
							pro_tmp = data_l.material


						ttemp['value']['product_uom'] = pro_tmp.uom_id.id
						ttemp['value']['product_qty'] = i.tms
						ttemp['value']['price_unit'] =i.cost
						ttemp['value']['gold_expected'] = i.ley_oz * 34.285
		return ttemp


#Movimiento de Almacén
class stock_move(models.Model):
	_inherit = 'stock.move'

	lot_num = fields.Many2one("purchase.liquidation","Lote")
	gold_expected = fields.Float("Expectativa de oro", digits=(10,3))
	ponderation = fields.Float("Ponderación", digits=(10,3))
	p_et2 = fields.Float("P_ET2", digits=(10,6))



# Product Template
class product_template(models.Model):
	_inherit = 'product.template'

	cost_method = fields.Selection(selection=[('standard', 'Standard Price'), ('average', 'Average Price'), ('real', 'Real Price'),('specific','Identificación Específica')])