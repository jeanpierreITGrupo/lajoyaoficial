# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.osv import osv

class detalle_simple_fisico_total_d_minimo_wizard(models.TransientModel):
	_name = 'detalle.simple.fisico.total.d.minimo.wizard'

	fecha = fields.Date('Fecha',required=True)

	_defaults={
		'fecha': lambda self,cr,uid,c: fields.Date.today(),
	}


	@api.multi
	def do_rebuild(self):
		self.env.cr.execute(""" 
			drop view if exists detalle_simple_fisico_total_d_minimo;
			create view detalle_simple_fisico_total_d_minimo as (

select row_number() OVER () AS id, u as almacen,p as producto ,s as saldo, product_min_qty as p_min from (
	select sl.id as u ,pp.id as p ,saldo as s, swo.product_min_qty from (
		select product_id,ubicacion, sum(saldo) as saldo from (
			select product_id,location_id as ubicacion, -product_qty as saldo from vst_stock_move_final_joya where date::date >= '"""+str(self.fecha.split('-')[0])+"""-01-01'::date and date::date <= '""" +str(self.fecha)+ """'::date
			union all
			select product_id,location_dest_id as ubicacion, product_qty as saldo from vst_stock_move_final_joya where date::date >= '"""+str(self.fecha.split('-')[0])+"""-01-01'::date and date::date <= '""" +str(self.fecha)+ """'::date
		) as T group by product_id,ubicacion )as X
	inner join stock_location sl on sl.id = X.ubicacion
	inner join product_product pp on pp.id = X.product_id
	inner join stock_warehouse_orderpoint swo on swo.product_id = pp.id
	where sl.usage = 'internal' and swo.product_min_qty > saldo
) as MN
order by u,p,s 

			); 
			""")

		view_id = self.env.ref('kardex_product_saldominimofisico_it.view_kardex_fisico_d_minimo',False)
		return {
			'type'     : 'ir.actions.act_window',
			'res_model': 'detalle.simple.fisico.total.d.minimo',
			# 'res_id'   : self.id,
			'view_id'  : view_id.id,
			'view_type': 'form',
			'view_mode': 'tree',
			'views'    : [(view_id.id, 'tree')],
			#'target'   : 'new',
			#'flags'    : {'form': {'action_buttons': True}},
			#'context'  : {},
		}

class detalle_simple_fisico_total_d(models.Model):
	_name = 'detalle.simple.fisico.total.d.minimo'

	producto = fields.Many2one('product.product','Producto')
	almacen = fields.Many2one('stock.location','Almacen')
	saldo = fields.Float('Disponibilidad',digits=(15,3))
	p_min = fields.Float('Cantidad Minima',digits=(12,2))

	_order = 'producto,almacen'
	_auto = False
