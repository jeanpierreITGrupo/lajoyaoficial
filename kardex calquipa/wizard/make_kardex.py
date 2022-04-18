# -*- coding: utf-8 -*-
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
import time
import openerp.addons.decimal_precision as dp
from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
values = {}

class make_kardex(osv.TransientModel):
	_name = "make.kardex"
	period_id= fields.Many2one('account.period','Periodo')
	fini= fields.Date('Fecha inicial',required=True)
	ffin= fields.Date('Fecha final',required=True)
	products_ids=fields.Many2many('product.product','rel_wiz_kardex','product_id','kardex_id',required=False)
	location_ids=fields.Many2many('stock.location','rel_kardex_location','location_id','kardex_id','Ubicacion',required=True)
	allproducts=fields.Boolean('Todos los productos')
	destino = fields.Selection([('csv','CSV'),('crt','Pantalla')],'Destino')
	check_fecha = fields.Boolean('Editar Fecha')
	alllocations = fields.Boolean('Todos los almacenes')

	fecha_ini_mod = fields.Date('Fecha Inicial')
	fecha_fin_mod = fields.Date('Fecha Final')
	analizador = fields.Boolean('Analizador',compute="get_analizador")
	


	@api.multi
	def get_analizador(self):
		print "contexto",self.env.context
		if 'tipo' in self.env.context:
			if self.env.context['tipo'] == 'valorado':
				self.analizador = True
			else:
				self.analizador = False				
		else:
			self.analizador = False

	_defaults={
		'destino':'crt',
		'check_fecha': False,
		'allproducts': True,
		'alllocations': True,
	}
	
	@api.onchange('fecha_ini_mod')
	def onchange_fecha_ini_mod(self):
		self.fini = self.fecha_ini_mod


	@api.onchange('fecha_fin_mod')
	def onchange_fecha_fin_mod(self):
		self.ffin = self.fecha_fin_mod

	def default_get(self, cr, uid, fields, context=None):
		res = super(make_kardex, self).default_get(cr, uid, fields, context=context)
		import datetime
		fecha_hoy = str(datetime.datetime.now())[:10]
		fecha_inicial = fecha_hoy[:4] + '-01-01' 
		res.update({'fecha_ini_mod':fecha_inicial})
		res.update({'fecha_fin_mod':fecha_hoy})
		res.update({'fini':fecha_inicial})
		res.update({'ffin':fecha_hoy})

		locat_ids = self.pool.get('stock.location').search(cr, uid, [('usage','in',('internal','inventory','transit','procurement','production'))])
		res.update({'location_ids':[(6,0,locat_ids)]})
		return res

	@api.onchange('alllocations')
	def onchange_alllocations(self):
		if self.alllocations == True:
			locat_ids = self.env['stock.location'].search( [('usage','in',('internal','inventory','transit','procurement','production'))] )
			self.location_ids = [(6,0,locat_ids.ids)]
		else:
			self.location_ids = [(6,0,[])]

	@api.onchange('period_id')
	def onchange_period_id(self):
		self.fini = self.period_id.date_start
		self.ffin = self.period_id.date_stop


	@api.v7
	def do_compare_purchase(self,cr,uid,ids,context=None):
		data = self.read(cr, uid, ids, [], context=context)[0]	
		cad=""	
		prods= self.pool.get('product.product').search(cr,uid,[])
		locat = self.pool.get('stock.location').search(cr,uid,[])

		lst_products  = prods
		lst_locations = data['location_ids']
		productos='{'
		almacenes='{'
		date_ini=data['fini']
		date_fin=data['ffin']
		
		for producto in lst_products:
			productos=productos+str(producto)+','
		productos=productos[:-1]+'}'
		for location in lst_locations:
			almacenes=almacenes+str(location)+','
		almacenes=almacenes[:-1]+'}'
		# raise osv.except_osv('Alertafis',[almacenes,productos])
		obj_cad= self.pool.get('kardex.account.purchase')
		lst = obj_cad.search(cr,uid,[])
		obj_cad.unlink(cr,uid,lst)

		cadf  = """


				select 
				CASE WHEN A2.code is not null THEN A2.code ELSE A1.periodo END as code,
				CASE WHEN A2.date is not null THEN A2.date ELSE A1.fecha END as date,
				
				A2.diario,
				A2.voucher,
				CASE WHEN A2.td is not null THEN A2.td ELSE A1.doc_type_ope END as td,
				CASE WHEN A2.seried is not null THEN A2.seried ELSE A1.serial END as seried,
				CASE WHEN A2.numerodd is not null THEN A2.numerodd ELSE A1.nro END as numerodd,
				CASE WHEN A2.partner  is not null THEN A2.partner  ELSE A1.name END as partner ,

				coalesce(A1.monto,0) as base, A2.base as valor_factura, coalesce(A1.monto,0)- coalesce(A2.base,0) as diferencia   from (
		select 
				t.periodo,
				t.serial,
				t.nro,
				t.fecha,
				t.operation_type,
				t.doc_type_ope,
				t.name,
				sum(abs(t.debit)) as monto
				from get_kardex_v("""+ date_ini.replace("-","") + "," + date_fin.replace("-","") + ",'" + productos + """'::INT[], '""" + almacenes + """'::INT[]) as T
				inner join stock_location origen on t.ubicacion_origen = origen.id
			    where --account_invoice is not null and account_invoice!='' and 
			    origen.usage = 'supplier'

				-- and doc_type_ope is not null -- and periodo = '""" + str(data['period_id'][1]) + """'
				group by 
				t.periodo,
				t.fecha,
				t.serial,
				t.fecha,
				t.nro,
				t.operation_type,
				t.name,
				t.doc_type_ope
				order by t.periodo,t.serial,t.nro ) as A1
		
				full join ( 
				select account_period.code,
		account_move.date,
		account_journal.name as diario,
		account_move.name as voucher,
		it_type_document.code as td,
		CASE
			WHEN "position"(account_move.dec_reg_nro_comprobante::text, '-'::text) = 0 THEN ''::text
			ELSE "substring"(account_move.dec_reg_nro_comprobante::text, 0, "position"(account_move.dec_reg_nro_comprobante::text, '-'::text))
		END AS seried,
		CASE
			WHEN "position"(account_move.dec_reg_nro_comprobante::text, '-'::text) = 0 THEN account_move.dec_reg_nro_comprobante::text
			ELSE "substring"(account_move.dec_reg_nro_comprobante::text, "position"(account_move.dec_reg_nro_comprobante::text, '-'::text) + 1)
		END AS numerodd,
		res_partner.name as partner,
		sum((account_move_line.debit)) as base
				from account_move
				inner join account_move_line on account_move.id = account_move_line.move_id
				inner join account_account on account_move_line.account_id = account_account.id
		inner join it_type_document on account_move.dec_reg_type_document_id = it_type_document.id
		inner join account_journal on account_move.journal_id = account_journal.id
				left join res_partner on account_move_line.partner_id = res_partner.id
				left join product_product on account_move_line.product_id = product_product.id
		left join product_template on product_product.product_tmpl_id = product_template.id
				inner join account_period on account_move.period_id = account_period.id
				where (account_account.code like '20%' or account_account.code like '25%' or account_account.code like '24%' or account_account.code like '26%') and account_period.id = """+ str(data['period_id'][0])+"""
				group by 
		account_period.code,
		account_journal.name,
		account_move.name,
		account_move.date,
		it_type_document.code,
		account_move.dec_reg_nro_comprobante,
		res_partner.name
		order by res_partner.name
				) as A2 on A1.serial  = A2.seried and A1.nro = A2.numerodd 


			"""
		# raise osv.except_osv('Alertafis',cadf)

		cr.execute(cadf)
		kardexdata=cr.dictfetchall()
		for diferente in kardexdata:
			vals={
				'periodo':diferente['code'],
				'fecha':diferente['date'],
				'libro':diferente['diario'],
				'voucher':diferente['voucher'],
				'td':diferente['td'],
				'serie':diferente['seried'],
				'numero':diferente['numerodd'],
				'proveedor':diferente['partner'],
				'base':diferente['base'],
				'valor_factura':diferente['valor_factura'],
				'diferencia':diferente['diferencia'],
			}
			obj_cad.create(cr,uid,vals)

			

		view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'kardex', 'view_kardex_account_purchase_tree')
		view_id = view_ref and view_ref[1] or False
		search_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'kardex', 'view_kardex_account_purchase_filter')
		
		return {
					'domain':[('diferencia','!=',0)],
					'type': 'ir.actions.act_window',
					'name': 'Kardex vs Compras',
					'res_model': 'kardex.account.purchase',
					'view_mode': 'tree',
					'view_type': 'form',				
					'target': 'current',
					'search_view_id':search_ref[1],
				}

	@api.v7
	def do_csv_resume(self,cr,uid,ids,context=None):
		data = self.read(cr, uid, ids, [], context=context)[0]	
		cad=""	
		prods= self.pool.get('product.product').search(cr,uid,[])
		locat = self.pool.get('stock.location').search(cr,uid,[])

		lst_products  = prods
		lst_locations = data['location_ids']
		productos='{'
		almacenes='{'
		date_ini=data['fini']
		date_fin=data['ffin']
		
		for producto in lst_products:
			productos=productos+str(producto)+','
		productos=productos[:-1]+'}'
		for location in lst_locations:
			almacenes=almacenes+str(location)+','
		almacenes=almacenes[:-1]+'}'
		# raise osv.except_osv('Alertafis',[almacenes,productos])
		if data['destino']=='csv':
			
			cadf=self.make_cad_res(cr,uid,date_ini,date_fin, productos , almacenes,'csv')
			cr.execute(cadf)
			f = open('e:/PLES_ODOO/kardex_cta.csv', 'rb')
			sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
			vals = {
				'output_name': 'kardex_cta.csv',
				'output_file': base64.encodestring(''.join(f.readlines())),		
			}
			mod_obj = self.pool.get('ir.model.data')
			act_obj = self.pool.get('ir.actions.act_window')
			sfs_id = self.pool.get('export.file.save').create(cr,uid,vals)
			result = {}
			view_ref = mod_obj.get_object_reference(cr,uid,'account_contable_book_it', 'export_file_save_action')
			view_id = view_ref and view_ref[1] or False
			result = act_obj.read( cr,uid,[view_id],context )
			return {
			    "type": "ir.actions.act_window",
			    "res_model": "export.file.save",
			    "views": [[False, "form"]],
			    "res_id": sfs_id,
			    "target": "new",
			}
		else:

			obj_cad= self.pool.get('kardex.resume')
			lst = obj_cad.search(cr,uid,[])
			obj_cad.unlink(cr,uid,lst)
			#cadf=self.make_cad_res(cr,uid,date_ini,date_fin, productos , almacenes,'crt')


			cadf  = """select A2.cuenta, coalesce(A1.debe,0) as saldo, A2.debit as contable,coalesce(A1.debe,0) - A2.debit as dif    from (
			select "Cuenta producto",sum("Ingreso Valorado.") as debe,round(sum("Salida Valorada"),2) as haber,
			sum("Ingreso Valorado.") as saldo
			
			from (select 
			get_kardex_v.almacen AS "Almacen",
			get_kardex_v.categoria as "Categoria",
			get_kardex_v.name_template as "Producto",
			get_kardex_v.fecha as "Fecha",
			get_kardex_v.ctanalitica as "Cta. Analitica",
			get_kardex_v.serial as "Serie",
			get_kardex_v.nro as "Nro. Documento", 
			get_kardex_v.operation_type as "Tipo de operacion",
			get_kardex_v.name as "Proveedor",
			get_kardex_v.ingreso as "Ingreso Fisico",
			get_kardex_v.salida as "Salida Fisico",
			get_kardex_v.saldof as "Saldo Fisico",
			get_kardex_v.debit as "Ingreso Valorado.",
			get_kardex_v.credit as "Salida Valorada",
			get_kardex_v.cadquiere as "Costo adquisicion",
			get_kardex_v.saldov as "Saldo valorado",
			get_kardex_v.cprom as "Costo promedio",
			get_kardex_v.cost_account as "Cuenta de costo",
			get_kardex_v.account_invoice as "Cuenta factura",
			get_kardex_v.product_account as "Cuenta producto",
			default_code as "Codigo",unidad as "Unidad",
			get_kardex_v.product_id,
			get_kardex_v.documento_partner,
			get_kardex_v.ubicacion_origen 
							from get_kardex_v("""+ date_ini.replace("-","") + "," + date_fin.replace("-","") + ",'" + productos + """'::INT[], '""" + almacenes + """'::INT[]) 
			order by location_id,product_id,fecha,esingreso,nro
			) t
			inner join stock_location origen on t.ubicacion_origen = origen.id
			where  origen.usage = 'supplier' -- and "Periodo" = '""" + str(data['period_id'][1]) + """'
			group by "Cuenta producto"
			order by "Cuenta producto" ) as A1
				full join ( 
				select account_period.code as "Periodo",
				account_account.code || ' - ' || account_account.name as cuenta,
				sum(account_move_line.debit ) as debit
				from account_move
				inner join account_move_line on account_move.id = account_move_line.move_id
				inner join account_account on account_move_line.account_id = account_account.id
				left join res_partner on account_move_line.partner_id = res_partner.id
				--inner join product_product on account_move_line.product_id = product_product.id
				inner join account_period on account_move.period_id = account_period.id
				where (account_account.code like '20%' or account_account.code like '25%' or account_account.code like '24%' or account_account.code like '26%' ) and account_period.id = """+ str(data['period_id'][0])+"""
				group by 
				account_period.code,
				account_account.code || ' - ' || account_account.name 
				) as A2 on A1."Cuenta producto" = A2.cuenta
				"""


			#raise osv.except_osv('Alertafis',cadf)
			cr.execute(cadf)
			dicf=cr.dictfetchall()
			for data_c in dicf:
				obj_cad.create(cr,uid,{'periodo':data['period_id'][1],'cta':data_c['cuenta'],'monto':data_c['saldo'],'contable':data_c['contable'],'dif':data_c['dif']})


				

			view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'kardex', 'view_kardex_resume_tree')
			view_id = view_ref and view_ref[1] or False
			search_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'kardex', 'view_kardex_resume_filter')
			
			return {
						'domain':[('dif','!=',0)],
						'type': 'ir.actions.act_window',
						'name': 'Kardex: Resumen X Cta. ',
						'res_model': 'kardex.resume',
						'view_mode': 'tree',
						'view_type': 'form',				
						'target': 'current',
						'search_view_id':search_ref[1],
					}



	@api.v7
	def kardex_vs_account_line(self,cr,uid,ids,context=None):
		data = self.read(cr, uid, ids, [], context=context)[0]	
		cad=""	
		prods= self.pool.get('product.product').search(cr,uid,[])
		locat = self.pool.get('stock.location').search(cr,uid,[])

		lst_products  = prods
		lst_locations = data['location_ids']
		productos='{'
		almacenes='{'
		date_ini=data['fini']
		date_fin=data['ffin']
		
		for producto in lst_products:
			productos=productos+str(producto)+','
		productos=productos[:-1]+'}'
		for location in lst_locations:
			almacenes=almacenes+str(location)+','
		almacenes=almacenes[:-1]+'}'
		# raise osv.except_osv('Alertafis',[almacenes,productos])
		obj_cad= self.pool.get('kardex.vs.account.line')

		lst = obj_cad.search(cr,uid,[])
		obj_cad.unlink(cr,uid,lst)

		# cadf=self.make_cad_res(cr,uid,date_ini,date_fin, productos , almacenes,'crt')
		# raise osv.except_osv('Alertafis',cadf)

		cadf  = """select * from (
select cuenta, proveedor, dec_reg_nro_comprobante, name_template, sum(montokardex) as montokardex, sum(monto) as monto, sum(diference) as diferencia from (

		select CASE WHEN A2.cuenta is not null THEN A2.cuenta ELSE A1."Cuenta producto" END as cuenta, 
CASE WHEN A2.proveedor is not null THEN A2.proveedor ELSE A1."Proveedor" END as proveedor , CASE WHEN A2.dec_reg_nro_comprobante is not null THEN A2.dec_reg_nro_comprobante ELSE A1."Factura" END as dec_reg_nro_comprobante
 , CASE WHEN A2.name_template is not null THEN A2.name_template ELSE A1."Producto" END as name_template, coalesce(A1.debe,0) as montokardex, coalesce(A2.debit,0) as monto, coalesce(A1.debe,0) - coalesce(A2.debit,0) as diference    from (
			select "Cuenta producto",sum("Ingreso Valorado.") as debe,round(sum("Salida Valorada"),2) as haber,
			sum("Ingreso Valorado.") as saldo,"Periodo",
			case when "Serie" is not null then "Serie"||'-'||"Nro. Documento" else "Nro. Documento" end as "Factura",
			"Producto","Proveedor",product_id,documento_partner
			from (select 
			get_kardex_v.almacen AS "Almacen",
			get_kardex_v.categoria as "Categoria",
			get_kardex_v.name_template as "Producto",
			get_kardex_v.fecha as "Fecha",
			get_kardex_v.periodo as "Periodo",
			get_kardex_v.ctanalitica as "Cta. Analitica",
			get_kardex_v.serial as "Serie",
			get_kardex_v.nro as "Nro. Documento", 
			get_kardex_v.operation_type as "Tipo de operacion",
			get_kardex_v.name as "Proveedor",
			get_kardex_v.ingreso as "Ingreso Fisico",
			get_kardex_v.salida as "Salida Fisico",
			get_kardex_v.saldof as "Saldo Fisico",
			get_kardex_v.debit as "Ingreso Valorado.",
			get_kardex_v.credit as "Salida Valorada",
			get_kardex_v.cadquiere as "Costo adquisicion",
			get_kardex_v.saldov as "Saldo valorado",
			get_kardex_v.cprom as "Costo promedio",
			get_kardex_v.cost_account as "Cuenta de costo",
			get_kardex_v.account_invoice as "Cuenta factura",
			get_kardex_v.product_account as "Cuenta producto",
			default_code as "Codigo",unidad as "Unidad",
			get_kardex_v.product_id,
			get_kardex_v.documento_partner,
			get_kardex_v.ubicacion_origen 
							from get_kardex_v("""+date_ini.replace("-","") + "," + date_fin.replace("-","")+ ",'" + productos + """'::INT[], '""" + almacenes + """'::INT[]) 
			order by location_id,product_id,fecha,esingreso,nro
			) t
			inner join stock_location origen on t.ubicacion_origen = origen.id 
			where --"Cuenta factura" is not null and "Cuenta factura"!='' and 
			origen.usage = 'supplier' -- and "Periodo" = '""" + str(data['period_id'][1]) + """'
			group by "Cuenta producto","Periodo","Serie", "Nro. Documento","Producto","Proveedor","Producto",product_id,documento_partner
			order by "Periodo","Proveedor","Serie", "Nro. Documento","Producto" ) as A1
				full join ( 
				select account_period.code,
				account_account.code || ' - ' || account_account.name as cuenta,
				account_move.dec_reg_nro_comprobante,
				CASE WHEN product_product.name_template is not null THEN product_product.name_template ELSE 'Nulo' END as name_template,
				sum(account_move_line.debit ) as debit,
				res_partner.name as proveedor,
				account_move_line.product_id,res_partner.type_number
				from account_move
				inner join account_move_line on account_move.id = account_move_line.move_id
				inner join account_account on account_move_line.account_id = account_account.id
				left join res_partner on account_move_line.partner_id = res_partner.id
				left join product_product on account_move_line.product_id = product_product.id
				inner join account_period on account_move.period_id = account_period.id
				where (account_account.code like '20%' or account_account.code like '25%' or account_account.code like '24%' or account_account.code like '26%' ) and account_period.id = """+ str(data['period_id'][0])+"""
				group by 
				account_period.code,
				account_account.code || ' - ' || account_account.name ,
				account_move.dec_reg_nro_comprobante,
				product_product.name_template,
				account_move_line.product_id,
				res_partner.name,res_partner.type_number ) as A2 on replace(A1."Factura",' ','') = replace(A2.dec_reg_nro_comprobante,' ','') and A1.product_id = A2.product_id
				and replace(A1.documento_partner,' ','') = replace(A2.type_number,' ','') and replace(A1."Cuenta producto",' ','') = replace(A2.cuenta,' ','')
)as X group by cuenta, proveedor, dec_reg_nro_comprobante, name_template ) as XM where diferencia != 0
				"""

		t = open('E:/SQL/x.txt','w')
		t.write(cadf)
		t.close()
		cr.execute(cadf)
		valores = cr.dictfetchall()
		for data_c in valores:
			obj_cad.create(cr,uid,
				{
				'cta':data_c['cuenta'],
				'periodo':data['period_id'][1],
				'proveedor':data_c['proveedor'],
				'factura':data_c['dec_reg_nro_comprobante'],
				'producto':data_c['name_template'],
				'montokardex':data_c['montokardex'],
				'contable':data_c['monto'],
				'dif':data_c['diferencia']})

		view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'kardex', 'view_kardex_vs_account_line_tree')
		view_id = view_ref and view_ref[1] or False
		search_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'kardex', 'view_kardex_vs_account_line_filter')
		
		return {
						'domain':[('dif','!=',0)],
					'type': 'ir.actions.act_window',
					'name': 'Kardex: Comprar lineas',
					'res_model': 'kardex.vs.account.line',
					'view_mode': 'tree',
					'view_type': 'form',				
					'target': 'current',
					'search_view_id':search_ref[1],
				}





	def getkardexsql(self,cr,uid,ids,context={},imprimir=False,listar2=False):
		mkt=self.pool.get('make.kardex.tree')
		cr.execute('delete from make_kardex_tree;')
		data = self.read(cr, uid, ids, [], context=context)[0]	
		cad=""	
		
		if 'allproducts' in data:
			if data['allproducts']:
				lst_products  = self.pool.get('product.product').search(cr,uid,[])
			else:
				lst_products  = data['products_ids']
		else:
			if data['products_ids']==[]:
				raise osv.except_osv('Alerta','No existen productos seleccionados')
				return
			lst_products  = data['products_ids']


		lst_locations = data['location_ids']

		productos='{'
		almacenes='{'
		date_ini=data['fini']
		date_fin=data['ffin']
		for producto in lst_products:
			productos=productos+str(producto)+','
		productos=productos[:-1]+'}'
		for location in lst_locations:
			almacenes=almacenes+str(location)+','
		almacenes=almacenes[:-1]+'}'
		# raise osv.except_osv('Alertafis',[almacenes,productos])
		print 'tipo',context['tipo']
		if context['tipo']=='valorado':
			cadf="select * from get_kardex_v("+date_ini.replace("-","") + "," + date_fin.replace("-","") + ",'" + productos + "'::INT[], '" + almacenes + "'::INT[]) order by location_id,product_id,fecha,esingreso,nro"
		else:
			if context['tipo']=='fisico':
				cadf="select * from get_kardex_v("+date_ini.replace("-","") + "," + date_fin.replace("-","") + ",'" + productos + "'::INT[], '" + almacenes + "'::INT[]) order by location_id,product_id,fecha,esingreso,nro"
			else:
				cadf="select * from get_kardex_fis_sumi("+date_ini.replace("-","") + "," + date_fin.replace("-","") + ",'" + productos + "'::INT[], '" + almacenes + "'::INT[]) order by location_id,product_id,fecha,esingreso,nro"							
		raise osv.except_osv('Alertafis',cadf)
		cr.execute(cadf)
		ds = cr.dictfetchall()
		if context['tipo']!='valorado':
			ds = self.makevalues(cr,uid,ds,lst_products,lst_locations,context)
		for linea in ds:
			valores={
				'location_id':linea['almacen'],
				'producto':linea['name_template'],
				'category_id':linea['categoria'],
				'date':linea['fecha'],   
				'type_doc':linea['doc_type_ope'],
				'serial_doc':linea['serial'],
				'num_doc':linea['nro'],
				'type_ope':linea['operation_type'],	
				'partner_id':linea['name'],	
				'input':linea['ingreso'],
				'output':linea['salida'],
				'saldo':linea['saldof'],
				'period_id':linea['periodo'],
				'cadquiere':linea['cadquiere'],
				'debit':linea['debit'],
				'credit':linea['credit'],
				'saldoval':linea['saldov'],
				'cprom':linea['cprom'],
				'analitic_id':linea['ctanalitica'],
				'analitic_id2':None,
				'cost_account':linea['cost_account'] if 'cost_account' in linea else '',
				'account_invoice':linea['account_invoice'] if 'account_invoice' in linea else '',
				'product_account':linea['product_account'] if 'product_account' in linea else ''
			}
			mkt.create(cr,uid,valores,context)

		if context['tipo']=='valorado':
			view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'kardex', 'view_make_kardex_tree_val')
		else:
			view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'kardex', 'view_make_kardex_tree_fis')
		
		view_id = view_ref and view_ref[1] or False
		# raise osv.except_osv('Alertafis',ds)
		return {
					'type': 'ir.actions.act_window',
					'name': 'Kardex',
					'res_model': 'make.kardex.tree',
					'view_mode': 'tree',
					'view_type': 'form',				
					'view_id': view_id,
					'target': 'current',
					'nodestroy': True,
					'multi':True,
				}
		# return True

	"""
	select distinct account_invoice.id,account_invoice.name,
	account_invoice.supplier_invoice_number,res_partner.name,
	account_invoice.date_invoice
	from account_invoice 
	inner join account_invoice_line on account_invoice.id = account_invoice_line.invoice_id
	inner join product_product on account_invoice_line.product_id = product_product.id
	inner join product_template on product_product.product_tmpl_id = product_template.id
	inner join res_partner on account_invoice.partner_id =res_partner.id
	where product_template.type = 'product' and account_invoice.state in ('open','paid')
	and account_invoice.id not in (
	select distinct account_invoice.id
	from stock_move
	inner join product_product on stock_move.product_id = product_product.id
	inner join product_template on product_product.product_tmpl_id = product_template.id
	inner join stock_picking on stock_move.picking_id = stock_picking.id
	inner join account_invoice on stock_move.invoice_id = account_invoice.id
	where (stock_picking.invoice_id is not null or stock_move.invoice_id is not null) and 
	product_template.type = 'product'
	union
	select distinct account_invoice.id
	from stock_move
	inner join product_product on stock_move.product_id = product_product.id
	inner join product_template on product_product.product_tmpl_id = product_template.id
	inner join stock_picking on stock_move.picking_id = stock_picking.id
	inner join account_invoice on stock_picking.invoice_id = account_invoice.id
	where (stock_picking.invoice_id is not null or stock_move.invoice_id is not null) and 
	product_template.type = 'product'
	)
	"""


	@api.v7
	def do_saldocta_csv(self,cr,uid,ids,context=None):
		data = self.read(cr, uid, ids, [], context=context)[0]	
		cad=""	
		if data['products_ids']==[]:
			raise osv.except_osv('Alerta','No existen productos seleccionados')
			return
		lst_products  = data['products_ids']
		lst_locations = data['location_ids']
		productos='{'
		almacenes='{'
		date_ini=data['fini']
		date_fin=data['ffin']
		if 'allproducts' in data:
			if data['allproducts']:
				lst_products  = self.pool.get('product.product').search(cr,uid,[])
			else:
				lst_products  = data['products_ids']
		else:
			lst_products  = data['products_ids']


		for producto in lst_products:
			productos=productos+str(producto)+','
		productos=productos[:-1]+'}'
		for location in lst_locations:
			almacenes=almacenes+str(location)+','
		almacenes=almacenes[:-1]+'}'
		# raise osv.except_osv('Alertafis',[almacenes,productos])
		print 'tipo',context['tipo']
		if context['tipo']=='valorado':
			cadf="""
				copy (select "Cuenta factura",sum("Ingreso Valorado.") as debe,sum("Salida Valorada") as haber,
				sum("Ingreso Valorado.")-sum("Salida Valorada") as saldo
				from (select 
				almacen AS "Almacen",
				categoria as "Categoria",
				name_template as "Producto",
				fecha as "Fecha",
				periodo as "Periodo",
				ctanalitica as "Cta. Analitica",
				serial as "Serie",
				nro as "Nro. Documento",
				operation_type as "Tipo de operacion",
				name as "Proveedor",
				ingreso as "Ingreso Fisico",
				salida as "Salida Fisico",
				saldof as "Saldo Fisico",
				debit as "Ingreso Valorado.",
				credit as "Salida Valorada",
				cadquiere as "Costo adquisicion",
				saldov as "Saldo valorado",
				cprom as "Costo promedio",cost_account as "Cuenta de costo",account_invoice as "Cuenta factura",product_account as "Cuenta producto",default_code as "Codigo",unidad as "Unidad"
				from get_kardex_v("""+date_ini.replace("-","") + "," + date_fin.replace("-","") + ",'" + productos + """'::INT[], '""" + almacenes + """'::INT[]) 
				order by location_id,product_id,fecha,esingreso,nro) t
				where "Cuenta factura" is not null and "Cuenta factura"!='' 
				group by "Cuenta factura"
				) 
				to 'e:/PLES_ODOO/kardex_cta.csv'  WITH DELIMITER ',' CSV HEADER 
				"""
		# raise osv.except_osv('Alertafis',cadf)

		cr.execute(cadf)
		

		f = open('e:/PLES_ODOO/kardex_cta.csv', 'rb')
			
			
		sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
		vals = {
			'output_name': 'kardex_cta.csv',
			'output_file': base64.encodestring(''.join(f.readlines())),		
		}

		mod_obj = self.pool.get('ir.model.data')
		act_obj = self.pool.get('ir.actions.act_window')
		sfs_id = self.pool.get('export.file.save').create(cr,uid,vals)
		result = {}
		view_ref = mod_obj.get_object_reference(cr,uid,'account_contable_book_it', 'export_file_save_action')
		view_id = view_ref and view_ref[1] or False
		result = act_obj.read( cr,uid,[view_id],context )
		print sfs_id

		#import os
		#os.system('c:\\eSpeak2\\command_line\\espeak.exe -ves-f1 -s 170 -p 100 "Se Realizo La exportación exitosamente Y A EDWARD NO LE GUSTA XDXDXDXDDDDDDDDDDDD" ')

		return {
		    "type": "ir.actions.act_window",
		    "res_model": "export.file.save",
		    "views": [[False, "form"]],
		    "res_id": sfs_id,
		    "target": "new",
		}


	@api.v7
	def do_csvnewversion(self,cr,uid,ids,context=None):
		data = self.read(cr, uid, ids, [], context=context)[0]	
		cad=""	

		lst_products  = data['products_ids']
		lst_locations = data['location_ids']
		productos='['
		almacenes='['
		date_ini=data['fini']
		date_fin=data['ffin']
		if 'allproducts' in data:
			if data['allproducts']:
				lst_products  = self.pool.get('product.product').search(cr,uid,[])
			else:
				lst_products  = data['products_ids']
		else:
			if data['products_ids']==[]:
				raise osv.except_osv('Alerta','No existen productos seleccionados')
				return
			lst_products  = data['products_ids']


		for producto in lst_products:
			productos=productos+str(producto)+','
		productos=productos[:-1]+']'
		for location in lst_locations:
			almacenes=almacenes+str(location)+','
		almacenes=almacenes[:-1]+']'

		import os
		os.system('python E:/Kardex Python/kardex.py "'+productos+'" "'+almacenes+'" "'+date_ini.replace("-","")+'" "'+date_fin.replace("-","")+'"')

		f = open('E:/Kardex Python/kardex-python.csv','rb')
			
			
		sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
		vals = {
			'output_name': 'kardex.csv',
			'output_file': base64.encodestring(''.join(f.readlines())),		
		}

		mod_obj = self.pool.get('ir.model.data')
		act_obj = self.pool.get('ir.actions.act_window')
		sfs_id = self.pool.get('export.file.save').create(cr,uid,vals)
		result = {}
		view_ref = mod_obj.get_object_reference(cr,uid,'account_contable_book_it', 'export_file_save_action')
		view_id = view_ref and view_ref[1] or False
		result = act_obj.read( cr,uid,[view_id],context )
		print sfs_id

		#import os
		#os.system('c:\\eSpeak2\\command_line\\espeak.exe -ves-f1 -s 170 -p 100 "Se Realizo La exportación exitosamente Y A EDWARD NO LE GUSTA XDXDXDXDDDDDDDDDDDD" ')

		return {
		    "type": "ir.actions.act_window",
		    "res_model": "export.file.save",
		    "views": [[False, "form"]],
		    "res_id": sfs_id,
		    "target": "new",
		}


	@api.multi
	def do_csvtoexcel(self):
		cad = ""

		lst_products  = self.products_ids.ids
		lst_locations = self.location_ids.ids
		productos='{'
		almacenes='{'
		date_ini=self.fini
		date_fin=self.ffin
		if self.allproducts:
			lst_products = self.env['product.product'].search([]).ids
		else:
			lst_products = self.products_ids.ids

		if len(lst_products) == 0:
			raise osv.except_osv('Alerta','No existen productos seleccionados')

		for producto in lst_products:
			productos=productos+str(producto)+','
		productos=productos[:-1]+'}'
		for location in lst_locations:
			almacenes=almacenes+str(location)+','
		almacenes=almacenes[:-1]+'}'
		# raise osv.except_osv('Alertafis',[almacenes,productos])

		if self.env.context['tipo']=='valorado':

			import io
			from xlsxwriter.workbook import Workbook
			output = io.BytesIO()
			########### PRIMERA HOJA DE LA DATA EN TABLA
			#workbook = Workbook(output, {'in_memory': True})

			direccion = self.env['main.parameter'].search([])[0].dir_create_file
			workbook = Workbook(direccion +'kardex_producto.xlsx')
			worksheet = workbook.add_worksheet("Kardex")
			bold = workbook.add_format({'bold': True})
			bold.set_font_size(8)
			normal = workbook.add_format()
			boldbord = workbook.add_format({'bold': True})
			boldbord.set_border(style=2)
			boldbord.set_align('center')
			boldbord.set_align('vcenter')
			boldbord.set_text_wrap()
			boldbord.set_font_size(8)
			boldbord.set_bg_color('#DCE6F1')

			especial1 = workbook.add_format({'bold': True})
			especial1.set_align('center')
			especial1.set_align('vcenter')
			especial1.set_text_wrap()
			especial1.set_font_size(15)
			
			numbertres = workbook.add_format({'num_format':'0.000'})
			numberdos = workbook.add_format({'num_format':'0.00'})
			numberseis = workbook.add_format({'num_format':'0.000000'})
			numberseis.set_font_size(8)
			numberocho = workbook.add_format({'num_format':'0.00000000'})
			numberocho.set_font_size(8)
			bord = workbook.add_format()
			bord.set_border(style=1)
			bord.set_font_size(8)
			numberdos.set_border(style=1)
			numberdos.set_font_size(8)
			numbertres.set_border(style=1)			
			numberseis.set_border(style=1)			
			numberocho.set_border(style=1)		
			numberdosbold = workbook.add_format({'num_format':'0.00','bold':True})	
			numberdosbold.set_font_size(8)
			x= 10				
			tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			tam_letra = 1.2
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')

			worksheet.merge_range(1,5,1,10, "KARDEX VALORADO", especial1)
			worksheet.write(2,0,'FECHA INICIO:',bold)
			worksheet.write(3,0,'FECHA FIN:',bold)

			worksheet.write(2,1,self.fini)
			worksheet.write(3,1,self.ffin)			
			import datetime		

			worksheet.merge_range(8,0,9,0, u"Fecha Alm.",boldbord)
			worksheet.merge_range(8,1,9,1, u"Fecha",boldbord)
			worksheet.merge_range(8,2,9,2, u"Tipo",boldbord)
			worksheet.merge_range(8,3,9,3, u"Serie",boldbord)
			worksheet.merge_range(8,4,9,4, u"Número",boldbord)
			worksheet.merge_range(8,5,9,5, u"T. OP.",boldbord)
			worksheet.merge_range(8,6,8,7, "Ingreso",boldbord)
			worksheet.write(9,6, "Cantidad",boldbord)
			worksheet.write(9,7, "Costo",boldbord)
			worksheet.merge_range(8,8,8,9, "Salida",boldbord)
			worksheet.write(9,8, "Cantidad",boldbord)
			worksheet.write(9,9, "Costo",boldbord)
			worksheet.merge_range(8,10,8,11, "Saldo",boldbord)
			worksheet.write(9,10, "Cantidad",boldbord)
			worksheet.write(9,11, "Costo",boldbord)
			worksheet.merge_range(8,12,9,12, "Costo Adquisicion",boldbord)
			worksheet.merge_range(8,13,9,13, "Costo Promedio",boldbord)
			worksheet.merge_range(8,14,9,14, "Ubicacion Origen",boldbord)
			worksheet.merge_range(8,15,9,15, "Ubicacion Destino",boldbord)
			worksheet.merge_range(8,16,9,16, "Almacen",boldbord)
			worksheet.merge_range(8,17,9,17, "Cuenta Factura",boldbord)
			worksheet.merge_range(8,18,9,18, "Documento Almacen",boldbord)
			worksheet.merge_range(8,19,9,19, "Producto",boldbord)
			worksheet.merge_range(8,20,9,20, "Unidad Producto",boldbord)
			worksheet.merge_range(8,21,9,21, "Pedido Compra",boldbord)
			worksheet.merge_range(8,22,9,22, "Licitacion",boldbord)


			self.env.cr.execute(""" 
				 select 
				fecha as "Fecha",
				type_doc as "T. Doc.",
				serial as "Serie",
				nro as "Nro. Documento",
				operation_type as "Tipo de operacion",				 
				ingreso as "Ingreso Fisico",
				round(debit,6) as "Ingreso Valorado.",
				salida as "Salida Fisico",
				round(credit,6) as "Salida Valorada",
				saldof as "Saldo Fisico",
				round(saldov,6) as "Saldo valorado",
				round(cadquiere,6) as "Costo adquisicion",
				round(cprom,6) as "Costo promedio",
					origen as "Origen",
					destino as "Destino",
				almacen AS "Almacen",
				account_invoice as "Cuenta factura",
				stock_doc as "Doc. Almacén",
				fecha_albaran as "Fecha Alb.",	
				name_template as "Producto",
				unidad as "Unidad"	,
				pedido_compra as "Pedido de Compra",
				licitacion as "Licitacion"		


				from get_kardex_v("""+ str(date_ini).replace('-','') + "," + str(date_fin).replace('-','') + ",'" + productos + """'::INT[], '""" + almacenes + """'::INT[]) 
			""")

			ingreso1= 0
			ingreso2= 0
			salida1= 0
			salida2= 0

			for line in self.env.cr.fetchall():
				worksheet.write(x,0,line[18] if line[18] else '' ,bord )
				worksheet.write(x,1,line[0] if line[0] else '' ,bord )
				worksheet.write(x,2,line[1] if line[1] else '' ,bord )
				worksheet.write(x,3,line[2] if line[2] else '' ,bord )
				worksheet.write(x,4,line[3] if line[3] else '' ,bord )
				worksheet.write(x,5,line[4] if line[4] else '' ,bord )
				
				worksheet.write(x,6,line[5] if line[5] else 0 ,numberdos )
				worksheet.write(x,7,line[6] if line[6] else 0 ,numberdos )
				worksheet.write(x,8,line[7] if line[7] else 0 ,numberdos )
				worksheet.write(x,9,line[8] if line[8] else 0 ,numberdos )
				worksheet.write(x,10,line[9] if line[9] else 0 ,numberdos )
				worksheet.write(x,11,line[10] if line[10] else 0 ,numberdos )
				worksheet.write(x,12,line[11] if line[11] else 0 ,numberseis )
				worksheet.write(x,13,line[12] if line[12] else 0 ,numberocho )

				worksheet.write(x,14,line[13] if line[13] else '' ,bord )
				worksheet.write(x,15,line[14] if line[14] else '' ,bord )
				worksheet.write(x,16,line[15] if line[15] else '' ,bord )
				worksheet.write(x,17,line[16] if line[16] else '' ,bord )
				worksheet.write(x,18,line[17] if line[17] else '' ,bord )
				worksheet.write(x,19,line[19] if line[19] else '' ,bord )
				worksheet.write(x,20,line[20] if line[20] else '' ,bord )
				worksheet.write(x,21,line[21] if line[21] else '' ,bord )
				worksheet.write(x,22,line[22] if line[22] else '' ,bord )

				ingreso1 += line[5] if line[5] else 0
				ingreso2 +=line[6] if line[6] else 0
				salida1 +=line[7] if line[7] else 0
				salida2 += line[8] if line[8] else 0

				x = x +1

			tam_col = [11,11,5,5,7,5,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11]

			worksheet.write(x,5,'TOTALES:' ,bold )
			worksheet.write(x,6,ingreso1 ,numberdosbold )
			worksheet.write(x,7,ingreso2 ,numberdosbold )
			worksheet.write(x,8,salida1 ,numberdosbold )
			worksheet.write(x,9,salida2 ,numberdosbold )

			worksheet.set_column('A:A', tam_col[0])
			worksheet.set_column('B:B', tam_col[1])
			worksheet.set_column('C:C', tam_col[2])
			worksheet.set_column('D:D', tam_col[3])
			worksheet.set_column('E:E', tam_col[4])
			worksheet.set_column('F:F', tam_col[5])
			worksheet.set_column('G:G', tam_col[6])
			worksheet.set_column('H:H', tam_col[7])
			worksheet.set_column('I:I', tam_col[8])
			worksheet.set_column('J:J', tam_col[9])
			worksheet.set_column('K:K', tam_col[10])
			worksheet.set_column('L:L', tam_col[11])
			worksheet.set_column('M:M', tam_col[12])
			worksheet.set_column('N:N', tam_col[13])
			worksheet.set_column('O:O', tam_col[14])
			worksheet.set_column('P:P', tam_col[15])
			worksheet.set_column('Q:Q', tam_col[16])
			worksheet.set_column('R:R', tam_col[17])
			worksheet.set_column('S:S', tam_col[18])
			worksheet.set_column('T:Z', tam_col[19])

			workbook.close()
			
			f = open(direccion + 'kardex_producto.xlsx', 'rb')
			
			
			sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
			vals = {
				'output_name': 'Kardex.xlsx',
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

			#import os
			#os.system('c:\\eSpeak2\\command_line\\espeak.exe -ves-f1 -s 170 -p 100 "Se Realizo La exportación exitosamente Y A EDWARD NO LE GUSTA XDXDXDXDDDDDDDDDDDD" ')

			return {
			    "type": "ir.actions.act_window",
			    "res_model": "export.file.save",
			    "views": [[False, "form"]],
			    "res_id": sfs_id.id,
			    "target": "new",
			}
		else:
			
			import io
			from xlsxwriter.workbook import Workbook
			output = io.BytesIO()
			########### PRIMERA HOJA DE LA DATA EN TABLA
			#workbook = Workbook(output, {'in_memory': True})

			direccion = self.env['main.parameter'].search([])[0].dir_create_file
			workbook = Workbook(direccion +'kardex_producto.xlsx')
			worksheet = workbook.add_worksheet("Kardex")
			bold = workbook.add_format({'bold': True})
			bold.set_font_size(8)
			normal = workbook.add_format()
			boldbord = workbook.add_format({'bold': True})
			boldbord.set_border(style=2)
			boldbord.set_align('center')
			boldbord.set_align('vcenter')
			boldbord.set_text_wrap()
			boldbord.set_font_size(8)
			boldbord.set_bg_color('#DCE6F1')

			especial1 = workbook.add_format({'bold': True})
			especial1.set_align('center')
			especial1.set_align('vcenter')
			especial1.set_text_wrap()
			especial1.set_font_size(15)
			
			numbertres = workbook.add_format({'num_format':'0.000'})
			numberdos = workbook.add_format({'num_format':'0.00'})
			numberseis = workbook.add_format({'num_format':'0.000000'})
			numberseis.set_font_size(8)
			numberocho = workbook.add_format({'num_format':'0.00000000'})
			numberocho.set_font_size(8)
			bord = workbook.add_format()
			bord.set_border(style=1)
			bord.set_font_size(8)
			numberdos.set_border(style=1)
			numberdos.set_font_size(8)
			numbertres.set_border(style=1)			
			numberseis.set_border(style=1)			
			numberocho.set_border(style=1)		
			numberdosbold = workbook.add_format({'num_format':'0.00','bold':True})	
			numberdosbold.set_font_size(8)
			x= 10				
			tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			tam_letra = 1.2
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')

			worksheet.merge_range(1,5,1,10, "KARDEX VALORADO", especial1)
			worksheet.write(2,0,'FECHA INICIO:',bold)
			worksheet.write(3,0,'FECHA FIN:',bold)

			worksheet.write(2,1,self.fini)
			worksheet.write(3,1,self.ffin)			
			import datetime		

			worksheet.merge_range(8,0,9,0, u"Fecha Alm.",boldbord)
			worksheet.merge_range(8,1,9,1, u"Fecha",boldbord)
			worksheet.merge_range(8,2,9,2, u"Tipo",boldbord)
			worksheet.merge_range(8,3,9,3, u"Serie",boldbord)
			worksheet.merge_range(8,4,9,4, u"Número",boldbord)
			worksheet.merge_range(8,5,9,5, u"T. OP.",boldbord)
			worksheet.write(8,6, "Ingreso",boldbord)
			worksheet.write(9,6, "Cantidad",boldbord)
			worksheet.write(8,7, "Salida",boldbord)
			worksheet.write(9,7, "Cantidad",boldbord)
			worksheet.write(8,8, "Saldo",boldbord)
			worksheet.write(9,8, "Cantidad",boldbord)
			worksheet.merge_range(8,9,9,9, "Ubicacion Origen",boldbord)
			worksheet.merge_range(8,10,9,10, "Ubicacion Destino",boldbord)
			worksheet.merge_range(8,11,9,11, "Almacen",boldbord)
			worksheet.merge_range(8,12,9,12, "Cuenta Factura",boldbord)
			worksheet.merge_range(8,13,9,13, "Documento Almacen",boldbord)
			worksheet.merge_range(8,14,9,14, "Producto",boldbord)
			worksheet.merge_range(8,15,9,15, "Unidad Producto",boldbord)
			worksheet.merge_range(8,16,9,16, "Pedido Compra",boldbord)
			worksheet.merge_range(8,17,9,17, "Licitacion",boldbord)


			self.env.cr.execute(""" 
				 select 
				fecha as "Fecha",
				type_doc as "T. Doc.",
				serial as "Serie",
				nro as "Nro. Documento",
				operation_type as "Tipo de operacion",				 
				ingreso as "Ingreso Fisico",
				round(debit,6) as "Ingreso Valorado.",
				salida as "Salida Fisico",
				round(credit,6) as "Salida Valorada",
				saldof as "Saldo Fisico",
				round(saldov,6) as "Saldo valorado",
				round(cadquiere,6) as "Costo adquisicion",
				round(cprom,6) as "Costo promedio",
					origen as "Origen",
					destino as "Destino",
				almacen AS "Almacen",
				account_invoice as "Cuenta factura",
				stock_doc as "Doc. Almacén",
				fecha_albaran as "Fecha Alb.",	
				name_template as "Producto",
				unidad as "Unidad"	,
				pedido_compra as "Pedido de Compra",
				licitacion as "Licitacion"		


				from get_kardex_v("""+ str(date_ini).replace('-','') + "," + str(date_fin).replace('-','') + ",'" + productos + """'::INT[], '""" + almacenes + """'::INT[]) 
			""")

			ingreso1= 0
			ingreso2= 0
			salida1= 0
			salida2= 0

			for line in self.env.cr.fetchall():
				worksheet.write(x,0,line[18] if line[18] else '' ,bord )
				worksheet.write(x,1,line[0] if line[0] else '' ,bord )
				worksheet.write(x,2,line[1] if line[1] else '' ,bord )
				worksheet.write(x,3,line[2] if line[2] else '' ,bord )
				worksheet.write(x,4,line[3] if line[3] else '' ,bord )
				worksheet.write(x,5,line[4] if line[4] else '' ,bord )
				
				worksheet.write(x,6,line[5] if line[5] else 0 ,numberdos )
				worksheet.write(x,7,line[7] if line[7] else 0 ,numberdos )
				worksheet.write(x,8,line[9] if line[9] else 0 ,numberdos )

				worksheet.write(x,9,line[13] if line[13] else '' ,bord )
				worksheet.write(x,10,line[14] if line[14] else '' ,bord )
				worksheet.write(x,11,line[15] if line[15] else '' ,bord )
				worksheet.write(x,12,line[16] if line[16] else '' ,bord )
				worksheet.write(x,13,line[17] if line[17] else '' ,bord )
				worksheet.write(x,14,line[19] if line[19] else '' ,bord )
				worksheet.write(x,15,line[20] if line[20] else '' ,bord )
				worksheet.write(x,16,line[21] if line[21] else '' ,bord )
				worksheet.write(x,17,line[22] if line[22] else '' ,bord )

				ingreso1 += line[5] if line[5] else 0
				ingreso2 +=line[6] if line[6] else 0
				salida1 +=line[7] if line[7] else 0
				salida2 += line[8] if line[8] else 0

				x = x +1

			tam_col = [11,11,5,5,7,5,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11]

			worksheet.write(x,5,'TOTALES:' ,bold )
			worksheet.write(x,6,ingreso1 ,numberdosbold )
			#worksheet.write(x,7,ingreso2 ,numberdosbold )
			worksheet.write(x,7,salida1 ,numberdosbold )
			#worksheet.write(x,9,salida2 ,numberdosbold )

			worksheet.set_column('A:A', tam_col[0])
			worksheet.set_column('B:B', tam_col[1])
			worksheet.set_column('C:C', tam_col[2])
			worksheet.set_column('D:D', tam_col[3])
			worksheet.set_column('E:E', tam_col[4])
			worksheet.set_column('F:F', tam_col[5])
			worksheet.set_column('G:G', tam_col[6])
			worksheet.set_column('H:H', tam_col[7])
			worksheet.set_column('I:I', tam_col[8])
			worksheet.set_column('J:J', tam_col[9])
			worksheet.set_column('K:K', tam_col[10])
			worksheet.set_column('L:L', tam_col[11])
			worksheet.set_column('M:M', tam_col[12])
			worksheet.set_column('N:N', tam_col[13])
			worksheet.set_column('O:O', tam_col[14])
			worksheet.set_column('P:P', tam_col[15])
			worksheet.set_column('Q:Q', tam_col[16])
			worksheet.set_column('R:R', tam_col[17])
			worksheet.set_column('S:S', tam_col[18])
			worksheet.set_column('T:Z', tam_col[19])

			workbook.close()
			
			f = open(direccion + 'kardex_producto.xlsx', 'rb')
			
			
			sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
			vals = {
				'output_name': 'Kardex.xlsx',
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

			#import os
			#os.system('c:\\eSpeak2\\command_line\\espeak.exe -ves-f1 -s 170 -p 100 "Se Realizo La exportación exitosamente Y A EDWARD NO LE GUSTA XDXDXDXDDDDDDDDDDDD" ')

			return {
			    "type": "ir.actions.act_window",
			    "res_model": "export.file.save",
			    "views": [[False, "form"]],
			    "res_id": sfs_id.id,
			    "target": "new",
			}

			#raise osv.except_osv('Alerta','Solo Kardex Valorado tiene formato excel')


	@api.v7
	def do_csv(self,cr,uid,ids,context=None):
		data = self.read(cr, uid, ids, [], context=context)[0]	
		cad=""	

		lst_products  = data['products_ids']
		lst_locations = data['location_ids']
		productos='{'
		almacenes='{'
		date_ini=data['fini']
		date_fin=data['ffin']
		if 'allproducts' in data:
			if data['allproducts']:
				lst_products  = self.pool.get('product.product').search(cr,uid,[])
			else:
				lst_products  = data['products_ids']
		else:
			if data['products_ids']==[]:
				raise osv.except_osv('Alerta','No existen productos seleccionados')
				return
			lst_products  = data['products_ids']


		for producto in lst_products:
			productos=productos+str(producto)+','
		productos=productos[:-1]+'}'
		for location in lst_locations:
			almacenes=almacenes+str(location)+','
		almacenes=almacenes[:-1]+'}'
		# raise osv.except_osv('Alertafis',[almacenes,productos])
		print 'tipo',context['tipo']
		if context['tipo']=='valorado':
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
				fecha_albaran as "Fecha Alb.",
				fecha as "Fecha",
				periodo as "Periodo",
				ctanalitica as "Cta. Analitica",
				stock_doc as "Doc. Almacén",
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
				pedido_compra as "Pedido de Compra",
				licitacion as "Licitacion"
				from get_kardex_v("""+date_ini.replace("-","") + "," + date_fin.replace("-","") + ",'" + productos + """'::INT[], '""" + almacenes + """'::INT[]) order by location_id,product_id,fecha,esingreso,nro) to 'e:/PLES_ODOO/kardex.csv'  WITH DELIMITER ',' CSV HEADER 
				"""
		else:
			if context['tipo']=='fisico':
				cadf="""
				copy (select 
					origen as "Origen",
					destino as "Destino",
				almacen AS "Almacen",
				categoria as "Categoria",
				name_template as "Producto",
				fecha_albaran as "Fecha Alb.",
				fecha as "Fecha",
				periodo as "Periodo",
				ctanalitica as "Cta. Analitica",
				account_analytic_account.name as "C. Costo",				
				stock_doc as "Doc. Almacén",
				serial as "Serie",
				nro as "Nro. Documento",
				operation_type as "Tipo de operacion",
				get_kardex_v.name as "Proveedor",
				ingreso as "Ingreso Fisico",
				salida as "Salida Fisico",
				saldof as "Saldo Fisico",
				default_code as "Codigo",unidad as "Unidad",
				mrpname as "Ord. Prodc.",
				documento_partner as "Guia de remision",
				responsable as "Entregado a",
				pedido_compra as "Pedido de Compra",
				licitacion as "Licitacion"
				from get_kardex_v("""+date_ini.replace("-","") + "," + date_fin.replace("-","") + ",'" + productos + """'::INT[], '""" + almacenes + """'::INT[]) 
				left join account_analytic_account on get_kardex_v.ctanalitica =account_analytic_account.code
				order by location_id,product_id,fecha,esingreso,nro) to 'e:/PLES_ODOO/kardex.csv'  WITH DELIMITER ',' CSV HEADER 
				"""
			else:
				cadf="select * from get_kardex_fis_sumi("+date_ini.replace("-","") + "," + date_fin.replace("-","") + ",'" + productos + "'::INT[], '" + almacenes + "'::INT[]) order by location_id,product_id,fecha,esingreso,nro"							
		# raise osv.except_osv('Alertafis',cadf)

		cr.execute(cadf)
		

		f = open('e:/PLES_ODOO/kardex.csv', 'rb')
			
			
		sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
		vals = {
			'output_name': 'kardex.csv',
			'output_file': base64.encodestring(''.join(f.readlines())),		
		}

		mod_obj = self.pool.get('ir.model.data')
		act_obj = self.pool.get('ir.actions.act_window')
		sfs_id = self.pool.get('export.file.save').create(cr,uid,vals)
		result = {}
		view_ref = mod_obj.get_object_reference(cr,uid,'account_contable_book_it', 'export_file_save_action')
		view_id = view_ref and view_ref[1] or False
		result = act_obj.read( cr,uid,[view_id],context )
		print sfs_id

		#import os
		#os.system('c:\\eSpeak2\\command_line\\espeak.exe -ves-f1 -s 170 -p 100 "Se Realizo La exportación exitosamente Y A EDWARD NO LE GUSTA XDXDXDXDDDDDDDDDDDD" ')

		return {
		    "type": "ir.actions.act_window",
		    "res_model": "export.file.save",
		    "views": [[False, "form"]],
		    "res_id": sfs_id,
		    "target": "new",
		}

	@api.v7
	def do_excel(self,cr,uid,ids,context={},imprimir=False,listar2=False):
		data = self.read(cr, uid, ids, [], context=context)[0]	
		cad=""	
		if data['products_ids']==[]:
			raise osv.except_osv('Alerta','No existen productos seleccionados')
			return
		lst_products  = data['products_ids']
		lst_locations = data['location_ids']
		productos='{'
		almacenes='{'
		date_ini=data['fini']
		date_fin=data['ffin']
		for producto in lst_products:
			productos=productos+str(producto)+','
		productos=productos[:-1]+'}'
		for location in lst_locations:
			almacenes=almacenes+str(location)+','
		almacenes=almacenes[:-1]+'}'
		# raise osv.except_osv('Alertafis',[almacenes,productos])
		print 'tipo',context['tipo']
		if context['tipo']=='valorado':
			cadf="select * from get_kardex_v("+date_ini.replace("-","") + "," + date_fin.replace("-","") + ",'" + productos + "'::INT[], '" + almacenes + "'::INT[]) order by location_id,product_id,fecha,esingreso,nro"
		else:
			if context['tipo']=='fisico':
				cadf="select * from get_kardex_fis("+date_ini.replace("-","") + "," + date_fin.replace("-","") + ",'" + productos + "'::INT[], '" + almacenes + "'::INT[]) order by location_id,product_id,fecha,esingreso,nro"
			else:
				cadf="select * from get_kardex_fis_sumi("+date_ini.replace("-","") + "," + date_fin.replace("-","") + ",'" + productos + "'::INT[], '" + almacenes + "'::INT[]) order by location_id,product_id,fecha,esingreso,nro"							
		# raise osv.except_osv('Alertafis',cadf)
		cr.execute(cadf)
		ds = cr.dictfetchall()
		if context['tipo']!='valorado':
			ds = self.makevalues(cr,uid,ds,lst_products,lst_locations,context)


		filtro = []
		currency = False
		type_show='excel'	
		if type_show == 'excel':
			import io
			from xlsxwriter.workbook import Workbook
			output = io.BytesIO()

			direccionid = self.pool.get('main.parameter').search(cr,uid,[])[0]
			direccion=self.pool.get('main.parameter').browse(cr,uid,direccionid,context).dir_create_file


			workbook = Workbook(direccion+'planillaprueba.xlsx')
				# '/home/Odoo/planillaprueba.xlsx')
			worksheet = workbook.add_worksheet("Kardex")
			bold = workbook.add_format({'bold': True})
			normal = workbook.add_format()
			boldbord = workbook.add_format({'bold': True})
			boldbord.set_border(style=2)
			boldbord.set_align('center')
			boldbord.set_align('vcenter')
			boldbord.set_text_wrap()
			boldbord.set_font_size(9)
			boldbord.set_bg_color('#DCE6F1')
			numbertres = workbook.add_format({'num_format':'0.000'})
			numberseis = workbook.add_format({'num_format':'0.000000'})
			numberdos = workbook.add_format({'num_format':'0.00'})
			bord = workbook.add_format()
			bord.set_border(style=1)
			# numberdos.set_border(style=1)
			numbertres.set_border(style=1)			
			x= 4				
			tam_col = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23]
			tam_letra = 1.2
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')
			import datetime
			tam_col[0] = 20
			tam_col[1] = 20
			tam_col[2] = 20
			tam_col[3] = 10
			tam_col[4] = 10
			tam_col[5] = 10
			tam_col[6] = 10
			tam_col[7] = 15
			tam_col[8] = 10
			tam_col[9] = 10
			tam_col[10] = 10
			tam_col[11] = 12
			tam_col[12] = 10
			tam_col[13] = 10
			tam_col[14] = 20
			tam_col[15] = 10
			tam_col[16] = 10
			tam_col[17] = 10
			tam_col[18] = 10
			tam_col[19] = 10
			tam_col[20] = 10
			tam_col[21] = 10
			tam_col[22] = 10

			n=0
			x=0
			worksheet.write(0,2,'KARDEX',bold)
			cadper='DEL '+date_ini+ ' AL ' +date_fin
			worksheet.write(2,2,cadper,bold)
			x=3
			worksheet.write(x,0,'Ubicac.',bold)
			worksheet.write(x,1,'Categ.',bold)
			worksheet.write(x,2,'Producto',bold)
			worksheet.write(x,3,'Cta. Producto',bold)
			worksheet.write(x,4,'Fecha',bold)	
			worksheet.write(x,5,'Periodo',bold)
			worksheet.write(x,6,'Cta. Costo',bold)
			worksheet.write(x,7,'Cta. Analitica',bold)
			worksheet.write(x,8,'Tipo',bold)
			worksheet.write(x,9,'Serie',bold)
			worksheet.write(x,10,'Nro.',bold)
			worksheet.write(x,11,'Cta. Factura',bold)
			worksheet.write(x,12,'Tipo de operac.',bold)
			worksheet.write(x,13,'Raz. social',bold)
			worksheet.write(x,14,'Ingresos',bold)
			worksheet.write(x,15,'Egresos',bold)
			worksheet.write(x,16,'Saldo',bold)
			worksheet.write(x,17,'C. Adqui.',bold)
			worksheet.write(x,18,'Debe',bold)
			worksheet.write(x,19,'Haber',bold)
			worksheet.write(x,20,'Saldo',bold)
			worksheet.write(x,21,'C. Prom.',bold)
			x=5
			n=0
			tingreso =0
			tsalida=0
			tdebe=0
			thaber=0
			for line in ds:
				worksheet.write(x,0, line['almacen'] if line['almacen']  else '',numberdos)
				worksheet.write(x,1, line['categoria']  if line['categoria'] else '',numberdos)
				worksheet.write(x,2, line['name_template'] if line['name_template'] else '',numberdos)
				worksheet.write(x,3, line['product_account'] if 'product_account' in line else '' ,numberdos)
				worksheet.write(x,4, line['fecha'] if line['fecha'] else '',numberdos)
				worksheet.write(x,5, line['periodo'] if line['periodo'] else '',numberdos)
				worksheet.write(x,6, line['cost_account'] if line['cost_account'] else '',numberdos)
				worksheet.write(x,7, line['ctanalitica'] if line['ctanalitica'] else '',numberdos)
				worksheet.write(x,8, line['doc_type_ope'] if line['doc_type_ope'] else '',numberdos)
				worksheet.write(x,9, line['serial'] if line['serial'] else '',numberdos)
				worksheet.write(x,10, line['nro'] if line['nro'] else '',numberdos)
				worksheet.write(x,11, line['account_invoice'] if 'account_invoice' in line else '' ,numberdos)
				worksheet.write(x,12, line['operation_type'] if  line['operation_type'] else '',numberdos)
				worksheet.write(x,13, line['name'] if line['name'] else '',numberdos)
				worksheet.write(x,14, line['ingreso'] if line['ingreso'] else '',numberdos)
				worksheet.write(x,15, line['salida'] if line['salida'] else '',numberdos)
				worksheet.write(x,16, line['saldof'] if line['saldof'] else '',numberdos)
				worksheet.write(x,17, line['cadquiere'] if line['cadquiere'] else '',numberdos)
				worksheet.write(x,18, line['debit'] if line['debit'] else '',numberdos)
				worksheet.write(x,19, line['credit'] if line['credit'] else '',numberdos)
				worksheet.write(x,20, line['saldov'] if line['saldov'] else '',numberdos)
				worksheet.write(x,21, line['cprom'] if line['cprom'] else '',numberseis)
				tingreso =tingreso+line['ingreso'] if line['ingreso'] else tingreso
				tsalida=tsalida+line['salida'] if line['salida'] else tsalida
				tdebe=tdebe+line['debit'] if line['debit'] else tdebe
				thaber=thaber+line['credit'] if line['credit'] else thaber
				x=x+1
			# worksheet.set_column('A:A', tam_col[0])
			worksheet.write(x,14, tingreso,numberdos)
			worksheet.write(x,15, tsalida,numberdos)
			worksheet.write(x,18, tdebe,numberdos)
			worksheet.write(x,19, thaber,numberdos)

			worksheet.set_column('A:A', tam_col[0])
			worksheet.set_column('B:B', tam_col[1])
			worksheet.set_column('C:C', tam_col[2])
			worksheet.set_column('D:D', tam_col[3])
			worksheet.set_column('E:E', tam_col[4])
			worksheet.set_column('F:F', tam_col[5])
			worksheet.set_column('G:G', tam_col[6])
			worksheet.set_column('H:H', tam_col[7])
			worksheet.set_column('I:I', tam_col[8])
			worksheet.set_column('J:J', tam_col[9])
			worksheet.set_column('K:K', tam_col[10])
			worksheet.set_column('L:L', tam_col[11])
			worksheet.set_column('M:M', tam_col[12])
			worksheet.set_column('N:N', tam_col[13])
			worksheet.set_column('O:O', tam_col[14])
			worksheet.set_column('P:P', tam_col[15])
			worksheet.set_column('Q:Q', tam_col[16])
			worksheet.set_column('R:R', tam_col[17])
			worksheet.set_column('S:S', tam_col[18])
			worksheet.set_column('T:T', tam_col[19])
			worksheet.set_column('U:U', tam_col[20])
			worksheet.set_column('V:V', tam_col[21])



			workbook.close()
			
			f = open(direccion + 'planillaprueba.xlsx', 'rb')
			
			
			sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
			vals = {
				'output_name': 'kardex.xlsx',
				'output_file': base64.encodestring(''.join(f.readlines())),		
			}

			mod_obj = self.pool.get('ir.model.data')
			act_obj = self.pool.get('ir.actions.act_window')
			sfs_id = self.pool.get('export.file.save').create(cr,uid,vals)
			result = {}
			view_ref = mod_obj.get_object_reference(cr,uid,'account_contable_book_it', 'export_file_save_action')
			view_id = view_ref and view_ref[1] or False
			result = act_obj.read( cr,uid,[view_id],context )
			print sfs_id

			#import os
			#os.system('c:\\eSpeak2\\command_line\\espeak.exe -ves-f1 -s 170 -p 100 "Se Realizo La exportación exitosamente Y A EDWARD NO LE GUSTA XDXDXDXDDDDDDDDDDDD" ')

			return {
			    "type": "ir.actions.act_window",
			    "res_model": "export.file.save",
			    "views": [[False, "form"]],
			    "res_id": sfs_id,
			    "target": "new",
			}

		
		
		
	def isfloat(self,value):
		try:
			float(value)
			return True
		except:
			return False
	def makevalues(self,cr,uid,ds,products,locations,context):
		for location in locations:
			for product in products:
				nsaldof = 0
				nsaldov = 0
				cprom = 0
				cadquiere = 0
				ingreso = 0
				salida = 0
				debit = 0
				credit = 0
				for dr in ds:
					if str(dr['location_id'])==str(location) and str(dr["product_id"])==str(product):
						if self.isfloat(dr["ingreso"]):
							ingreso=float(dr["ingreso"]) 
						if self.isfloat(dr["salida"]):
							salida=float(dr["salida"]) 
						if self.isfloat(dr["debit"]):
							debit=float(dr["debit"]) 
						if self.isfloat(dr["credit"]):
							credit=float(dr["credit"]) 
							
						if self.isfloat(dr["cadquiere"]):
							cadquiere=float(dr["cadquiere"])
						if cadquiere <= 0:
							cadquiere = cprom

						if salida>0:
							credit = cadquiere * salida
						nsaldov = nsaldov + (debit - credit)
						nsaldof = nsaldof + (ingreso - salida)

						if nsaldof > 0:
							if ingreso > 0:
								cprom = nsaldov / nsaldof
								cadquiere = debit / ingreso
							else:
								if salida == 0:
									if debit + credit > 0:
										cprom = nsaldov / nsaldof
								else:
									credit = salida * cprom
						else:
							cprom = 0
						

						if nsaldov <= 0 and nsaldof <= 0:
							dr["cprom"] = 0
							cprom = 0

						dr["cprom"] = cprom
						dr["cadquiere"] = cadquiere
						dr["credit"] = credit
						dr["saldof"] = nsaldof
						dr["saldov"] = nsaldov				

		return ds
	def get_saldo_ant(self,cr,uid,period_id,location_id,product_id,context=None):
		n=0	
		cad = "select * from account_period where special=true"
		cr.execute(cad)
		f=cr.dictfetchall()
		periodo=self.pool.get('account.period').browse(cr,uid,period_id,context)
		for l in f:
			if periodo.date_start ==l['date_start']:
				if l['special']:
					return 0
		lst=self.pool.get('period.kardex').search(cr,uid,[
			('period_id','=',period_id),
			('location_id','in',location_id),
			('product_id','=',product_id),
			])
		
		if lst!=[]:
			ps=self.pool.get('period.kardex').browse(cr,uid,lst,context)[0]
			n=ps.saldo
			# for dc in self.pool.get('period.kardex').browse(cr,uid,lst,context):
		# raise osv.except_osv('Alertafis',period_id)
		return n
make_kardex()