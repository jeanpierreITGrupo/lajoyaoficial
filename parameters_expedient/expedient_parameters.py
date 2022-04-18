# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api

class production_parameter(models.Model):
	_name = "production.parameter"

	name                 = fields.Char('Nombre',size=50, default='Parametros Generales')
	journal_id           = fields.Many2one('account.journal',"Diario Asientos de Costos")
	#account_parent_id   = fields.Many2one('account.analytic.account',"Padre Analítica Gastos Acopio")
	product_ids          = fields.One2many('expedient.products', 'main_parameter', "Productos")
	ruma_product         = fields.Many2one('product.product', "Producto Ruma")
	virtual_location_id  = fields.Many2one('stock.location', "Ubicación de Producción")
	
	top_origen_chancado  = fields.Many2one('stock.picking.type', "Tipo Operación Origen Chancado")
	top_destino_chancado = fields.Many2one('stock.picking.type', "Tipo Operación Destino Chancado")
	
	top_origen_ruma      = fields.Many2one('stock.picking.type', "Tipo Operación Origen Ruma")
	top_destino_ruma     = fields.Many2one('stock.picking.type', "Tipo Operación Destino Ruma")
	
	top_consumo_ruma     = fields.Many2one('stock.picking.type', "Tipo Operación Consumo Ruma")

	control_prod_proceso = fields.Many2one('stock.picking.type', "Control de Productos en Proceso")

	cuentas_analisis     = fields.Many2many('account.account','account_rel_parameter_analisis','account_id','parameter_id','Cuentas Analisis')
	tipo_documentos      = fields.Many2many('it.type.document','itd_rel_parameter_analisis','itd_id','parameter_id','Tipo Documentos para Notas de Credito')

	def init(self, cr):
		cr.execute('select id from res_users')
		uid = cr.dictfetchall()
		cr.execute('select id from production_parameter')
		ids = cr.fetchall()
		
		if len(ids) == 0:
			cr.execute("""INSERT INTO production_parameter (create_uid, name) VALUES (""" + str(uid[0]['id']) + """, 'Parametros Generales');""")


class expedient_products(models.Model):
	_name = "expedient.products"

	main_parameter = fields.Many2one('main.parameter', "Parámetros")
	product_id = fields.Many2one('product.product', "Productos")
