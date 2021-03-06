# -*- coding: utf-8 -*-

from openerp import models, fields, api
import base64
from openerp.osv import osv

from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import magenta, red , black , blue, gray, Color, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Table
from reportlab.lib.units import  cm,mm
from reportlab.lib.utils import simpleSplit
import decimal

class account_asset_category(models.Model):
	_inherit='account.asset.category'

	account_analytics_id = fields.Many2one('account.analytic.plan.instance',string='Distribución Analítica')
	year_depreciacion = fields.Float('Años de depreciaciones',digits=(12,2))
	percent_depreciacion = fields.Float('Tasa de Depreciación (%)',digits=(12,2))
	account_retire = fields.Many2one('account.account','Cuenta Retiro')

	_defaults = {
		'method_period': 1,
		'method_number': 0,
		'percent_depreciacion':0,
	}
	
	@api.model
	def create(self,vals):
		asset_id = super(account_asset_category, self).create( vals)
		asset_id.year_depreciacion = float(asset_id.method_number)/12.0
		if asset_id.method_number == 0:
			asset_id.percent_depreciacion = 0
		else:	
			asset_id.percent_depreciacion = 100.0 / (float(asset_id.method_number)/12.0)
		return asset_id

	@api.one
	def write(self,vals):
		if not vals:
			vals={}
		m_n = None
		if 'percent_depreciacion' in vals:
			m_n = vals['percent_depreciacion']
		else:
			m_n = self.percent_depreciacion
		if m_n != 0:
			vals['year_depreciacion'] = 100/m_n
		else:
			vals['year_depreciacion'] = 0
		vals['method_number'] = vals['year_depreciacion']*12
		asset_id = super(account_asset_category, self).write(vals)
		return asset_id

	@api.onchange('percent_depreciacion')
	def onchange_percent_depreciacion(self):
		if self.percent_depreciacion:
			t = 100/self.percent_depreciacion if self.percent_depreciacion != 0 else 0
			self.year_depreciacion = t
			self.method_number = t*12


class account_invoice(models.Model):
	_inherit = 'account.invoice'

	@api.multi
	def action_cancel(self):
		for obj in self:
			t = self.env['account.asset.asset'].search([('invoice_id','=',obj.id)])
			for i in t:
				for j in i.depreciation_line_ids:
					j.unlink()
				i.unlink()
		return super(account_invoice,self).action_cancel()


class account_asset_retire(models.TransientModel):
	_name = 'account.asset.retire'

	date = fields.Date('Fecha de Baja',required="1")
	journal_id = fields.Many2one('account.journal','Diario',required="1")

	@api.multi
	def do_rebuild(self):
		mes = int(self.date[5:7] )
		ano = int(self.date[:4] )

		mes =  12 if mes == 0 else mes -1
		ano = ano -1 if mes == 12 else ano

		txt_period = ( '0' + str(mes) if mes <10 else str(mes) )  + '/' +  str(ano)

		obj_asset = self.env['account.asset.asset'].search([('id','=',self._context['id_nosequien'])])

		lineas_asset = self.env['account.asset.depreciation.line'].search([('asset_id','=',obj_asset.id),('period_id','=',txt_period)])
		a = b = None
		if lineas_asset:
			a= obj_asset.purchase_value - lineas_asset.depreciation_acum
			b= lineas_asset.depreciation_acum
			
		else:
			a= obj_asset.purchase_value
			b= 0
			
		obj_asset.valor_retiro= a
		obj_asset.depreciacion_retiro= b
		obj_asset.f_baja= self.date
		obj_asset.state= 'baja'

		total_a_hijo= 0
		total_b_hijo= 0
		for hijo in self.env['account.asset.asset'].search([('parent_id','=',obj_asset.id)]):
			
			lineas_asset_hijo = self.env['account.asset.depreciation.line'].search([('asset_id','=',hijo.id),('period_id','=',txt_period)])
			a_hijo = b_hijo = None
			if lineas_asset_hijo:
				a_hijo= hijo.purchase_value - lineas_asset_hijo.depreciation_acum
				b_hijo= lineas_asset_hijo.depreciation_acum
				
			else:
				a_hijo= hijo.purchase_value
				b_hijo= 0
				
			hijo.valor_retiro= a_hijo
			hijo.depreciacion_retiro= b_hijo
			hijo.f_baja= self.date
			hijo.state= 'baja'
			total_a_hijo += a_hijo
			total_b_hijo += b_hijo


		period = self.env['account.period'].search([('code','=',self.date[5:7] + '/' + self.date[:4] )])

		if not obj_asset.category_id.account_retire.id:
			raise osv.except_osv('Alerta!', "No esta configurada la cuenta de Retiro en la categoria.")

		l1 = {
			'name': 'Valor de Retiro',
			'debit': a + total_a_hijo,
			'credit': 0,
			'account_id': obj_asset.category_id.account_retire.id,
			'ref': 'Valor de Retiro',
			'analytic_account_id':obj_asset.category_id.account_analytic_id.id,
			'analytics_id':obj_asset.category_id.account_analytics_id.id,
			'date': self.date,
		}

		l2 = {
			'name': 'Valor de Depreciación',
			'debit': b + total_b_hijo,
			'credit': 0,
			'account_id': obj_asset.category_id.account_depreciation_id.id,
			'ref': 'Valor de Depreciación',
			'date': self.date,
		}

		l3 = {
			'name': 'Valor de Activo',
			'debit': 0,
			'credit': a + b + total_a_hijo + total_b_hijo,
			'account_id': obj_asset.category_id.account_asset_id.id,
			'ref': 'Valor de Activo',
			'date': self.date,
		}

		data = {
			'ref': 'Retiro Activo',
			'line_id': [(0, 0, l3), (0, 0, l2),(0, 0, l1)],
			'journal_id': self.journal_id.id,
			'period_id': period.id,
			'date': self.date,
		}

		move_obj = self.env['account.move'].create(data)

		if move_obj.state=='draft':
			move_obj.button_validate()

		obj_asset.asiento_id = move_obj
		for hijo in self.env['account.asset.asset'].search([('parent_id','=',obj_asset.id)]):
			hijo.asiento_id= move_obj
		return True



class account_asset_asset(models.Model):
	_inherit='account.asset.asset'

	state = fields.Selection([('draft','Draft'),('open','Running'),('close','Close'),('baja','De Baja')], 'Status', required=True, copy=False,
                                  help="When an asset is created, the status is 'Draft'.\n" \
                                       "If the asset is confirmed, the status goes in 'Running' and the depreciation lines can be posted in the accounting.\n" \
                                       "You can manually close an asset when the depreciation is over. If the last line of depreciation is posted, the asset automatically goes in that status.")

	codigo = fields.Char('Codigo',size=50)
	date_start = fields.Date('Fecha Inicio')
	tipo  = fields.Selection([('adquisicion', 'Adquisiciones'),('mejoras', 'Mejoras'),('otros', 'Otros Ajustes')], 'Tipo')

	ubicacion = fields.Char('Ubicación',size=100)
	marca = fields.Char('Marca',size=100)
	modelo = fields.Char('Modelo',size=100)
	serie = fields.Char('Serie y/o Placa',size=100)

	cta_activo = fields.Many2one('account.account',string="Cuenta Activo", related="category_id.account_asset_id",store=True)
	f_baja = fields.Date('Fecha de Baja')

	invoice_id = fields.Many2one('account.invoice',string="Factura")
	asiento_id = fields.Many2one('account.move',string="Asiento de Baja")

	movimientos = fields.One2many('account.asset.asset','parent_id',string='Movimientos')

	valor_retiro = fields.Float('Valor de Retiro',digits=(12,2))
	depreciacion_retiro = fields.Float('Depreciación del Retiro',digits=(12,2))
	autorizacion_depreciacion = fields.Char('Autorización para la Depreciación',size=100)

	f_contra = fields.Date('Fecha del Contrato')
	num_contra = fields.Char('Nro. Contrato Arrendamiento Financiero',size=100)
	f_ini_arren = fields.Date('Fecha de Inicio del Contrato Arrendamiento')
	num_cuotas = fields.Integer('Nro Cuotas Pactadas')
	monto_contra = fields.Float('Monto Total Contrato De Arrendamiento', digits=(12,2))



	@api.multi
	def calculate_hijos(self):
		if self.parent_id.id:
			self.id_grupo_asset = self.parent_id.id
		else:
			self.id_grupo_asset = self.id

	id_grupo_asset = fields.Many2one('account.asset.asset','Padre',store=True, compute="calculate_hijos")

	_defaults ={
		'tipo': 'adquisicion',
	}

	@api.multi
	def button_retire(self):
		data = {
				'context': {'id_nosequien':self[0].id},
				'name': 'Dar de Baja',
				'view_type': 'form',
				'view_mode': 'form',
				'res_model': 'account.asset.retire',
				'target': 'new',
				'view_id': False,
				'type': 'ir.actions.act_window',
			}
		return data

	@api.multi
	def button_cancel_retire(self):
		self.valor_retiro= 0
		self.depreciacion_retiro = 0
		self.f_baja = False
		self.state= 'draft'


	@api.one
	def count_invoices(self):
		self.invoice_count = 1 if self.invoice_id.id else 0



	@api.one
	def count_asientos(self):
		self.asiento_count = 1 if self.asiento_id.id else 0

	invoice_count = fields.Integer('Facturas:', compute="count_invoices")
	asiento_count = fields.Integer('Asiento de Baja:', compute="count_asientos")

	@api.model
	def create(self, vals):
		asset_id = super(account_asset_asset, self).create( vals )
		asset_id.compute_depreciation_board_modify_it()
		return asset_id

	def compute_depreciation_board(self, cr, uid, ids, context=None):
		return True

	@api.onchange('purchase_date')
	def onchange_purchase_date(self):
		if self.purchase_date:			
			year = int(str(self.purchase_date)[:4])
			mounth = int(str(self.purchase_date)[5:7]) +1
			day = int(str(self.purchase_date)[8:10])
			if mounth == 13:
				year +=1
				mounth= 1
			self.date_start = str(year) + '-' + ( str( mounth )if mounth>9 else ('0'+ str(mounth) )  ) + '-' + '01'


	@api.multi
	def open_invoice(self):
		if self.invoice_id.id:
			return {
				'name': 'Factura',
				'view_type': 'form',
				'view_mode': 'form',
				'res_model': 'account.invoice',
				'res_id': self.invoice_id.id,
				'view_id': False,
				'type': 'ir.actions.act_window',
			}
		return True

	@api.multi
	def open_asiento(self):
		if self.asiento_id.id:
			return {
				'name': 'Asiento Baja',
				'view_type': 'form',
				'view_mode': 'form',
				'res_model': 'account.move',
				'res_id': self.asiento_id.id,
				'view_id': False,
				'type': 'ir.actions.act_window',
			}
		return True

	@api.one
	def compute_depreciation_board_modify_it(self):

		for i in self.depreciation_line_ids:
			if not i.move_id.id:
				i.unlink()

		if self.category_id.method_number != 0:
				
			cantidad = float(self.value_residual) / float(self.category_id.method_number)
			cantidad = float( "%0.2f"% cantidad)
			monto_var = self.purchase_value
			fecha_partida = self.date_start
			print fecha_partida
			year = int(str(self.date_start)[:4])
			mounth = int(str(self.date_start)[5:7]) -1
			day = int(str(self.date_start)[8:10])
			acum = 0
			for i in range(1,self.category_id.method_number+1):
				t = self.env['account.asset.depreciation.line'].search([('asset_id', '=', self.id),('mes','=',i)])

				mounth +=1
				if mounth == 13:
					mounth= 1
					year +=1

				acum += cantidad

				if len(t)==0:
					vals = {}
					if i != self.category_id.method_number:
						vals = {
							 'asset_id': self.id,
							 'sequence': i,
							 'name': str(self.id) +'/' + str(i),
							 'mes': i,
							 'depreciation_date': str(year) + '-' + ( ('0'+str(mounth)) if mounth<10 else str(mounth)  ) + '-' +  ( ('0'+str(day)) if day<10 else str(day) ),
							 'period_id': ( ('0'+str(mounth)) if mounth<10 else str(mounth)  ) + '/' + str(year),
							 'amount': monto_var,
							 'depreciated_value': cantidad,
							 'remaining_value': monto_var-cantidad,
							 'depreciation_acum': acum,
						}
					else:
						vals = {
							 'asset_id': self.id,
							 'sequence': i,
							 'name': str(self.id) +'/' + str(i),
							 'mes': i,
							 'depreciation_date': str(year) + '-' + ( ('0'+str(mounth)) if mounth<10 else str(mounth)  ) + '-' +  ( ('0'+str(day)) if day<10 else str(day) ),
							 'period_id': ( ('0'+str(mounth)) if mounth<10 else str(mounth)  ) + '/' + str(year),
							 'amount': monto_var,
							 'depreciated_value': float("%0.2f"%(monto_var-self.salvage_value) ),
							 'remaining_value': float("%0.2f"% (monto_var- (float("%0.2f"%(monto_var-self.salvage_value) )) )),
							 'depreciation_acum': self.value_residual,
						}

					self.env['account.asset.depreciation.line'].create(vals)

				monto_var -= cantidad

		return True


