# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.osv import osv
import base64

class kardex_save(models.Model):
	_name = 'kardex.save'
	
	fiscal_id = fields.Many2one('account.fiscalyear','Año Fiscal',required=True)
	period_id = fields.Many2one('account.period','Periodo',required=True)
	usuario = fields.Many2one('res.users','Usuario',readonly=True)

	@api.model
	def create(self,vals):
		t = super(kardex_save,self).create(vals)
		t.write({'usuario':self.env.uid})
		otros = self.env['kardex.save'].search([('fiscal_id','=',t.fiscal_id.id),('period_id','=',t.period_id.id),('id','!=',t.id)])
		if len(otros) > 0:
			raise osv.except_osv('Alerta!','El periodo de Kardex ya existe.')
		return t

	@api.one
	def write(self,vals):
		vals['usuario'] = self.env.uid
		t = super(kardex_save,self).write(vals)
		self.refresh()
		otros = self.env['kardex.save'].search([('fiscal_id','=',self.fiscal_id.id),('period_id','=',self.period_id.id),('id','!=',self.id)])
		if len(otros) > 0:
			raise osv.except_osv('Alerta!','El periodo de Kardex ya existe.')	
		return t

	@api.multi
	def update_or_create_table(self):
		self.write({'usuario':self.env.uid})
		name_t = 'kardex_' + self.fiscal_id.name + '_' + self.period_id.code.replace('/','_')

		productos='{'
		almacenes='{'
		
		lst_products  = self.env['product.product'].search([('type','=','product')])

		for producto in lst_products:
			productos=productos+str(producto.id)+','
		productos=productos[:-1]+'}'

		lst_locations  = self.env['stock.location'].search([('usage','in',('internal','inventory','transit','procurement','production'))])

		for location in lst_locations:
			almacenes=almacenes+str(location.id)+','
		almacenes=almacenes[:-1]+'}'
	

		self.env.cr.execute(""" 
			DROP TABLE IF EXISTS """ + name_t + """;
			CREATE TABLE """ + name_t + """ AS
			 select * from get_kardex_v("""+ str(self.fiscal_id.name) + "0101," + str(self.period_id.date_stop).replace('-','') + ",'" + productos + """'::INT[], '""" + almacenes + """'::INT[]) 
		""")

	@api.multi
	def exportar_kardex_almacenado(self):
		name_t = 'kardex_' + self.fiscal_id.name + '_' + self.period_id.code.replace('/','_')
		cadf="""
			copy (select 
				type_doc as "T. Doc.",
				numdoc_cuadre as "Nro. Documento",
				doc_partner as "Nro Doc. Partner",
				origen as "Origen",
				destino as "Destino",
				almacen AS "Almacen",
				categoria as "Categoria",
				name_template as "Producto",
				fecha_albaran as "Fecha Alm.",
				fecha as "Fecha",
				periodo as "Periodo",
				ctanalitica as "Cta. Analitica",
				doc_almac as "Doc. Almacen",
				serial as "Serie",
				nro as "Nro. Documento",
				operation_type as "Tipo de operacion",
				name as "Proveedor",
				ingreso as "Ingreso Fisico",
				salida as "Salida Fisico",
				saldof as "Saldo Fisico",
				round(debit,6) as "Ingreso Valorado.",
				round(credit,6) as "Salida Valorada",
				round(cadquiere,6) as "Costo adquisicion",
				round(saldov,6) as "Saldo valorado",
				round(cprom,6) as "Costo promedio",cost_account as "Cuenta de costo",
				account_invoice as "Cuenta factura",
				product_account as "Cuenta producto",
				default_code as "Codigo",
				unidad as "Unidad",
				lotept as "LotePT",
				lotemp as "LoteMP"
			from """ +name_t+ """ order by location_id,product_id,fecha,esingreso,nro) to 'e:/PLES_ODOO/kardex.csv'  WITH DELIMITER ',' CSV HEADER 
			"""

		self.env.cr.execute(cadf)
		

		f = open('e:/PLES_ODOO/kardex.csv', 'rb')

		vals = {
			'output_name': 'KardexAlmacenado.csv',
			'output_file': base64.encodestring(''.join(f.readlines())),
		}
		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']
		sfs_id = self.env['export.file.save'].create(vals)
		result = {}

		view_ref = mod_obj.get_object_reference('account_contable_book_it', 'export_file_save_action')
		view_id = view_ref and view_ref[1] or False
		result = act_obj.read( [view_id] )
		print sfs_id

		
		return {
		    "type": "ir.actions.act_window",
		    "res_model": "export.file.save",
		    "views": [[False, "form"]],
		    "res_id": sfs_id.id,
		    "target": "new",
		}


	@api.multi
	def exportar_kardex_guardado_diferencia(self):

		name_t = 'kardex_' + self.fiscal_id.name + '_' + self.period_id.code.replace('/','_')

		productos='{'
		almacenes='{'
		
		lst_products  = self.env['product.product'].search([('type','=','product')])

		for producto in lst_products:
			productos=productos+str(producto.id)+','
		productos=productos[:-1]+'}'

		lst_locations  = self.env['stock.location'].search([('usage','in',('internal','inventory','transit','procurement','production'))])

		for location in lst_locations:
			almacenes=almacenes+str(location.id)+','
		almacenes=almacenes[:-1]+'}'

		cadf="""
			copy (
			select X.* from (
			select 
				type_doc as "T. Doc.",
				numdoc_cuadre as "Nro Documento",
				doc_partner as "Nro Doc. Partner",
				origen as "Origen",
				destino as "Destino",
				almacen AS "Almacen",
				categoria as "Categoria",
				name_template as "Producto",
				fecha_albaran as "Fecha Alm.",
				fecha as "Fecha",
				periodo as "Periodo",
				ctanalitica as "Cta. Analitica",
				doc_almac as "Doc. Almacen",
				serial as "Serie",
				nro as "Nro. Documento",
				operation_type as "Tipo de operacion",
				name as "Proveedor",
				ingreso as "Ingreso Fisico",
				salida as "Salida Fisico",
				saldof as "Saldo Fisico",
				round(debit,6) as "Ingreso Valorado",
				round(credit,6) as "Salida Valorada",
				round(cadquiere,6) as "Costo adquisicion",
				round(saldov,6) as "Saldo valorado",
				round(cprom,6) as "Costo promedio",cost_account as "Cuenta de costo",
				account_invoice as "Cuenta factura",
				product_account as "Cuenta producto",
				default_code as "Codigo",
				unidad as "Unidad",
				stock_moveid as "ID",
				lotept as "LotePT",
				lotemp as "LoteMP"
			from get_kardex_v("""+ str(self.fiscal_id.name) + "0101," + str(self.period_id.date_stop).replace('-','')  + ",'" + productos + """'::INT[], '""" + almacenes + """'::INT[]) ) as X
			full join 
			    (
					select 
					type_doc as "T. Doc.",
					numdoc_cuadre as "Nro Documento",
					doc_partner as "Nro Doc. Partner",
					origen as "Origen",
					destino as "Destino",
					almacen AS "Almacen",
					categoria as "Categoria",
					name_template as "Producto",
					fecha_albaran as "Fecha Alm.",
					fecha as "Fecha",
					periodo as "Periodo",
					ctanalitica as "Cta. Analitica",
					doc_almac as "Doc. Almacen",
					serial as "Serie",
					nro as "Nro. Documento",
					operation_type as "Tipo de operacion",
					name as "Proveedor",
					ingreso as "Ingreso Fisico",
					salida as "Salida Fisico",
					saldof as "Saldo Fisico",
					round(debit,6) as "Ingreso Valorado",
					round(credit,6) as "Salida Valorada",
					round(cadquiere,6) as "Costo adquisicion",
					round(saldov,6) as "Saldo valorado",
					round(cprom,6) as "Costo promedio",cost_account as "Cuenta de costo",
					account_invoice as "Cuenta factura",
					product_account as "Cuenta producto",
					default_code as "Codigo",
					unidad as "Unidad",
					stock_moveid as "ID",
				lotept as "LotePT",
				lotemp as "LoteMP"
					from """ + name_t + """
			    ) as Y on X."Origen" = Y."Origen" and X."Destino" = Y."Destino" and X."Almacen"=Y."Almacen" and X."ID" = Y."ID" 

			where (Y."Nro. Documento" is null or X."Ingreso Fisico" != Y."Ingreso Fisico" or X."Salida Fisico" != Y."Salida Fisico" or X."Ingreso Valorado" != Y."Ingreso Valorado"
			or X."Saldo Fisico" != Y."Saldo Fisico"
			or X."Salida Valorada" != Y."Salida Valorada" or X."Costo adquisicion" != Y."Costo adquisicion" or X."Saldo valorado" != X."Saldo valorado"
			or X."Costo promedio" != Y."Costo promedio" or X."Cuenta de costo" != Y."Cuenta de costo" or X."Cuenta factura" != Y."Cuenta factura"
			or X."Cuenta producto" != Y."Cuenta producto" or X."Codigo" != Y."Codigo" or X."Unidad" != Y."Unidad" or X."LotePT" != Y."LotePT" or X."LoteMP" != Y."LoteMP") and X."Nro. Documento" is not null
			) to 'e:/PLES_ODOO/kardex.csv'  WITH DELIMITER ',' CSV HEADER 
			"""

		self.env.cr.execute(cadf)

		f = open('e:/PLES_ODOO/nn.txt', 'w')
		f.write(cadf)
		f.close()


		f = open('e:/PLES_ODOO/kardex.csv', 'rb')

		vals = {
			'output_name': 'KardexGuardadoDiferencia.csv',
			'output_file': base64.encodestring(''.join(f.readlines())),
		}
		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']
		sfs_id = self.env['export.file.save'].create(vals)
		result = {}
		
		view_ref = mod_obj.get_object_reference('account_contable_book_it', 'export_file_save_action')
		view_id = view_ref and view_ref[1] or False
		result = act_obj.read( [view_id] )
		print sfs_id

		return {
		    "type": "ir.actions.act_window",
		    "res_model": "export.file.save",
		    "views": [[False, "form"]],
		    "res_id": sfs_id.id,
		    "target": "new",
		}


	@api.multi
	def exportar_kardex_nuevo_diferencia(self):

		name_t = 'kardex_' + self.fiscal_id.name + '_' + self.period_id.code.replace('/','_')

		productos='{'
		almacenes='{'
		
		lst_products  = self.env['product.product'].search([('type','=','product')])

		for producto in lst_products:
			productos=productos+str(producto.id)+','
		productos=productos[:-1]+'}'

		lst_locations  = self.env['stock.location'].search([('usage','in',('internal','inventory','transit','procurement','production'))])

		for location in lst_locations:
			almacenes=almacenes+str(location.id)+','
		almacenes=almacenes[:-1]+'}'

		cadf="""
			copy (
			select X.* from (
			select 
				type_doc as "T. Doc.",
				numdoc_cuadre as "Nro Documento",
				doc_partner as "Nro Doc. Partner",
				origen as "Origen",
				destino as "Destino",
				almacen AS "Almacen",
				categoria as "Categoria",
				name_template as "Producto",
				fecha_albaran as "Fecha Alm.",
				fecha as "Fecha",
				periodo as "Periodo",
				ctanalitica as "Cta. Analitica",
				doc_almac as "Doc. Almacen",
				serial as "Serie",
				nro as "Nro. Documento",
				operation_type as "Tipo de operacion",
				name as "Proveedor",
				ingreso as "Ingreso Fisico",
				salida as "Salida Fisico",
				saldof as "Saldo Fisico",
				round(debit,6) as "Ingreso Valorado",
				round(credit,6) as "Salida Valorada",
				round(cadquiere,6) as "Costo adquisicion",
				round(saldov,6) as "Saldo valorado",
				round(cprom,6) as "Costo promedio",cost_account as "Cuenta de costo",
				account_invoice as "Cuenta factura",
				product_account as "Cuenta producto",
				default_code as "Codigo",
				unidad as "Unidad",
					stock_moveid as "ID",
				lotept as "LotePT",
				lotemp as "LoteMP"
			from get_kardex_v("""+ str(self.fiscal_id.name) + "0101," + str(self.period_id.date_stop).replace('-','')  + ",'" + productos + """'::INT[], '""" + almacenes + """'::INT[]) ) as Y
			full join 
			    (
			    	select 
					type_doc as "T. Doc.",
					numdoc_cuadre as "Nro Documento",
					doc_partner as "Nro Doc. Partner",
					origen as "Origen",
					destino as "Destino",
					almacen AS "Almacen",
					categoria as "Categoria",
					name_template as "Producto",
				fecha_albaran as "Fecha Alm.",
					fecha as "Fecha",
					periodo as "Periodo",
					ctanalitica as "Cta. Analitica",
					doc_almac as "Doc. Almacen",
					serial as "Serie",
					nro as "Nro. Documento",
					operation_type as "Tipo de operacion",
					name as "Proveedor",
					ingreso as "Ingreso Fisico",
					salida as "Salida Fisico",
					saldof as "Saldo Fisico",
					round(debit,6) as "Ingreso Valorado",
					round(credit,6) as "Salida Valorada",
					round(cadquiere,6) as "Costo adquisicion",
					round(saldov,6) as "Saldo valorado",
					round(cprom,6) as "Costo promedio",cost_account as "Cuenta de costo",
					account_invoice as "Cuenta factura",
					product_account as "Cuenta producto",
					default_code as "Codigo",
					unidad as "Unidad",
					stock_moveid as "ID"
					from """ + name_t + """,
				lotept as "LotePT",
				lotemp as "LoteMP"
			    ) as X on X."Origen" = Y."Origen" and X."Destino" = Y."Destino" and X."Almacen"=Y."Almacen" and X."ID" = Y."ID" 

			where (Y."Nro. Documento" is null or X."Ingreso Fisico" != Y."Ingreso Fisico" or X."Salida Fisico" != Y."Salida Fisico" or X."Ingreso Valorado" != Y."Ingreso Valorado"
			or X."Saldo Fisico" != Y."Saldo Fisico"
			or X."Salida Valorada" != Y."Salida Valorada" or X."Costo adquisicion" != Y."Costo adquisicion" or X."Saldo valorado" != X."Saldo valorado"
			or X."Costo promedio" != Y."Costo promedio" or X."Cuenta de costo" != Y."Cuenta de costo" or X."Cuenta factura" != Y."Cuenta factura"
			or X."Cuenta producto" != Y."Cuenta producto" or X."Codigo" != Y."Codigo" or X."Unidad" != Y."Unidad" or X."LotePT" != Y."LotePT" or X."LoteMP" != Y."LoteMP") and X."Nro. Documento" is not null
			) to 'e:/PLES_ODOO/kardex.csv'  WITH DELIMITER ',' CSV HEADER 
			"""
		self.env.cr.execute(cadf)
		f = open('e:/PLES_ODOO/kardex.csv', 'rb')
		vals = {
			'output_name': 'KardexNuevoDiferencia.csv',
			'output_file': base64.encodestring(''.join(f.readlines())),
		}
		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']
		sfs_id = self.env['export.file.save'].create(vals)
		result = {}		

		view_ref = mod_obj.get_object_reference('account_contable_book_it', 'export_file_save_action')
		view_id = view_ref and view_ref[1] or False
		result = act_obj.read( [view_id] )
		print sfs_id

		return {
			"type": "ir.actions.act_window",
			"res_model": "export.file.save",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}