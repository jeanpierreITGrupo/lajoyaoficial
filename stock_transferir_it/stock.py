# -*- encoding: utf-8 -*-
from openerp.osv import osv
from openerp     import models, fields, api
import base64
import codecs

import datetime
import decimal

class stock_picking(models.Model):
	_inherit = 'stock.picking'

	@api.one
	def transferir_picking(self):
		from_internal = True
		for i in self.move_lines:
			if i.location_id.usage != 'internal':
				from_internal = False
				break
		
		if from_internal:
			disp_wzd = self.get_disponibilidad_kfisico()
			dsk = self.env['detalle.simple.kfisicot'].search([('id','=',disp_wzd['res_id'])])
			if len(dsk):
				dsk = dsk[0]
				
				#CANTIDAD TOTAL A TRANSFERIR POR CADA PRODUCTO
				prod_dict = {}
				for i in self.move_lines:
					if i.product_id.id not in prod_dict:
						prod_dict[i.product_id.id] = i.product_uom_qty
					else:
						prod_dict[i.product_id.id] += i.product_uom_qty

				#VERIFICA LA DISPONIBILIDAD DE TODOS LOS PRODUCTOS
				error_msg   = ""
				for i in dsk.lineas:
					if i.saldo < prod_dict[i.producto.id]:
						error_msg += i.producto.name + " (" + str(prod_dict[i.producto.id]) + ") - " + str(i.saldo) + "\n"

				#SI NO HAY STOCK LANZA ERROR, CASO CONTRARIO TRANSFIERE
				# se ha pedido expresament y dos veces que se permita mover cantidades aun que no exista disponibilidad
				# repito que esto anula todo lo pensado para la disponibilidad de la Joya es 13-04-2018 las lineas siguientes serán comentadas
				# a pedido expreso de Lily y Edward, sigo pensando que este no es el camino pero a pesar que he intentado argumentar 
				# han seguido en la idea de hacerlo, lo hago.

				# if len(error_msg):
					# raise osv.except_osv('Alerta!', "Los siguientes productos no cuentan con disponibilidad:\n Producto (Cantidad) - Disponible\n"+error_msg)
				# else:
					# for i in self.move_lines:
						# i.state = 'done'
					# self.state = 'done'
				for i in self.move_lines:
					i.state = 'done'
				self.state = 'done'
		else:
			for i in self.move_lines:
				i.state = 'done'
			self.state = 'done'