class account_invoice_line(models.Model):

	_inherit = 'account.invoice.line'
	

	@api.onchange('asset_category_id')
	def onchange_asset_category(self):
		if self.asset_category_id.id:
			if self.asset_category_id.account_asset_id.id:
				self.account_id = self.asset_category_id.account_asset_id.id

	def asset_create(self, cr, uid, lines, context=None):
		context = context or {}
		asset_obj = self.pool.get('account.asset.asset')
		for line in lines:
			if line.asset_category_id:
				fecha_inicio = line.invoice_id.date_invoice
				date_inicio = fecha_inicio
				if fecha_inicio:
					year = int(str(fecha_inicio)[:4])
					mounth = int(str(fecha_inicio)[5:7]) +1
					day = int(str(fecha_inicio)[8:10])
					if mounth == 13:
						year +=1
						mounth= 1
					date_inicio = str(year) + '-' + ( str( mounth )if mounth>9 else ('0'+ str(mounth) )  ) + '-01'
				company_list = self.pool.get('res.company').search(cr,uid,[])
				currency_company = self.pool.get('res.company').browse(cr,uid,company_list)[0].currency_id.id
				vals = {
					'name': line.name,
					'code': line.invoice_id.supplier_invoice_number or line.invoice_id.number or False,
					'invoice_id': line.invoice_id.id,
					'category_id': line.asset_category_id.id,
					'purchase_value': line.price_subtotal * line.invoice_id.currency_rate_auto if line.invoice_id.currency_id.name != 'PEN' else line.price_subtotal,
					'period_id': line.invoice_id.period_id.id,
					'partner_id': line.invoice_id.partner_id.id,
					'company_id': line.invoice_id.company_id.id,
					'currency_id': currency_company,
					'purchase_date' : line.invoice_id.date_invoice,
					'date_start' : date_inicio,
				}
				changed_vals = asset_obj.onchange_category_id(cr, uid, [], vals['category_id'], context=context)
				vals.update(changed_vals['value'])
				asset_id = asset_obj.create(cr, uid, vals, context=context)
				if line.asset_category_id.open_asset:
					asset_obj.validate(cr, uid, [asset_id], context=context)
		return True




class account_asset_depreciation_line(models.Model):
	_inherit = 'account.asset.depreciation.line'

	mes = fields.Integer('Mes')
	depreciation_acum = fields.Float('Depreciación Acumulada',digits=(12,2))
	period_id = fields.Char('Periodo',size=100)

	_defaults={
		'name':'Manual',
	}
	_order= 'mes'



class account_asset_analisis_depreciacion(models.Model):
	_name = 'account.asset.analisis.depreciacion'
	_auto = False

	activofijo = fields.Char('Activo Fijo',size=100)
	mes = fields.Integer('Mes')
	periodo = fields.Char('Periodo',size=100)
	depreciacion = fields.Float('Depreciación',digits=(12,2))
	categoria = fields.Char('Categoría',size=100)
	cta_gasto = fields.Char('Cta. Gasto',size=100)
	cta_depre = fields.Char('Cta. Depreciación',size=100)
	cta_analitica = fields.Char('Cta. Analítica',size=100)
	distrib_analitica = fields.Char('Dist. Analítica',size=100)
	asentado = fields.Boolean('Asentado')
	aadl_id = fields.Integer('ID Aadl')



	def init(self,cr):
		cr.execute(""" 
			DROP VIEW IF EXISTS account_asset_analisis_depreciacion;
			create or replace view account_asset_analisis_depreciacion as (

			SELECT row_number() OVER () AS id,* from (
			select aaa.name as activofijo,aadl.mes as mes,ap.name as periodo, aadl.depreciated_value as depreciacion, aac.name as categoria, aa_gasto.code as cta_gasto, aa_depreciacion.code as cta_depre, analytic_account.name as cta_analitica, aapi.name as distrib_analitica,
			CASE WHEN aadl.move_id is null THEN false ELSE True END as asentado,
			aadl.id as aadl_id
			 from account_asset_asset aaa
			inner join account_asset_depreciation_line aadl on aadl.asset_id = aaa.id
			inner join account_period ap on ap.name = aadl.period_id
			inner join account_asset_category aac on aac.id = aaa.category_id
			left join account_account aa_gasto on aa_gasto.id = aac.account_expense_depreciation_id
			left join account_account aa_depreciacion on aa_depreciacion.id = aac.account_depreciation_id
			left join account_analytic_account analytic_account on aac.account_analytic_id = analytic_account.id
			left join account_analytic_plan_instance aapi on aapi.id = aac.account_analytics_id
			where 
			( CASE WHEN aaa.f_baja is not Null THEN aaa.f_baja >= ap.date_start else True END)
			order by aaa.id, aadl.mes ) AS T

			)
			""")





class account_asset_analisis_wizard(osv.TransientModel):
	_name='account.asset.analisis.wizard'
	
	period_id = fields.Many2one('account.period','Periodo',required=True)
	

	@api.multi
	def do_rebuild(self):
		fechaini_obj = self.period_id
	
		
		move_obj=self.env['account.asset.analisis.depreciacion']
		filtro = []
		filtro.append( ('periodo','=',fechaini_obj.name) )
		
		
		lstidsmove = move_obj.search( filtro )
		
		if (len(lstidsmove) == 0):
			raise osv.except_osv('Alerta','No contiene datos.')
	
		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']

		
		
		return {
			'domain' : filtro,
			'type': 'ir.actions.act_window',
			'res_model': 'account.asset.analisis.depreciacion',
			'view_mode': 'tree',
			'view_type': 'form',
			'views': [(False, 'tree')],
		}



class account_move(models.Model):
	_inherit="account.move"

	check_depreciation_activo = fields.Boolean('Check Depreciacion')

	_defaults={
		'check_depreciation_activo': False,
	}






class account_asset_analisis_depreciacion_asiento(models.Model):
	_name = 'account.asset.analisis.depreciacion.asiento'
	_auto = False

	periodo = fields.Integer('Periodo')
	debe = fields.Float('Debe',digits=(12,2))
	haber = fields.Float('Haber',digits=(12,2))
	cta = fields.Integer('Cuenta')
	cta_analitica = fields.Integer('Cuenta Analitica')
	distrib_analitica = fields.Integer('Distrib. Analitica')
	categoria = fields.Char('Categoria',size=200)



	def init(self,cr):
		cr.execute(""" 
			DROP VIEW IF EXISTS account_asset_analisis_depreciacion_asiento;
			create or replace view account_asset_analisis_depreciacion_asiento as (

SELECT row_number() OVER () AS id,* from (
select ap.id as periodo, sum(aadl.depreciated_value) as debe, 0 as haber, aac.name as categoria, aa_gasto.id as cta, analytic_account.id as cta_analitica, aapi.id as distrib_analitica
 from account_asset_asset aaa
inner join account_asset_depreciation_line aadl on aadl.asset_id = aaa.id
inner join account_period ap on ap.name = aadl.period_id
inner join account_asset_category aac on aac.id = aaa.category_id
left join account_account aa_gasto on aa_gasto.id = aac.account_expense_depreciation_id
left join account_account aa_depreciacion on aa_depreciacion.id = aac.account_depreciation_id
left join account_analytic_account analytic_account on aac.account_analytic_id = analytic_account.id
left join account_analytic_plan_instance aapi on aapi.id = aac.account_analytics_id
where 
( CASE WHEN aaa.f_baja is not Null THEN aaa.f_baja >= ap.date_start else True END)
group by periodo,categoria,cta,cta_analitica, distrib_analitica

union all

select ap.id as periodo, 0 as debe, sum(aadl.depreciated_value) as haber, '' as categoria,  aa_depreciacion.id as cta, Null::integer as cta_analitica, Null::integer as distrib_analitica
 from account_asset_asset aaa
inner join account_asset_depreciation_line aadl on aadl.asset_id = aaa.id
inner join account_period ap on ap.name = aadl.period_id
inner join account_asset_category aac on aac.id = aaa.category_id
left join account_account aa_gasto on aa_gasto.id = aac.account_expense_depreciation_id
left join account_account aa_depreciacion on aa_depreciacion.id = aac.account_depreciation_id
left join account_analytic_account analytic_account on aac.account_analytic_id = analytic_account.id
left join account_analytic_plan_instance aapi on aapi.id = aac.account_analytics_id
where 
( CASE WHEN aaa.f_baja is not Null THEN aaa.f_baja >= ap.date_start else True END)
group by periodo,cta,cta_analitica, distrib_analitica

order by periodo,debe,haber ) AS T

			)
			""")




