# -*- encoding: utf-8 -*-
from openerp import models, fields, api
from openerp.osv import osv

class stock_picking(models.Model):
	_inherit='stock.picking'

	motivo_guia = fields.Selection(
				(
					('1','Venta'),
					('2','Venta sujeta a confirmación del comprador'),
					('3','Compra'),
					('4','Consignación'),
					('5','Devolución'),
					('6','Traslado entre establecimientos de la misma empresa'),
					('7','Traslado de bienes para transformación'),
					('8','Recojo de bienes transformados'),
					('9','Traslado por emisor itinerante de comprobantes de pago'),
					('10','Traslado zona primaria'),
					('11','Importación'),
					('12','Exportación'),
					('13','Otros'),
					('14','Venta con entrega a terceros'),
					('15','Saldo inicial'),
				),'Motivo de traslado')