class account_asset_leasing(models.Model):
	_name = 'account.asset.leasing'
	_auto = False

	asset_name = fields.Char('Activo')
	category_name = fields.Char('Categoria')
	f_contra = fields.Date('Fecha del Contrato')
	num_contra = fields.Char('Nro. Contrato Arrenamiento Financiero',size=100)
	f_ini_arren = fields.Date('Fecha de Inicio del Contrato Arrendamiento')
	num_cuotas = fields.Integer('Nro Cuotas Pactadas')
	monto_contra = fields.Float('Monto Total Contrato De Arrendamiento', digits=(12,2))


	def init(self,cr):
		cr.execute(""" 
			DROP VIEW IF EXISTS account_asset_leasing;
			create or replace view account_asset_leasing as (

SELECT row_number() OVER () AS id,* from (
select aaa.name as asset_name, aac.name as category_name, aaa.f_contra , aaa.num_contra, aaa.f_ini_arren, aaa.num_cuotas, aaa.monto_contra from account_asset_asset aaa
inner join account_asset_category aac on aac.id = aaa.category_id
where f_contra is not null
order by aaa.name, aac.name
 ) AS T
			)
			""")


class account_asset_analisis_asiento_wizard(osv.TransientModel):
	_name='account.asset.analisis.asiento.wizard'
	
	period_id = fields.Many2one('account.period','Periodo',required=True)
	journal_id = fields.Many2one('account.journal','Diario',required=True)
	

	@api.multi
	def do_rebuild(self):
		fechaini_obj = self.period_id
		journal_obj = self.journal_id
		
		for w in self.env['account.move'].search([('period_id','=',fechaini_obj.id),('check_depreciation_activo','=',True)]):
			if w.state=='posted':
				w.button_cancel()
			w.unlink()

		move_obj=self.env['account.asset.analisis.depreciacion.asiento']
		filtro = []
		filtro.append( ('periodo','=',fechaini_obj.id) )
		
		
		lstidsmove = move_obj.search( filtro )
		
		if (len(lstidsmove) == 0):
			raise osv.except_osv('Alerta','No contiene datos.')
	
		vals={
			'journal_id':journal_obj.id,
			'period_id':fechaini_obj.id,
			'date':fechaini_obj.date_stop,
			'check_depreciation_activo':True,
			'ref':'DEPRECIACION DE '+ fechaini_obj.code,
		}
		t_move = self.env['account.move'].create(vals)
		
		for i in lstidsmove:
			vals_line = {
				'name': 'DEPRECIACION DE '+ i.categoria + fechaini_obj.code,
				'account_id': i.cta,
				'analytic_account_id':i.cta_analitica,
				'analytics_id':i.distrib_analitica,
				'debit':i.debe,
				'credit':i.haber,
				'move_id':t_move.id,
			}
			self.env['account.move.line'].create(vals_line)


		if t_move.state=='draft':
			t_move.button_validate()

		obj_move_active = self.env['account.asset.analisis.depreciacion'].search( [('periodo','=',fechaini_obj.name)] )
		for j in obj_move_active:
			obj_real = self.env['account.asset.depreciation.line'].search([('id','=',j.aadl_id)])[0]
			obj_real.move_id = t_move.id
			obj_real.write({'move_id':t_move.id})
			
		rep = "Asiento Creado Exitosamente."
		obj_id = self.env['warning'].create({'title': 'Generar Asientos de Depreciación', 'message': rep, 'type': 'info'})

		res = {
			'name': 'Generar Asientos de Depreciación',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'warning',
			'type': 'ir.actions.act_window',
			'target': 'new',
			'res_id': obj_id.id
		}

		return res



class account_asset_formato_74(osv.TransientModel):
	_name='account.asset.formato.74'
	
	period_id = fields.Many2one('account.fiscalyear','Año fiscal',required=True)
	tipo = fields.Selection([('pdf', 'Pdf'),('excel', 'Excel')],string='Tipo', required=True)

	save_page_states = []
	@api.multi
	def do_rebuild(self):
		fechaini_obj = self.period_id.date_stop
	
		
		move_obj=self.env['account.asset.asset']
		filtro = []
		filtro.append( ('purchase_date','<=',str(fechaini_obj) ) )
		
		filtro.append( ('f_contra','!=',False ) )
		
		lstidsmove = move_obj.search( filtro )
			
		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']

		if self.tipo == 'excel':
			import io
			from xlsxwriter.workbook import Workbook
			output = io.BytesIO()
			########### PRIMERA HOJA DE LA DATA EN TABLA
			#workbook = Workbook(output, {'in_memory': True})

			direccion = self.env['main.parameter'].search([])[0].dir_create_file

			workbook = Workbook(direccion +'tempo_activo_74.xlsx')
			worksheet = workbook.add_worksheet("Activo - Formato 74")
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
			numberdos = workbook.add_format({'num_format':'0.00'})
			bord = workbook.add_format()
			bord.set_border(style=1)
			numberdos.set_border(style=1)
			numbertres.set_border(style=1)			
			x= 7				
			tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			tam_letra = 1.2
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')

			worksheet.write(0,0, 'FORMATO 7.4: "REGISTRO DE ACTIVOS FIJOS - DETALLE DE LOS ACTIVOS FIJOS BAJO LA MODALIDAD DE ARRENDAMIENTO FINANCIERO AL 31.12"', bold)



			worksheet.write(2,0, "Periodo:",bold)
			tam_col[0] = tam_letra* len("Periodo:") if tam_letra* len("Periodo:")> tam_col[0] else tam_col[0]

			worksheet.write(2,1, str(self.period_id.name), normal)
			tam_col[1] = tam_letra* len(str(self.period_id.name)) if tam_letra* len(str(self.period_id.name))> tam_col[1] else tam_col[1]
			

			company = self.env['res.company'].search([])[0]

			worksheet.write(3,0, "RUC:",bold)
			tam_col[0] = tam_letra* len("RUC:") if tam_letra* len("RUC:")> tam_col[0] else tam_col[0]

			worksheet.write(3,1, str(company.partner_id.type_number), normal)
			tam_col[1] = tam_letra* len(str(company.partner_id.type_number)) if tam_letra* len(str(company.partner_id.type_number))> tam_col[1] else tam_col[1]
			



			worksheet.write(4,0, u"Apellidos y nombres, denominación o Razón Social:",bold)
			tam_col[0] = tam_letra* len(u"Apellidos y nombres, denominación o Razón Social:") if tam_letra* len(u"Apellidos y nombres, denominación o Razón Social:")> tam_col[0] else tam_col[0]

			worksheet.write(4,1, str(company.partner_id.name), normal)
			tam_col[1] = tam_letra* len(str(company.partner_id.name)) if tam_letra* len(str(company.partner_id.name))> tam_col[1] else tam_col[1]
			

			worksheet.write(6,0, "ACTIVO FIJO",boldbord)
			tam_col[0] = tam_letra* len("ACTIVO FIJO") if tam_letra* len("ACTIVO FIJO")> tam_col[0] else tam_col[0]
			worksheet.write(6,1, "FECHA DEL CONTRATO",boldbord)
			tam_col[1] = tam_letra* len("FECHA DEL CONTRATO") if tam_letra* len("FECHA DEL CONTRATO")> tam_col[1] else tam_col[1]
			worksheet.write(6,2, "NUMERO DEL CONTRATO DE ARRENDAMIENTO",boldbord)
			tam_col[2] = tam_letra* len("NUMERO DEL CONTRATO DE ARRENDAMIENTO") if tam_letra* len("NUMERO DEL CONTRATO DE ARRENDAMIENTO")> tam_col[2] else tam_col[2]
			worksheet.write(6,3, "FECHA DE INICIO DEL CONTRATO",boldbord)
			tam_col[3] = tam_letra* len("FECHA DE INICIO DEL CONTRATO") if tam_letra* len("FECHA DE INICIO DEL CONTRATO")> tam_col[3] else tam_col[3]
			worksheet.write(6,4, u"NUMERO DE CUOTAS PACTADAS",boldbord)
			tam_col[4] = tam_letra* len(u"NUMERO DE CUOTAS PACTADAS") if tam_letra* len(u"NUMERO DE CUOTAS PACTADAS")> tam_col[4] else tam_col[4]
			worksheet.write(6,5, "MONTO DEL CONTRATO",boldbord)
			tam_col[5] = tam_letra* len("MONTO DEL CONTRATO") if tam_letra* len("MONTO DEL CONTRATO")> tam_col[5] else tam_col[5]
			


			for line in lstidsmove:
				worksheet.write(x,0,line.name if line.name else '' ,bord )
				worksheet.write(x,1,line.f_contra if line.f_contra  else '',bord )
				worksheet.write(x,2,line.num_contra if line.num_contra  else '',bord)
				worksheet.write(x,3,line.f_ini_arren if line.f_ini_arren  else '',bord)
				worksheet.write(x,4,line.num_cuotas,bord)
				worksheet.write(x,5,line.monto_contra ,numberdos)
				

				tam_col[0] = tam_letra* len(line.name if line.name else '' ) if tam_letra* len(line.name if line.name else '' )> tam_col[0] else tam_col[0]
				tam_col[1] = tam_letra* len(line.f_contra if line.f_contra  else '') if tam_letra* len(line.f_contra if line.f_contra  else '')> tam_col[1] else tam_col[1]
				tam_col[2] = tam_letra* len(line.num_contra if line.num_contra  else '') if tam_letra* len(line.num_contra if line.num_contra  else '')> tam_col[2] else tam_col[2]
				tam_col[3] = tam_letra* len(line.f_ini_arren if line.f_ini_arren  else '') if tam_letra* len(line.f_ini_arren if line.f_ini_arren  else '')> tam_col[3] else tam_col[3]
				tam_col[4] = tam_letra* len(str(line.num_cuotas) if line.num_cuotas  else '') if tam_letra* len(str(line.num_cuotas) if line.num_cuotas  else '')> tam_col[4] else tam_col[4]
				tam_col[5] = tam_letra* len("%0.2f"%line.monto_contra ) if tam_letra* len("%0.2f"%line.monto_contra )> tam_col[5] else tam_col[5]
				
				x = x +1


			tam_col = [45,19,39,26,27,22,0,0,0,0,0,0,0,0,0]
			worksheet.set_column('A:A', tam_col[0])
			worksheet.set_column('B:B', tam_col[1])
			worksheet.set_column('C:C', tam_col[2])
			worksheet.set_column('D:D', tam_col[3])
			worksheet.set_column('E:E', tam_col[4])
			worksheet.set_column('F:F', tam_col[5])
			workbook.close()
			
			f = open(direccion + 'tempo_activo_74.xlsx', 'rb')
			
			
			sfs_obj = self.pool.get('account_contable_book_it.sunat_file_save')
			vals = {
				'output_name': 'ActivoFormato7_4.xlsx',
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



		if self.tipo == 'pdf':
			self.reporteador()
			
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')
			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']
			import os

			direccion = self.env['main.parameter'].search([])[0].dir_create_file
			vals = {
				'output_name': 'ActivoFormato7_4.pdf',
				'output_file': open(direccion + "a.pdf", "rb").read().encode("base64"),	
			}
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
	def cabezera(self,c,wReal,hReal):

		c.setFont("Times-Bold", 12)
		c.setFillColor(black)

		c.setFont("Times-Bold", 9)
		c.drawCentredString((wReal/2)+20,hReal, u'FORMATO 7.4: "REGISTRO DE ACTIVOS FIJOS - DETALLE DE LOS ACTIVOS FIJOS BAJO LA MODALIDAD DE ARRENDAMIENTO FINANCIERO AL 31.12"')
		c.drawString(40,hReal-24, u"Periodo: ")

		c.setFont("Times-Roman", 9)
		c.drawString(90,hReal-24, self.period_id.name)
		c.setFont("Times-Bold", 9)
		c.drawString(40,hReal-36, u"RUC: " )

		c.setFont("Times-Roman", 9)
		c.drawString(90,hReal-36, self.env["res.company"].search([])[0].partner_id.type_number )

		c.setFont("Times-Bold", 9)

		c.drawString(40,hReal-48, u"Apellido y nombres, Denominación o Razón Social: " )
		c.setFont("Times-Roman", 9)
		c.drawString(290,hReal-48,  self.env["res.company"].search([])[0].name.upper() )

		style = getSampleStyleSheet()["Normal"]
		style.leading = 8
		style.alignment= 1
		paragraph1 = Paragraph(
			"<font size=9><b>ACTIVO FIJO</b></font>",
			style
		)
		paragraph2 = Paragraph(
			"<font size=9><b>FECHA DEL CONTRATO</b></font>",
			style
		)
		paragraph3 = Paragraph(
			"<font size=9><b>NUMERO DEL CONTRATO DE ARRENDAMIENTO</b></font>",
			style
		)
		paragraph4 = Paragraph(
			"<font size=9><b>FECHA DE INICIO DEL CONTRATO</b></font>",
			style
		)
		paragraph5 = Paragraph(
			"<font size=9><b>NUMERO DE CUOTAS PACTADAS</b></font>",
			style
		)
		paragraph6 = Paragraph(
			"<font size=9><b>MONTO DEL CONTRATO</b></font>",
			style
		)
		data= [[ paragraph1 , paragraph2 , paragraph3 ,  paragraph4,  paragraph5,paragraph6]]
		
		t=Table(data ,colWidths=(250, 90, 90, 90, 90, 120), rowHeights=(40))
		t.setStyle(TableStyle([
			('GRID',(0,0),(-1,-1), 1, colors.black),
			('ALIGN',(0,0),(-1,-1),'CENTER'),
			('VALIGN',(0,0),(-1,-1),'MIDDLE'),
			('TEXTFONT', (0, 0), (-1, -1), 'Times-Bold'),
			('FONTSIZE',(0,0),(-1,-1),2)
		]))
		t.wrapOn(c,30,500)
		t.drawOn(c,30,hReal-115)


	@api.multi
	def reporteador(self):

		import sys
		nivel_left_page = 1
		nivel_left_fila = 0
		
		nivel_right_page = 1
		nivel_right_fila = 0

		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		width , height = A4  # 595 , 842
		hReal = width- 30
		wReal = height - 40

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		c = canvas.Canvas( direccion + "a.pdf", pagesize=(height,width) )
		inicio = 0
		pos_inicial = hReal-136

		pagina = 1
		textPos = 0
		
		tamanios = {}
		voucherTamanio = None
		contTamanio = 0

		self.cabezera(c,wReal,hReal)


		c.setFont("Times-Bold", 9)
		#c.drawCentredString(421,25,'Pág. ' + str(pagina))


		#pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,16,pagina)

		fechaini_obj = self.period_id.date_stop
	
		
		move_obj=self.env['account.asset.asset']
		filtro = []
		filtro.append( ('purchase_date','<=',str(fechaini_obj) ) )
		filtro.append( ('f_contra','!=',False ) )
		
		
		lstidsmove = move_obj.search( filtro )
		total = 0
		for line in lstidsmove:
			c.setFont("Times-Roman", 9)
			c.drawString(35,pos_inicial, line.name if line.name else '')
			c.drawString(285,pos_inicial, line.f_contra if line.f_contra  else '')
			c.drawString(375,pos_inicial, line.num_contra if line.num_contra  else '')
			c.drawString(465,pos_inicial, line.f_ini_arren if line.f_ini_arren  else '')
			c.drawString(555,pos_inicial, str(line.num_cuotas) )
			c.drawRightString(645+110,pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"%line.monto_contra)))			
			total += line.monto_contra
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,15,pagina)


		c.setFont("Times-Bold", 9)
		c.drawString(555,pos_inicial, "TOTAL: ")
		c.drawRightString(645+110,pos_inicial, '{:,.2f}'.format(decimal.Decimal("%0.2f"%total)))

		c.save()

	@api.multi
	def particionar_text(self,c):
		tet = ""
		for i in range(len(c)):
			tet += c[i]
			lines = simpleSplit(tet,'Times-Roman',8,95)
			if len(lines)>1:
				return tet[:-1]
		return tet


	@api.multi
	def cargar_pagina(self,c,pagina):
		c.__dict__.update(self.save_page_states[pagina-1])

	@api.multi
	def finalizar(self,c):
		for state in self.save_page_states:
			c.__dict__.update(state)
			canvas.Canvas.showPage(c)
		canvas.Canvas.save(c)

	@api.multi
	def guardar_state(self,c):
		if c._pageNumber > len(self.save_page_states):
			self.save_page_states.append(dict(c.__dict__))
		else:
			self.save_page_states[c._pageNumber-1] = dict(c.__dict__)
		return True

	@api.multi
	def verify_linea(self,c,wReal,hReal,posactual,valor,pagina):
		if posactual <40:
			c.showPage()
			self.cabezera(c,wReal,hReal)

			c.setFont("Times-Bold", 9)
			#c.drawCentredString(421,25,'Pág. ' + str(pagina+1))
			return pagina+1,hReal-136
		else:
			return pagina,posactual-valor











class account_asset_formato_71(osv.TransientModel):
	_name='account.asset.formato.71'
	
	period_id = fields.Many2one('account.fiscalyear','Año fiscal',required=True)
	period_period_id = fields.Many2one('account.period','Periodo',required=True)
	tipo = fields.Selection([('pdf', 'Pdf'),('excel', 'Excel')],string='Tipo', required=True)
	
	global_controler = True
	save_page_states = []


	@api.onchange('period_id')
	def onchange_fiscalyear(self):
		if self.period_id:
			return {'domain':{'period_period_id':[('fiscalyear_id','=',self.period_id.id )] }}
		else:
			return {'domain':{'period_period_id':[] }}


	@api.multi
	def do_rebuild(self):
		fechaini_obj = self.period_period_id.date_stop
			
		move_obj=self.env['account.asset.asset']
		filtro = []
		filtro.append( ('purchase_date','<=',str(fechaini_obj) ) )
		filtro.append( ('parent_id','=',False) )
		
		lstidsmove = move_obj.search( filtro )
		
		mod_obj = self.env['ir.model.data']
		act_obj = self.env['ir.actions.act_window']

		if self.tipo == 'excel':
			import io
			from xlsxwriter.workbook import Workbook
			output = io.BytesIO()
			########### PRIMERA HOJA DE LA DATA EN TABLA
			#workbook = Workbook(output, {'in_memory': True})

			direccion = self.env['main.parameter'].search([])[0].dir_create_file

			workbook = Workbook(direccion +'tempo_activo_71.xlsx')
			worksheet = workbook.add_worksheet("Activo - Formato 74")
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
			numberdos = workbook.add_format({'num_format':'0.00'})
			bord = workbook.add_format()
			bord.set_border(style=1)
			numberdos.set_border(style=1)
			numbertres.set_border(style=1)			
			x= 8				
			tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			tam_letra = 1.2
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')

			worksheet.write(0,0, 'FORMATO 7.1: "REGISTRO DE ACTIVOS FIJOS - DETALLE DE LOS ACTIVOS FIJOS"', bold)



			worksheet.write(2,0, "Periodo:",bold)
			tam_col[0] = tam_letra* len("Periodo:") if tam_letra* len("Periodo:")> tam_col[0] else tam_col[0]

			worksheet.write(2,3, str(self.period_id.name), normal)
			tam_col[1] = tam_letra* len(str(self.period_id.name)) if tam_letra* len(str(self.period_id.name))> tam_col[1] else tam_col[1]
			

			company = self.env['res.company'].search([])[0]

			worksheet.write(3,0, "RUC:",bold)
			tam_col[0] = tam_letra* len("RUC:") if tam_letra* len("RUC:")> tam_col[0] else tam_col[0]

			worksheet.write(3,3, str(company.partner_id.type_number), normal)
			tam_col[1] = tam_letra* len(str(company.partner_id.type_number)) if tam_letra* len(str(company.partner_id.type_number))> tam_col[1] else tam_col[1]
			



			worksheet.write(4,0, u"Apellidos y nombres, denominación o Razón Social:",bold)
			tam_col[0] = tam_letra* len(u"Apellidos y nombres, denominación o Razón Social:") if tam_letra* len(u"Apellidos y nombres, denominación o Razón Social:")> tam_col[0] else tam_col[0]

			worksheet.write(4,3, str(company.partner_id.name), normal)
			tam_col[1] = tam_letra* len(str(company.partner_id.name)) if tam_letra* len(str(company.partner_id.name))> tam_col[1] else tam_col[1]
			

			worksheet.merge_range(6,0,7,0, u"Código Relacionado con el Activo Fijo",boldbord)
			tam_col[0] = tam_letra* len(u"Código Relacionado co") if tam_letra* len(u"Código Relacionado co")> tam_col[0] else tam_col[0]
			worksheet.merge_range(6,1,7,1, "Cuenta Contable del Activo Fijo",boldbord)
			tam_col[1] = tam_letra* len("Cuenta Contable de") if tam_letra* len("Cuenta Contable de")> tam_col[1] else tam_col[1]
			worksheet.write(7,2, u"Descripción",boldbord)
			tam_col[2] = tam_letra* len(u"Descripción") if tam_letra* len(u"Descripción")> tam_col[2] else tam_col[2]
			worksheet.write(7,3, "Marca del Activo Fijo",boldbord)
			tam_col[3] = tam_letra* len("Marca del Activo Fijo") if tam_letra* len("Marca del Activo Fijo")> tam_col[3] else tam_col[3]
			worksheet.write(7,4, u"Modelo del Activo Fijo",boldbord)
			tam_col[4] = tam_letra* len(u"Modelo del Activo Fijo") if tam_letra* len(u"Modelo del Activo Fijo")> tam_col[4] else tam_col[4]
			worksheet.write(7,5, u"Número de Serie y/o Placa del Activo Fijo",boldbord)
			tam_col[5] = tam_letra* len(u"Número de Serie y/o Placa del Activo Fijo") if tam_letra* len(u"Número de Serie y/o Placa del Activo Fijo")> tam_col[5] else tam_col[5]
			
			worksheet.merge_range(6,2,6,5, u"Detalle del Activo Fijo",boldbord)
			
			worksheet.merge_range(6,6,7,6, "Saldo Inicial",boldbord)
			tam_col[6] = tam_letra* len(u"Saldo Inicial") if tam_letra* len(u"Saldo Inicial")> tam_col[0] else tam_col[0]

			worksheet.merge_range(6,7,7,7, "Adquisiones Adiciones",boldbord)
			tam_col[7] = tam_letra* len(u"Adquisiones Adiciones") if tam_letra* len(u"Adquisiones Adiciones")> tam_col[0] else tam_col[0]

			worksheet.merge_range(6,8,7,8, "Mejoras",boldbord)
			tam_col[8] = tam_letra* len(u"Mejoras") if tam_letra* len(u"Mejoras")> tam_col[0] else tam_col[0]

			worksheet.merge_range(6,9,7,9, "Retiros y/o Bajas",boldbord)
			tam_col[9] = tam_letra* len(u"Retiros y/o Bajas") if tam_letra* len(u"Retiros y/o Bajas")> tam_col[0] else tam_col[0]

			worksheet.merge_range(6,10,7,10, "Otros Ajustes",boldbord)
			tam_col[10] = tam_letra* len(u"Otros Ajustes") if tam_letra* len(u"Otros Ajustes")> tam_col[0] else tam_col[0]

			
			worksheet.merge_range(6,11,7,11, u"Valor Histórico del Activo Fijo al 31.12",boldbord)
			tam_col[11] = tam_letra* len(u"Valor Histórico del Act") if tam_letra* len(u"Valor Histórico del Act")> tam_col[0] else tam_col[0]

			worksheet.merge_range(6,12,7,12, u"Ajuste por Inflación",boldbord)
			tam_col[12] = tam_letra* len(u"Ajuste por Inflación") if tam_letra* len(u"Ajuste por Inflación")> tam_col[0] else tam_col[0]

			worksheet.merge_range(6,13,7,13, "Valor Ajustado del Activo Fijo al 31.12",boldbord)
			tam_col[13] = tam_letra* len(u"Valor Ajustado del Act") if tam_letra* len(u"Valor Ajustado del Act")> tam_col[0] else tam_col[0]

			worksheet.merge_range(6,14,7,14, u"Fecha de Adquisición",boldbord)
			tam_col[14] = tam_letra* len(u"Fecha de Adquisición") if tam_letra* len(u"Fecha de Adquisición")> tam_col[0] else tam_col[0]

			worksheet.merge_range(6,15,7,15, "Fecha Inicio del Uso del Activo Fijo",boldbord)
			tam_col[15] = tam_letra* len(u"Fecha Inicio del Uso") if tam_letra* len(u"Fecha Inicio del Uso")> tam_col[0] else tam_col[0]

			worksheet.merge_range(6,16,6,17, u"Depreciación",boldbord)

			worksheet.write(7,16, u"Método Aplicado",boldbord)
			tam_col[16] = tam_letra* len(u"Método Aplicado") if tam_letra* len(u"Método Aplicado")> tam_col[0] else tam_col[0]

			worksheet.write(7,17, u"Nro de Documento de Autorización",boldbord)
			tam_col[17] = tam_letra* len(u"Nro de Documento de Autorización") if tam_letra* len(u"Nro de Documento de Autorización")> tam_col[0] else tam_col[0]

			worksheet.merge_range(6,18,7,18, u"Porcentaje de Depreciación",boldbord)
			tam_col[18] = tam_letra* len(u"Porcentaje de Depreciación") if tam_letra* len(u"Porcentaje de Depreciación")> tam_col[0] else tam_col[0]




			worksheet.merge_range(6,19,7,19, u"Depreciación acumulada al Cierre del Ejercicio Anterior",boldbord)
			tam_col[19] = tam_letra* len(u"Depreciación acumulada al Cierre") if tam_letra* len(u"Depreciación acumulada al Cierre")> tam_col[0] else tam_col[0]

			worksheet.merge_range(6,20,7,20, u"Depreciación del Ejercicio",boldbord)
			tam_col[20] = tam_letra* len(u"Depreciación del Ejercicio") if tam_letra* len(u"Depreciación del Ejercicio")> tam_col[0] else tam_col[0]

			worksheet.merge_range(6,21,7,21, u"Depreciación del Ejercicio Relacionada con los retiros y/o bajas",boldbord)
			tam_col[21] = tam_letra* len(u"lacionada con los retiros y/o bajas") if tam_letra* len(u"lacionada con los retiros y/o bajas")> tam_col[0] else tam_col[0]

			worksheet.merge_range(6,22,7,22, u"Depreciación relacionada con otros ajusted",boldbord)
			tam_col[22] = tam_letra* len(u"relacionada con otros ajusted") if tam_letra* len(u"relacionada con otros ajusted")> tam_col[0] else tam_col[0]

			worksheet.merge_range(6,23,7,23, u"Depreciación acumulada Histórico",boldbord)
			tam_col[23] = tam_letra* len(u" acumulada Histórico") if tam_letra* len(u" acumulada Histórico")> tam_col[0] else tam_col[0]

			worksheet.merge_range(6,24,7,24, u"Ajuste por inflación de la Depreciación",boldbord)
			tam_col[24] = tam_letra* len(u"inflación de la Depreciación") if tam_letra* len(u"inflación de la Depreciación")> tam_col[0] else tam_col[0]

			worksheet.merge_range(6,25,7,25, u"Depreciación acumulada Ajustada por Inflación",boldbord)
			tam_col[25] = tam_letra* len(u" Ajustada por Inflación") if tam_letra* len(u" Ajustada por Inflación")> tam_col[0] else tam_col[0]




			for line in lstidsmove:

				hijos = self.env['account.asset.asset'].search([('parent_id','=',line.id),('purchase_date','<=',str(fechaini_obj))])

				total = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

				for h in hijos:
					total[0] += h.purchase_value if h.purchase_date < self.period_id.date_start else 0
					total[1] += h.purchase_value if h.purchase_date >= self.period_id.date_start and h.purchase_date <= self.period_id.date_stop  and h.tipo == 'adquisicion' else 0
					total[2] += h.purchase_value if h.purchase_date >= self.period_id.date_start and h.purchase_date <= self.period_id.date_stop  and h.tipo == 'mejoras' else 0
					

					primer_acum_neg = h.purchase_value if h.purchase_date <= self.period_id.date_start else 0
					primer_acum_neg += h.purchase_value if h.purchase_date >= self.period_id.date_start and h.purchase_date <= self.period_id.date_stop  and h.tipo == 'adquisicion' else 0
					primer_acum_neg += h.purchase_value if h.purchase_date >= self.period_id.date_start and h.purchase_date <= self.period_id.date_stop  and h.tipo == 'mejoras' else 0
					primer_acum_neg += h.purchase_value if h.purchase_date >= self.period_id.date_start and h.purchase_date <= self.period_id.date_stop  and h.tipo == 'otros' else 0


					total[3] += (- primer_acum_neg) if h.state=='baja' else 0
					total[4] += h.purchase_value if h.purchase_date >= self.period_id.date_start and h.purchase_date <= self.period_id.date_stop  and h.tipo == 'otros' else 0
					total[5] += h.purchase_value
					total[6] += -h.depreciacion_retiro

					acum_anterior = 0
					for ii in h.depreciation_line_ids:
						if ii.depreciation_date < self.period_id.date_start:
							acum_anterior += ii.depreciated_value
					total[7] += acum_anterior

					acum_actual = 0
					for ii in h.depreciation_line_ids:
						if ii.depreciation_date >= self.period_id.date_start and ii.depreciation_date <= self.period_period_id.date_stop:
							acum_actual += ii.depreciated_value

					total[8] = acum_actual if h.tipo=='adquisicion' else 0
					#total[9] = acum_actual if h.tipo=='retiro' else 0
					total[10] = acum_actual if h.tipo=='otros' else 0 
					total[11] = acum_anterior+acum_actual
				#faltan estos 3

				#modificar para agrupar desde codigo e ir sumando en los hijos que se encuentren. Por SQL va ser muy costoso demasiado
				#modificar o crear una funcion que saque eso y devuelva un array y de ahi solo sumar

				#terminar eso y el calculo y de ahi solo sumar mucho mas rapido y confiable que por sql y ibujar esa nueva información


				worksheet.write(x,0,line.codigo if line.codigo else '' ,bord )
				worksheet.write(x,1,line.category_id.account_asset_id.code if line.category_id.account_asset_id.code else '' ,bord )
				worksheet.write(x,2,line.name if line.name  else '',bord )
				worksheet.write(x,3,line.marca if line.marca  else '',bord )
				worksheet.write(x,4,line.modelo if line.modelo  else '',bord )
				worksheet.write(x,5,line.serie if line.serie  else '',bord )

				primer_acum_neg = (line.purchase_value+total[0] if line.purchase_date < self.period_id.date_start else 0 +total[0])
				primer_acum_neg += (line.purchase_value+total[1] if line.purchase_date >= self.period_id.date_start and line.purchase_date <= self.period_id.date_stop  and line.tipo == 'adquisicion' else 0+total[1]) 
				primer_acum_neg += (line.purchase_value+total[2] if line.purchase_date >= self.period_id.date_start  and line.purchase_date <= self.period_id.date_stop and line.tipo == 'mejoras' else 0+total[2])
				primer_acum_neg += (line.purchase_value+total[4] if line.purchase_date >= self.period_id.date_start  and line.purchase_date <= self.period_id.date_stop and line.tipo == 'otros' else 0+total[4])

				worksheet.write(x,6,line.purchase_value+total[0] if line.purchase_date < self.period_id.date_start else 0 +total[0],numberdos )
				worksheet.write(x,7,line.purchase_value+total[1] if line.purchase_date >= self.period_id.date_start and line.purchase_date <= self.period_id.date_stop  and line.tipo == 'adquisicion' else 0+total[1],numberdos )
				worksheet.write(x,8,line.purchase_value+total[2] if line.purchase_date >= self.period_id.date_start  and line.purchase_date <= self.period_id.date_stop and line.tipo == 'mejoras' else 0+total[2],numberdos )
				worksheet.write(x,9, (-primer_acum_neg+total[3]) if line.state=='baja' else 0,numberdos )
				worksheet.write(x,10,line.purchase_value+total[4] if line.purchase_date >= self.period_id.date_start  and line.purchase_date <= self.period_id.date_stop and line.tipo == 'otros' else 0+total[4],numberdos )
				
				primer_acum = (line.purchase_value+total[0] if line.purchase_date < self.period_id.date_start else 0 +total[0])
				primer_acum += (line.purchase_value+total[1] if line.purchase_date >= self.period_id.date_start and line.purchase_date <= self.period_id.date_stop  and line.tipo == 'adquisicion' else 0+total[1]) 
				primer_acum += (line.purchase_value+total[2] if line.purchase_date >= self.period_id.date_start  and line.purchase_date <= self.period_id.date_stop and line.tipo == 'mejoras' else 0+total[2])
				primer_acum += (-primer_acum_neg+total[3]) if line.state=='baja' else 0
				primer_acum += (line.purchase_value+total[4] if line.purchase_date >= self.period_id.date_start  and line.purchase_date <= self.period_id.date_stop and line.tipo == 'otros' else 0+total[4])


				#worksheet.write(x,11,line.purchase_value+total[5] + primer_acum, numberdos )
				worksheet.write(x,11, primer_acum, numberdos )
				worksheet.write(x,12,'',bord )
				worksheet.write(x,13,'',bord )
				worksheet.write(x,14,line.purchase_date if line.purchase_date else '',bord )
				worksheet.write(x,15,line.date_start if line.date_start else '',bord )
				worksheet.write(x,16,'Metodo Lineal',bord )
				worksheet.write(x,17,line.autorizacion_depreciacion if line.autorizacion_depreciacion else '',bord )
				worksheet.write(x,18,line.category_id.percent_depreciacion,numberdos )
				#worksheet.write(x,18,-line.depreciacion_retiro+total[6],numberdos )
				
				acum_anterior = 0
				for ii in line.depreciation_line_ids:
					if ii.depreciation_date < self.period_id.date_start:
						acum_anterior += ii.depreciated_value

				worksheet.write(x,19, acum_anterior+total[7], numberdos )

				acum_actual = 0
				for ii in line.depreciation_line_ids:
					if ii.depreciation_date >= self.period_id.date_start and ii.depreciation_date <= self.period_period_id.date_stop:
						acum_actual += ii.depreciated_value

				worksheet.write(x,20,acum_actual+total[8] if line.tipo=='adquisicion' else 0+total[8] ,numberdos)

				total_ultimo = acum_anterior + total[7]
				total_ultimo += acum_actual+total[8] if line.tipo=='adquisicion' else 0+total[8]
				total_ultimo += acum_actual+total[10] if line.tipo=='otros' else 0+total[10]

				worksheet.write(x,21,( -(total_ultimo ) if line.state == 'baja' else 0) ,numberdos)

				worksheet.write(x,22,acum_actual+total[10] if line.tipo=='otros' else 0+total[10] ,numberdos)
				worksheet.write(x,23,acum_anterior+acum_actual+total[11] + ( ( -total_ultimo ) if line.state == 'baja' else 0 +total[9] ) ,numberdos)
				worksheet.write(x,24,0,numberdos )
				worksheet.write(x,25,0,numberdos )

				x = x +1

			tam_col = [10.29,7.14,32.57,9.14,13.57,8.57,8.14,8.14,8.14,8.14,8.14,8.14,8.14,8.14,9.71,9.71,12.7,12.7,4,8.14,8.14,8.14,8.14,8.14,8.14,8.14,8.14,8.14,8.14]

			worksheet.set_row(7, 78.75)
			worksheet.set_column(0,0, tam_col[0])
			worksheet.set_column(1,1, tam_col[1])
			worksheet.set_column(2,2, tam_col[2])
			worksheet.set_column(3,3, tam_col[3])
			worksheet.set_column(4,4, tam_col[4])
			worksheet.set_column(5,5, tam_col[5])
			worksheet.set_column(6,6, tam_col[6])
			worksheet.set_column(7,7, tam_col[7])
			worksheet.set_column(8,8, tam_col[8])
			worksheet.set_column(9,9, tam_col[9])
			worksheet.set_column(10,10, tam_col[10])
			worksheet.set_column(11,11, tam_col[11])
			worksheet.set_column(12,12, tam_col[12])
			worksheet.set_column(13,13, tam_col[13])
			worksheet.set_column(14,14, tam_col[14])
			worksheet.set_column(15,15, tam_col[15])
			worksheet.set_column(16,16, tam_col[16])
			worksheet.set_column(17,17, tam_col[17])
			worksheet.set_column(18,18, tam_col[18])
			worksheet.set_column(19,19, tam_col[19])
			worksheet.set_column(20,20, tam_col[20])
			worksheet.set_column(21,21, tam_col[21])
			worksheet.set_column(22,22, tam_col[22])
			worksheet.set_column(23,23, tam_col[23])
			worksheet.set_column(24,24, tam_col[24])
			worksheet.set_column(25,25, tam_col[25])
			workbook.close()
			
			f = open(direccion + 'tempo_activo_71.xlsx', 'rb')
			
			
			sfs_obj = self.pool.get('account_contable_book_it.sunat_file_save')
			vals = {
				'output_name': 'ActivoFormato7_1.xlsx',
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



		if self.tipo == 'pdf':
			self.reporteador()
			
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')
			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']
			import os

			direccion = self.env['main.parameter'].search([])[0].dir_create_file
			vals = {
				'output_name': 'ActivoFormato7_1.pdf',
				'output_file': open(direccion + "a.pdf", "rb").read().encode("base64"),	
			}
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
	def cabezera(self,c,wReal,hReal):

		c.setFont("Times-Bold", 12)
		c.setFillColor(black)

		c.setFont("Times-Bold", 9)
		c.drawCentredString((wReal/2)+20,hReal, u"FORMATO 7.1: REGISTRO DE ACTIVOS FIJOS - DETALLE DE LOS ACTIVOS FIJOS")
		c.drawString(40,hReal-24, u"Periodo: ")

		c.setFont("Times-Roman", 9)
		c.drawString(90,hReal-24, self.period_id.name)
		c.setFont("Times-Bold", 9)
		c.drawString(40,hReal-36, u"RUC: " )

		c.setFont("Times-Roman", 9)
		c.drawString(90,hReal-36, self.env["res.company"].search([])[0].partner_id.type_number )

		c.setFont("Times-Bold", 9)

		c.drawString(40,hReal-48, u"Apellido y nombres, Denominación o Razón Social: " )
		c.setFont("Times-Roman", 9)
		c.drawString(290,hReal-48,  self.env["res.company"].search([])[0].name.upper() )

		style = getSampleStyleSheet()["Normal"]
		style.leading = 8
		style.alignment= 1
		paragraph1 = Paragraph(
			"<font size=5><b>CODIGO RELACIONADO CON EL ACTIVO FIJO</b></font>",
			style
		)
		paragraph2 = Paragraph(
			"<font size=5><b>CUENTA CONTABLE DEL ACTIVO FIJO</b></font>",
			style
		)
		paragraph3 = Paragraph(
			"<font size=5><b>DETALLE DEL ACTIVO FIJO</b></font>",
			style
		)
		paragraph4 = Paragraph(
			"<font size=5><b>DESCRIPCION</b></font>",
			style
		)
		paragraph5 = Paragraph(
			"<font size=5><b>MARCA DEL ACTIVO FIJO</b></font>",
			style
		)
		paragraph6 = Paragraph(
			"<font size=5><b>MODELO DEL ACTIVO FIJO</b></font>",
			style
		)
		paragraph7 = Paragraph(
			"<font size=5><b>NUMERO DE SERIE Y/O PLACA DEL ACTIVO FIJO</b></font>",
			style
		)
		paragraph8 = Paragraph(
			"<font size=5><b>SALDO INICIAL</b></font>",
			style
		)
		paragraph9 = Paragraph(
			"<font size=5><b>ADQUISICIONES ADICIONES</b></font>",
			style
		)
		paragraph10 = Paragraph(
			"<font size=5><b>MEJORAS</b></font>",
			style
		)
		paragraph11 = Paragraph(
			"<font size=5><b>RETIROS Y/O BAJAS</b></font>",
			style
		)
		paragraph12 = Paragraph(
			"<font size=5><b>OTROS AJUSTES</b></font>",
			style
		)
		paragraph13 = Paragraph(
			"<font size=5><b>VALOR HISTORICO DEL ACTIVO FIJO AL 31.12</b></font>",
			style
		)
		paragraph14 = Paragraph(
			"<font size=5><b>AJUSTE POR INFLACION</b></font>",
			style
		)
		paragraph15 = Paragraph(
			"<font size=5><b>VALOR AJUSTADO DEL ACTIVO FIJO AL 31.12</b></font>",
			style
		)
		paragraph16 = Paragraph(
			"<font size=5><b>FECHA DE ADQUISICION</b></font>",
			style
		)
		paragraph17 = Paragraph(
			"<font size=5><b>FECHA DE INICIO DEL USO DEL ACTIVO FIJO</b></font>",
			style
		)
		paragraph18 = Paragraph(
			"<font size=5><b>DEPRECIACION</b></font>",
			style
		)
		paragraph19 = Paragraph(
			"<font size=5><b>METODO APLICADO</b></font>",
			style
		)
		paragraph20 = Paragraph(
			"<font size=5><b>Nro DE DOCUMENTO DE AUTORIZACION</b></font>",
			style
		)
		paragraph21 = Paragraph(
			"<font size=5><b>PORCENTAJE DE DEPRECIACION</b></font>",
			style
		)
		paragraph22 = Paragraph(
			"<font size=5><b>DEPRECIACION ACUMULADA AL CIERRE DEL EJERCICIO ANTERIOR</b></font>",
			style
		)
		paragraph23 = Paragraph(
			"<font size=5><b>DEPRECIACION DEL EJERCICIO</b></font>",
			style
		)
		paragraph24 = Paragraph(
			"<font size=5><b>DEPRECIACION DEL EJERCICIO RELACIONADA CON LOS RETIROS Y/O BAJAS</b></font>",
			style
		)
		paragraph25 = Paragraph(
			"<font size=5><b>DEPRECIACION RELACIONADA CON OTROS AJUSTES</b></font>",
			style
		)
		paragraph26 = Paragraph(
			"<font size=5><b>DEPRECIACION ACUMULADA HISTORICA</b></font>",
			style
		)
		paragraph27 = Paragraph(
			"<font size=5><b>AJUSTE POR INFLACION DE LA DEPRECIACION</b></font>",
			style
		)
		paragraph28 = Paragraph(
			"<font size=5><b>DEPRECIACION ACUMULADA AJUSTADA POR INFLACION</b></font>",
			style
		)
		#paragraph18,'' ,          paragraph21,  paragraph22, paragraph23, paragraph24, paragraph25 , paragraph26 ,paragraph27 ,paragraph28  
		#,paragraph19 , paragraph20, ''          ,  ''         , ''           , ''       ,  ''         , ''        ,  ''        ,   ''    
		
		if self.global_controler:
			data= [[ paragraph1 , paragraph2 , paragraph3 , '',        '',        '',         paragraph8, paragraph9, paragraph10, paragraph11,  paragraph12, paragraph13, paragraph14, paragraph15, paragraph16, paragraph17  ],
			[        '',          '',          paragraph4,  paragraph5,paragraph6,paragraph7, ''        ,  ''       ,     ''     , ''          ,  ''         ,  ''        , ''         , ''         , ''          , ''       ]]
			
			t=Table(data, colWidths=(50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50) ,rowHeights=( 13,40))
			t.setStyle(TableStyle([
				('SPAN',(0,0),(0,1)),
				('SPAN',(1,0),(1,1)),
				('SPAN',(2,0),(5,0)),

				('SPAN',(6,0),(6,1)),
				('SPAN',(7,0),(7,1)),
				('SPAN',(8,0),(8,1)),
				('SPAN',(9,0),(9,1)),
				('SPAN',(10,0),(10,1)),
				('SPAN',(11,0),(11,1)),
				('SPAN',(12,0),(12,1)),
				('SPAN',(13,0),(13,1)),
				('SPAN',(14,0),(14,1)),
				('SPAN',(15,0),(15,1)),

	#			('SPAN',(16,0),(17,0)),

	#			('SPAN',(18,0),(18,1)),
	#			('SPAN',(19,0),(19,1)),
	#			('SPAN',(20,0),(20,1)),
	#			('SPAN',(21,0),(21,1)),
	#			('SPAN',(22,0),(22,1)),
	#			('SPAN',(23,0),(23,1)),
	#			('SPAN',(24,0),(24,1)),
	#			('SPAN',(25,0),(25,1)),

				('GRID',(0,0),(-1,-1), 1, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Times-Bold'),
				('FONTSIZE',(0,0),(-1,-1),2)
			]))
			t.wrapOn(c,15,500)
			t.drawOn(c,15,hReal-115)
		else:
			data= [[ paragraph1 , paragraph2 , paragraph3 , '',        '',        '',         paragraph18,'' ,          paragraph21,  paragraph22, paragraph23, paragraph24, paragraph25 , paragraph26 ,paragraph27 ,paragraph28],
			[        '',          '',          paragraph4,  paragraph5,paragraph6,paragraph7, paragraph19 , paragraph20, ''          ,  ''         , ''           , ''       ,  ''         , ''        ,  ''        ,   '' ]]
			
			t=Table(data, colWidths=(50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50) ,rowHeights=( 23,40))
			t.setStyle(TableStyle([
				('SPAN',(0,0),(0,1)),
				('SPAN',(1,0),(1,1)),
				('SPAN',(2,0),(5,0)),

				('SPAN',(6,0),(7,0)),
				('SPAN',(8,0),(8,1)),
				('SPAN',(9,0),(9,1)),
				('SPAN',(10,0),(10,1)),
				('SPAN',(11,0),(11,1)),
				('SPAN',(12,0),(12,1)),
				('SPAN',(13,0),(13,1)),
				('SPAN',(14,0),(14,1)),
				('SPAN',(15,0),(15,1)),

	#			('SPAN',(16,0),(17,0)),

	#			('SPAN',(18,0),(18,1)),
	#			('SPAN',(19,0),(19,1)),
	#			('SPAN',(20,0),(20,1)),
	#			('SPAN',(21,0),(21,1)),
	#			('SPAN',(22,0),(22,1)),
	#			('SPAN',(23,0),(23,1)),
	#			('SPAN',(24,0),(24,1)),
	#			('SPAN',(25,0),(25,1)),

				('GRID',(0,0),(-1,-1), 1, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Times-Bold'),
				('FONTSIZE',(0,0),(-1,-1),2)
			]))
			t.wrapOn(c,15,500)
			t.drawOn(c,15,hReal-115)


	@api.multi
	def reporteador(self):

		import sys
		nivel_left_page = 1
		nivel_left_fila = 0
		
		nivel_right_page = 1
		nivel_right_fila = 0

		reload(sys)
		sys.setdefaultencoding('iso-8859-1')
		width , height = A4  # 595 , 842
		hReal = width- 30
		wReal = height - 40

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		c = canvas.Canvas( direccion + "a.pdf", pagesize=(height,width) )
		inicio = 0
		pos_inicial = hReal-125

		pagina = 1
		textPos = 0
		
		tamanios = {}
		voucherTamanio = None
		contTamanio = 0

		self.cabezera(c,wReal,hReal)


		c.setFont("Times-Bold", 10)
		#c.drawCentredString(421,25,'Pág. ' + str(pagina))

		#datos a consultar
		fechaini_obj = self.period_period_id.date_stop
	
		
		move_obj=self.env['account.asset.asset']
		filtro = []
		filtro.append( ('purchase_date','<=',str(fechaini_obj) ) )
		filtro.append( ('parent_id','=',False ) )
		
		lstidsmove = move_obj.search( filtro )


		aa = 0
		bb = 0
		cc = 0
		dd = 0
		ee = 0
		ff = 0
		for line in lstidsmove:

			hijos = self.env['account.asset.asset'].search([('parent_id','=',line.id),('purchase_date','<=',str(fechaini_obj))])

			total = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

			for h in hijos:
				total[0] += h.purchase_value if h.purchase_date < self.period_id.date_start else 0
				total[1] += h.purchase_value if h.purchase_date >= self.period_id.date_start and h.purchase_date <= self.period_id.date_stop  and h.tipo == 'adquisicion' else 0
				total[2] += h.purchase_value if h.purchase_date >= self.period_id.date_start and h.purchase_date <= self.period_id.date_stop  and h.tipo == 'mejoras' else 0
				

				primer_acum_neg = h.purchase_value if h.purchase_date < self.period_id.date_start else 0
				primer_acum_neg += h.purchase_value if h.purchase_date >= self.period_id.date_start and h.purchase_date <= self.period_id.date_stop  and h.tipo == 'adquisicion' else 0
				primer_acum_neg += h.purchase_value if h.purchase_date >= self.period_id.date_start and h.purchase_date <= self.period_id.date_stop  and h.tipo == 'mejoras' else 0
				primer_acum_neg += h.purchase_value if h.purchase_date >= self.period_id.date_start and h.purchase_date <= self.period_id.date_stop  and h.tipo == 'otros' else 0


				total[3] += (- primer_acum_neg) if h.state=='baja' else 0

				total[4] += h.purchase_value if h.purchase_date >= self.period_id.date_start and h.purchase_date <= self.period_id.date_stop  and h.tipo == 'otros' else 0
				total[5] += h.purchase_value
				total[6] += -h.depreciacion_retiro

				acum_anterior = 0
				for ii in h.depreciation_line_ids:
					if ii.depreciation_date < self.period_id.date_start:
						acum_anterior += ii.depreciated_value
				total[7] += acum_anterior

				acum_actual = 0
				for ii in h.depreciation_line_ids:
					if ii.depreciation_date >= self.period_id.date_start and ii.depreciation_date <= self.period_period_id.date_stop:
						acum_actual += ii.depreciated_value

				total[8] = acum_actual if h.tipo=='adquisicion' else 0
				#total[9] = acum_actual if h.tipo=='retiro' else 0
				total[10] = acum_actual if h.tipo=='otros' else 0 
				total[11] = acum_anterior+acum_actual


			c.setFont("Times-Roman", 5)

			c.drawString(15+3,pos_inicial, self.particionar_text(line.codigo) if line.codigo else '')
			c.drawString(65+3,pos_inicial, line.category_id.account_asset_id.code if line.category_id.account_asset_id.code else '')
			c.drawString(115+3,pos_inicial, self.particionar_text(line.name) if line.name  else '')
			c.drawString(165+3,pos_inicial, line.marca if line.marca  else '')
			c.drawString(215+3,pos_inicial, line.modelo if line.modelo  else '')
			c.drawString(265+3,pos_inicial, line.serie if line.serie  else '')


			primer_acum_neg = (line.purchase_value+total[0] if line.purchase_date < self.period_id.date_start else 0 +total[0])
			primer_acum_neg += (line.purchase_value+total[1] if line.purchase_date >= self.period_id.date_start and line.purchase_date <= self.period_id.date_stop  and line.tipo == 'adquisicion' else 0+total[1]) 
			primer_acum_neg += (line.purchase_value+total[2] if line.purchase_date >= self.period_id.date_start  and line.purchase_date <= self.period_id.date_stop and line.tipo == 'mejoras' else 0+total[2])
			primer_acum_neg += (line.purchase_value+total[4] if line.purchase_date >= self.period_id.date_start  and line.purchase_date <= self.period_id.date_stop and line.tipo == 'otros' else 0+total[4])

			c.drawRightString(365-3,pos_inicial, '{:,.2f}'.format(decimal.Decimal("%0.2f"%(line.purchase_value+total[0] if line.purchase_date < self.period_id.date_start else 0+total[0]))) )
			c.drawRightString(415-3,pos_inicial, '{:,.2f}'.format(decimal.Decimal("%0.2f"%(line.purchase_value+total[1] if line.purchase_date >= self.period_id.date_start and line.purchase_date <= self.period_id.date_stop  and line.tipo == 'adquisicion' else 0+total[1]))) )
			c.drawRightString(465-3,pos_inicial, '{:,.2f}'.format(decimal.Decimal("%0.2f"%(line.purchase_value+total[2] if line.purchase_date >= self.period_id.date_start  and line.purchase_date <= self.period_id.date_stop and line.tipo == 'mejoras' else 0+total[2]))) )
			c.drawRightString(515-3,pos_inicial, '{:,.2f}'.format(decimal.Decimal("%0.2f"%( (-primer_acum_neg+total[3]) if line.state=='baja' else 0 ))))

			c.drawRightString(565-3,pos_inicial, '{:,.2f}'.format(decimal.Decimal("%0.2f"%(line.purchase_value+total[4] if line.purchase_date >= self.period_id.date_start  and line.purchase_date <= self.period_id.date_stop and line.tipo == 'otros' else 0+total[4]))) )
			
			primer_acum = (line.purchase_value+total[0] if line.purchase_date < self.period_id.date_start else 0 +total[0])
			primer_acum += (line.purchase_value+total[1] if line.purchase_date >= self.period_id.date_start and line.purchase_date <= self.period_id.date_stop  and line.tipo == 'adquisicion' else 0+total[1]) 
			primer_acum += (line.purchase_value+total[2] if line.purchase_date >= self.period_id.date_start  and line.purchase_date <= self.period_id.date_stop and line.tipo == 'mejoras' else 0+total[2])
			primer_acum +=  (-primer_acum_neg+total[3]) if line.state=='baja' else 0
			primer_acum += (line.purchase_value+total[4] if line.purchase_date >= self.period_id.date_start  and line.purchase_date <= self.period_id.date_stop and line.tipo == 'otros' else 0+total[4])

			c.drawRightString(615-3,pos_inicial, '{:,.2f}'.format(decimal.Decimal("%0.2f"%(primer_acum) ))) # dos blancos
			c.drawString(715+3,pos_inicial, line.purchase_date if line.purchase_date else '')
			c.drawString(765+3,pos_inicial, line.date_start if line.date_start else '')
			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)
			aa+=line.purchase_value+total[0] if line.purchase_date < self.period_id.date_start else 0+total[0]
			bb+=line.purchase_value+total[1] if line.purchase_date >= self.period_id.date_start and line.purchase_date <= self.period_id.date_stop  and line.tipo == 'adquisicion' else 0+total[1]
			cc+=line.purchase_value+total[2] if line.purchase_date >= self.period_id.date_start  and line.purchase_date <= self.period_id.date_stop and line.tipo == 'mejoras' else 0+total[2]
			dd+= (-primer_acum_neg+total[3]) if line.state=='baja' else 0 
			ee+=line.purchase_value+total[4] if line.purchase_date >= self.period_id.date_start  and line.purchase_date <= self.period_id.date_stop and line.tipo == 'otros' else 0+total[4]
			ff+=primer_acum

		c.setFont("Times-Bold", 5)
		c.drawString(265+3,pos_inicial, 'TOTAL:')
		c.drawRightString(365-3,pos_inicial, '{:,.2f}'.format(decimal.Decimal("%0.2f"%(aa) )))
		c.drawRightString(415-3,pos_inicial, '{:,.2f}'.format(decimal.Decimal("%0.2f"%(bb) )))
		c.drawRightString(465-3,pos_inicial, '{:,.2f}'.format(decimal.Decimal("%0.2f"%(cc) )))
		c.drawRightString(515-3,pos_inicial, '{:,.2f}'.format(decimal.Decimal("%0.2f"%(dd) )))
		c.drawRightString(565-3,pos_inicial, '{:,.2f}'.format(decimal.Decimal("%0.2f"%(ee) )))
		c.drawRightString(615-3,pos_inicial, '{:,.2f}'.format(decimal.Decimal("%0.2f"%(ff) ))) # dos blancos



		c.showPage()

		inicio = 0
		pos_inicial = hReal-125

		pagina = 1
		textPos = 0
		
		tamanios = {}
		voucherTamanio = None
		contTamanio = 0

		self.global_controler = False
		self.cabezera(c,wReal,hReal)


		c.setFont("Times-Bold", 10)
		#c.drawCentredString(421,25,'Pág. ' + str(pagina))

		#datos a consultar
		fechaini_obj = self.period_period_id.date_stop
	
		
		move_obj=self.env['account.asset.asset']
		filtro = []
		filtro.append( ('purchase_date','<=',str(fechaini_obj) ) )
		filtro.append( ('parent_id','=',False ) )
		lstidsmove = move_obj.search( filtro )


		aa = 0
		bb = 0
		cc = 0
		dd = 0
		ee = 0
		ff = 0
		for line in lstidsmove:

			hijos = self.env['account.asset.asset'].search([('parent_id','=',line.id),('purchase_date','<=',str(fechaini_obj))])

			total = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

			for h in hijos:
				total[0] += h.purchase_value if h.purchase_date < self.period_id.date_start else 0
				total[1] += h.purchase_value if h.purchase_date >= self.period_id.date_start and h.purchase_date <= self.period_id.date_stop  and h.tipo == 'adquisicion' else 0
				total[2] += h.purchase_value if h.purchase_date >= self.period_id.date_start and h.purchase_date <= self.period_id.date_stop  and h.tipo == 'mejoras' else 0
				
				primer_acum_neg = h.purchase_value if h.purchase_date < self.period_id.date_start else 0
				primer_acum_neg += h.purchase_value if h.purchase_date >= self.period_id.date_start and h.purchase_date <= self.period_id.date_stop  and h.tipo == 'adquisicion' else 0
				primer_acum_neg += h.purchase_value if h.purchase_date >= self.period_id.date_start and h.purchase_date <= self.period_id.date_stop  and h.tipo == 'mejoras' else 0
				primer_acum_neg += h.purchase_value if h.purchase_date >= self.period_id.date_start and h.purchase_date <= self.period_id.date_stop  and h.tipo == 'otros' else 0


				total[3] += - primer_acum_neg
				total[4] += h.purchase_value if h.purchase_date >= self.period_id.date_start and h.purchase_date <= self.period_id.date_stop  and h.tipo == 'otros' else 0
				total[5] += h.purchase_value
				total[6] += -h.depreciacion_retiro

				acum_anterior = 0
				for ii in h.depreciation_line_ids:
					if ii.depreciation_date < self.period_id.date_start:
						acum_anterior += ii.depreciated_value
				total[7] += acum_anterior

				acum_actual = 0
				for ii in h.depreciation_line_ids:
					if ii.depreciation_date >= self.period_id.date_start and ii.depreciation_date <= self.period_period_id.date_stop:
						acum_actual += ii.depreciated_value

				total[8] = acum_actual if h.tipo=='adquisicion' else 0
				#total[9] = acum_actual if h.tipo=='retiro' else 0
				total[10] = acum_actual if h.tipo=='otros' else 0 
				total[11] = acum_anterior+acum_actual

			c.setFont("Times-Roman", 5)

			c.drawString(15+3,pos_inicial, self.particionar_text(line.codigo) if line.codigo else '')
			c.drawString(65+3,pos_inicial, line.category_id.account_asset_id.code if line.category_id.account_asset_id.code else '')
			c.drawString(115+3,pos_inicial, self.particionar_text(line.name) if line.name  else '')
			c.drawString(165+3,pos_inicial, line.marca if line.marca  else '')
			c.drawString(215+3,pos_inicial, line.modelo if line.modelo  else '')
			c.drawString(265+3,pos_inicial, line.serie if line.serie  else '')
			c.drawString(315+3,pos_inicial, 'Metodo Lineal' )
			c.drawString(365+3,pos_inicial, line.autorizacion_depreciacion if line.autorizacion_depreciacion else '' )
			c.drawRightString(465-3,pos_inicial, '{:,.2f}'.format(decimal.Decimal("%0.2f"%( line.category_id.percent_depreciacion) )))

			acum_anterior = 0
			for ii in line.depreciation_line_ids:
				if ii.depreciation_date < self.period_id.date_start:
					acum_anterior += ii.depreciated_value

			c.drawRightString(515-3,pos_inicial, '{:,.2f}'.format(decimal.Decimal("%0.2f"%(acum_anterior+total[7]) )))

			acum_actual = 0
			for ii in line.depreciation_line_ids:
				if ii.depreciation_date >= self.period_id.date_start and ii.depreciation_date <= self.period_period_id.date_stop:
					acum_actual += ii.depreciated_value

			c.drawRightString(565-3,pos_inicial, '{:,.2f}'.format(decimal.Decimal("%0.2f"%(acum_actual+total[8] if line.tipo=='adquisicion' else 0+total[8]) )))


			total_ultimo = acum_anterior + total[7]
			total_ultimo += acum_actual+total[8] if line.tipo=='adquisicion' else 0+total[8]
			total_ultimo += acum_actual+total[10] if line.tipo=='otros' else 0+total[10]


			c.drawRightString(615-3,pos_inicial, '{:,.2f}'.format(decimal.Decimal("%0.2f"%( ((-total_ultimo) if total_ultimo!= 0 else 0 ) if line.state=='baja' else 0 ) )))
			c.drawRightString(665-3,pos_inicial, '{:,.2f}'.format(decimal.Decimal("%0.2f"%(acum_actual+total[10] if line.tipo=='otros' else 0+total[10]) )))
			c.drawRightString(715-3,pos_inicial, '{:,.2f}'.format(decimal.Decimal("%0.2f"%(acum_anterior+acum_actual+total[11] + ( ((-total_ultimo) if total_ultimo!= 0 else 0 ) if line.state=='baja' else 0 ) ) )))
			c.drawRightString(765-3,pos_inicial, "%0.2f"%(0) )
			c.drawRightString(815-3,pos_inicial, "%0.2f"%(0) )

			pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,12,pagina)

			aa+=-line.depreciacion_retiro+total[6]
			bb+=acum_anterior+total[7]
			cc+=acum_actual+total[8] if line.tipo=='adquisicion' else 0+total[8]
			dd+=((-total_ultimo) if total_ultimo!= 0 else 0 ) if line.state=='baja' else 0
			ee+=acum_actual+total[10] if line.tipo=='otros' else 0+total[10]
			ff+=acum_anterior+acum_actual+total[11]+ ( ((-total_ultimo) if total_ultimo!= 0 else 0 ) if line.state=='baja' else 0 )

				


		c.setFont("Times-Bold", 5)
		c.drawString(265+3,pos_inicial, 'TOTAL:')
		c.drawRightString(465-3,pos_inicial, '{:,.2f}'.format(decimal.Decimal("%0.2f"%(aa) )))
		c.drawRightString(515-3,pos_inicial, '{:,.2f}'.format(decimal.Decimal("%0.2f"%(bb) )))
		c.drawRightString(565-3,pos_inicial, '{:,.2f}'.format(decimal.Decimal("%0.2f"%(cc) )))
		c.drawRightString(615-3,pos_inicial, '{:,.2f}'.format(decimal.Decimal("%0.2f"%(dd) )))
		c.drawRightString(665-3,pos_inicial, '{:,.2f}'.format(decimal.Decimal("%0.2f"%(ee) )))
		c.drawRightString(715-3,pos_inicial, '{:,.2f}'.format(decimal.Decimal("%0.2f"%(ff) ))) # dos blancos
		c.drawRightString(765-3,pos_inicial, "%0.2f"%(0) )
		c.drawRightString(815-3,pos_inicial, "%0.2f"%(0) )

		self.finalizar(c)

	@api.multi
	def particionar_text(self,c):
		tet = ""
		for i in range(len(c)):
			tet += c[i]
			lines = simpleSplit(tet,'Times-Roman',5,48)
			if len(lines)>1:
				return tet[:-1]
		return tet


	@api.multi
	def cargar_pagina(self,c,pagina):
		c.__dict__.update(self.save_page_states[pagina-1])

	@api.multi
	def finalizar(self,c):
		for state in self.save_page_states:
			c.__dict__.update(state)
			canvas.Canvas.showPage(c)
		canvas.Canvas.save(c)

	@api.multi
	def guardar_state(self,c):
		if c._pageNumber > len(self.save_page_states):
			self.save_page_states.append(dict(c.__dict__))
		else:
			self.save_page_states[c._pageNumber-1] = dict(c.__dict__)
		return True

	@api.multi
	def verify_linea(self,c,wReal,hReal,posactual,valor,pagina):
		if posactual <40:
			if c._pageNumber > len(self.save_page_states):
				self.save_page_states.append(dict(c.__dict__))
			else:
				self.save_page_states[c._pageNumber-1] = dict(c.__dict__)
			c._startPage()
			self.cabezera(c,wReal,hReal)

			c.setFont("Times-Bold", 10)
			#c.drawCentredString(421,25,'Pág. ' + str(pagina+1))
			return pagina+1,hReal-60
		else:
			return pagina,posactual-valor

