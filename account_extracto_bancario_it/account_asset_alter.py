# -*- coding: utf-8 -*-

from openerp import models, fields, api
import base64
from openerp.osv import osv
from openerp import netsvc

class extracto_bancario_linea(models.Model):
	_name = 'extracto.bancario.linea'

	ref_conciliacion = fields.Char('Referencia Conciliación')
	comprobante = fields.Char('Comprobante')
	periodo = fields.Many2one('account.period','Periodo')
	fecha = fields.Date('Fecha')
	debe = fields.Float('Debe',digits=(12,2))
	haber = fields.Float('Haber',digits=(12,2))
	saldo = fields.Float('Saldo')

	padre = fields.Many2one('extracto.bancario','Padre')



class extracto_bancario(models.Model):
	_name = 'extracto.bancario'

	codigo_banco = fields.Many2one('account.account', 'Cuenta Contable Bancaria',required=True)
	periodo = fields.Many2one('account.period','Periodo',required=True)
	moneda = fields.Selection([('soles','PEN'),('dolar','USD')],'Moneda',required=True,readonly=True,compute='get_codigo_banco')

	lineas = fields.One2many('extracto.bancario.linea','padre','Detalle',readonly=True)
	csv = fields.Binary(u'Csv Importación',help="Archivo CSV del Extracto Bancario separado por '|', con las columnas: Referencia Reconciliación, Comprobante, Periodo, Fecha, Debe, Haber")

	_rec_name = 'periodo'

	@api.onchange('codigo_banco')
	def onchange_codigo_banco(self):
		if self.codigo_banco.id:
			if self.codigo_banco.currency_id.id:
				self.moneda = 'dolar'
			else:
				self.moneda = 'soles'
		else:
			self.moneda = False

	@api.multi
	def get_codigo_banco(selfs):
		for self in selfs:
			if self.codigo_banco.id:
				if self.codigo_banco.currency_id.id:
					self.moneda = 'dolar'
				else:
					self.moneda = 'soles'
			else:
				self.moneda = False



	@api.one
	def importar(self):
		import base64 
		saldo = 0
		if self.csv:
			tmp = base64.decodestring(self.csv)
			linea = self.env['extracto.bancario.linea']
			alineas=linea.search([('padre','=',self.id)])
			for al in alineas:
				al.unlink()
			for i in tmp.split('\n'):
				elem = i.split('|')
				if len(elem) == 6:
					saldo += float(elem[5]) - float(elem[4])
					data = {
						'ref_conciliacion' :elem[0],
						'comprobante' :elem[1],
						'periodo' : self.env['account.period'].search([('code','=',elem[2])])[0].id,
						'fecha' : elem[3],
						'debe' : float(elem[4]),
						'haber' : float(elem[5]),
						'padre' : self.id,	 				
						'saldo' : saldo,
					}
					linea.create(data)

	@api.multi
	def generar_comparacion(self):
		cadsql="""
		select MT.ref_conci_eb,
		 	MT.fecha,
		 	MT.cheque,
		 	MT.nombre,
		 	MT.documento,
		 	MT.glosa,
		 	coalesce(MT.cargo_mn,0) as cargo_mn,
		 	coalesce(MT.abono_mn,0) as abono_mn,
		 	MT.tipo_cambio,
		 	coalesce(MT.cargo_me,0) as cargo_me,
		 	coalesce(MT.abono_me,0) as abono_me,
		 	MT.nro_asiento,
		 	MT.aa_id,
		 	MT.ordenamiento,
		 	MT.diario_id,

		 	j.ref_conciliacion,
			j.comprobante,
			j.fechaj,
			coalesce(j.debe,0) as debe,
			coalesce(j.haber,0) as haber,
			coalesce(j.saldo,0) as saldo 

		 	from (
			SELECT 
		 	am.ref_conci_eb,
		 	aml.date AS fecha,
		 	aml.nro_comprobante AS cheque,
		 	rp.name as nombre,
		 	am.name as documento,
		 	aml.name as glosa,
		 	aml.debit as cargo_mn,
		 	aml.credit as abono_mn,
		 	aml.currency_rate_it as tipo_cambio,
		 	CASE WHEN aml.amount_currency>0 THEN aml.amount_currency ELSE 0 END as cargo_me,
		 	CASE WHEN aml.amount_currency<0 THEN -1*aml.amount_currency ELSE 0 END as abono_me,
		 	am.id as nro_asiento,
		 	aa.id as aa_id,
		 	1 as ordenamiento,
		 	aj.id as diario_id
			FROM account_move_line aml
			 JOIN account_move am ON am.id = aml.move_id
			 JOIN account_journal aj ON aj.id = am.journal_id
			 JOIN account_period ap ON ap.id = am.period_id
			 JOIN account_account aa ON aa.id = aml.account_id
			 LEFT JOIN it_means_payment mp ON mp.id = aml.means_payment_id
			 LEFT JOIN res_currency rc ON rc.id = aml.currency_id
			 LEFT JOIN res_partner rp ON rp.id = aml.partner_id
			 LEFT JOIN it_type_document itd ON itd.id = aml.type_document_id
			 LEFT JOIN account_analytic_account aaa ON aaa.id = aml.analytic_account_id
		WHERE periodo_num(ap.name) = periodo_num('"""+self.periodo.code+"""') 
		and am.state = 'posted' 
		and aa.code = '"""+str(self.codigo_banco.code)+"""'

		union all

		SELECT 
 		'AP00'::varchar as ref_conci_eb,
 	 	Null::date AS fecha,
 	 	Null::varchar AS cheque,
 	 	Null::varchar AS nombre,
 	 	Null::varchar as documento,
 	 	'Saldo Inicial' as glosa,
 	 	sum(aml.debit) as cargo_mn,
 		sum(aml.credit) as abono_mn,
 	 	Null::numeric as tipo_cambio,
	 	
 	 	sum( CASE WHEN aml.amount_currency>0 THEN aml.amount_currency else 0 END ) as cargo_me,
 	 	sum( CASE WHEN aml.amount_currency<0 THEN -1* aml.amount_currency ELSE 0 END) as abono_me,
 	 	Null::integer as nro_asiento,
 	 	aa.id as aa_id,
 	 	0 as ordenamiento,
 	 	0 as diario_id

 		FROM account_move_line aml
 		 JOIN account_move am ON am.id = aml.move_id
 		 JOIN account_journal aj ON aj.id = am.journal_id
 		 JOIN account_period ap ON ap.id = am.period_id
 		 JOIN account_account aa ON aa.id = aml.account_id
 		 LEFT JOIN it_means_payment mp ON mp.id = aml.means_payment_id
 		 LEFT JOIN res_currency rc ON rc.id = aml.currency_id
 		 LEFT JOIN res_partner rp ON rp.id = aml.partner_id
 		 LEFT JOIN it_type_document itd ON itd.id = aml.type_document_id
 		 LEFT JOIN account_analytic_account aaa ON aaa.id = aml.analytic_account_id
 	WHERE periodo_num(ap.code) >= """+self.periodo.fiscalyear_id.name+"""00  and periodo_num(ap.code) < periodo_num('""" +self.periodo.code+ """') and aa.code = '"""+ str(self.codigo_banco.code)+"""'
 	and am.state != 'draft'
 	group by aa.id

		order by fecha ) MT
		full join 
		(select 
		ref_conciliacion as ref_conciliacionT,
		comprobante,
		fecha as fechaj,
		debe,
		haber,
		saldo 
		from extracto_bancario_linea 
		inner join extracto_bancario on extracto_bancario_linea.padre = extracto_bancario.id
		inner join account_period on extracto_bancario.periodo = account_period.id
		where extracto_bancario.periodo = """+str(self.periodo.id)+""" 
		and extracto_bancario.codigo_banco = """+str(self.codigo_banco.id)+"""
		and extracto_bancario.id = """ +str(self.id)+ """
		) j on MT.ref_conci_eb = j.ref_conciliacionT
		"""


		self.env.cr.execute(cadsql)
		datas=self.env.cr.dictfetchall()
		saldo = 0
		tabla_examinar = []
		for data in datas:
			tabla_examinar.append(data)

		a1 = 0 #saldo empresa
		a2 = 0 #ingresos que no estan en el banco
		a3 = 0 #egresos queno estan en la empresa
		a4 = 0 #egreso que no estan en le banco
		a5 = 0 #ingresos que no estan en la empresa
		for i in tabla_examinar:
			a1 += (i['cargo_mn']-i['abono_mn']) if self.moneda == 'soles' else (i['cargo_me']-i['abono_me'])
			if self.moneda == 'soles':
				if i['cargo_mn'] - i['abono_mn'] + i['debe'] - i['haber'] != 0:
					a2 += -(i['cargo_mn'])
					a3 += -(i['debe'])
					a4 += i['abono_mn']
					a5 += i['haber']
			else:
				if i['cargo_me'] - i['abono_me'] + i['debe'] - i['haber'] != 0:
					a2 += -(i['cargo_me'])
					a3 += -(i['debe'])			
					a4 += i['abono_me']
					a5 += i['haber']
		
		
		import io
		from xlsxwriter.workbook import Workbook
		output = io.BytesIO()
		
		########### PRIMERA HOJA DE LA DATA EN TABLA
		#workbook = Workbook(output, {'in_memory': True})
		
		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		if not direccion:
			raise osv.except_osv('Alerta!', "No fue configurado el directorio para los archivos en Configuración.")
		workbook = Workbook( direccion + 'tempo_account_move_line.xlsx')
		worksheet = workbook.add_worksheet("Extracto Bancario" )
		bold = workbook.add_format({'bold': True})
		normal = workbook.add_format()
		boldbord = workbook.add_format({'bold': True})
		boldbord.set_border(style=2)
		numbertres = workbook.add_format({'num_format':'0.000'})
		numberdos = workbook.add_format({'num_format':'0.00'})
		bord = workbook.add_format()
		bord.set_border(style=1)
		boldbord = workbook.add_format({'bold': True})
		boldbord.set_border(style=2)
		boldbord.set_align('center')
		boldbord.set_align('vcenter')
		boldbord.set_text_wrap()
		boldbord.set_font_size(9)
		boldbord.set_bg_color('#DCE6F1')
		#numberdos.set_border(style=1)
		numbertres.set_border(style=1)			
		x= 6				
		tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
		tam_letra = 1.1
		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')

		worksheet.merge_range(1,1,1,5, u"Conciliación Bancaria", boldbord)
		worksheet.write(3,1,'Empresa:',bold)
		worksheet.write(3,2,self.env['res.company'].search([])[0].name,normal)

		worksheet.write(4,1,'Banco:',bold)	
		worksheet.write(4,2, self.codigo_banco.cashbank_financy if self.codigo_banco.cashbank_financy else '',normal)

		worksheet.write(5,1,'Cta Cont.:',bold)
		worksheet.write(5,2,self.codigo_banco.code + '-'+ self.codigo_banco.name,normal)
		worksheet.write(6,1,'# Cta Corriente:',bold)
		worksheet.write(6,2,self.codigo_banco.cashbank_number if self.codigo_banco.cashbank_number else '',normal)

		worksheet.write(3,4,'Fecha:',bold)
		import datetime
		worksheet.write(3,5,str(datetime.datetime.now())[:10],normal)
		worksheet.write(4,4,'Saldo Extracto Banco:',bold)
		worksheet.write(5,4,'Saldo Cta. Contable:',bold)
		
		worksheet.write(4,5,a1,numberdos)
		worksheet.write(5,5,a1+a2+a3+a4+a5,numberdos)
		
		worksheet.write(9,1,'a) Pagos Banco no Contabilidad',bold)
		worksheet.write(10,1,'b) Cobros Banco no Contabilidad',bold)
		worksheet.write(11,1,'c) Pagos Contabilidad no Banco',bold)
		worksheet.write(12,1,'d) Cobros Contabilidad no Banco',bold)
		

		worksheet.write(9,3, a4 ,numberdos)
		worksheet.write(10,3, -a2 ,numberdos)
		worksheet.write(11,3, -a3 ,numberdos)
		worksheet.write(12,3, a5 ,numberdos)

		worksheet.merge_range(15,1,15,5,'a) Pagos Banco no Contabilidad',boldbord)
		worksheet.write(17,1,'Fecha',boldbord)
		worksheet.write(17,2,'Concepto',boldbord)
		worksheet.write(17,3,'Importe',boldbord)
		worksheet.write(17,4,'Comprobante',boldbord)
		worksheet.write(17,5,u'Clave Conciliación',boldbord)

		pos =18
		for i in tabla_examinar:
			if self.moneda == 'soles':
				if i['cargo_mn'] - i['abono_mn'] + i['debe'] - i['haber'] != 0:
					if i['abono_mn'] != 0:
						worksheet.write(pos,1,i['fecha'],normal)
						worksheet.write(pos,2,i['glosa'],normal)
						worksheet.write(pos,3,i['abono_mn'],numberdos)
						worksheet.write(pos,4,i['cheque'],normal)
						worksheet.write(pos,5,i['ref_conci_eb'],normal)
						pos+=1
			else:
				if i['cargo_me'] - i['abono_me'] + i['debe'] - i['haber'] != 0:
					if i['abono_me'] != 0:
						worksheet.write(pos,1,i['fecha'],normal)
						worksheet.write(pos,2,i['glosa'],normal)
						worksheet.write(pos,3,i['abono_me'],numberdos)
						worksheet.write(pos,4,i['cheque'],normal)
						worksheet.write(pos,5,i['ref_conci_eb'],normal)
						pos+=1

		worksheet.write(pos,2,'Total',bold)
		worksheet.write(pos,3,a4,numberdos)
		pos +=2


		worksheet.merge_range(pos,1,pos,5,'b) Cobros Banco no Contabilidad',boldbord)
		pos+=2
		worksheet.write(pos,1,'Fecha',boldbord)
		worksheet.write(pos,2,'Concepto',boldbord)
		worksheet.write(pos,3,'Importe',boldbord)
		worksheet.write(pos,4,'Comprobante',boldbord)
		worksheet.write(pos,5,u'Clave Conciliación',boldbord)

		pos +=1
		for i in tabla_examinar:
			if self.moneda == 'soles':
				if i['cargo_mn'] - i['abono_mn'] + i['debe'] - i['haber'] != 0:
					if i['cargo_mn']!= 0:
						worksheet.write(pos,1,i['fecha'],normal)
						worksheet.write(pos,2,i['glosa'],normal)
						worksheet.write(pos,3,i['cargo_mn'],numberdos)
						worksheet.write(pos,4,i['cheque'],normal)
						worksheet.write(pos,5,i['ref_conci_eb'],normal)
						pos+=1
			else:
				if i['cargo_me'] - i['abono_me'] + i['debe'] - i['haber'] != 0:
					if i['cargo_me'] != 0:
						worksheet.write(pos,1,i['fecha'],normal)
						worksheet.write(pos,2,i['glosa'],normal)
						worksheet.write(pos,3,i['cargo_me'],numberdos)
						worksheet.write(pos,4,i['cheque'],normal)
						worksheet.write(pos,5,i['ref_conci_eb'],normal)
						pos+=1

		worksheet.write(pos,2,'Total',bold)
		worksheet.write(pos,3,-a2,numberdos)
		pos += 2


		worksheet.merge_range(pos,1,pos,5,'c) Pagos Contabilidad no Banco',boldbord)
		pos+=2
		worksheet.write(pos,1,'Fecha',boldbord)
		worksheet.write(pos,2,'Concepto',boldbord)
		worksheet.write(pos,3,'Importe',boldbord)
		worksheet.write(pos,4,'Comprobante',boldbord)
		worksheet.write(pos,5,u'Clave Conciliación',boldbord)

		pos +=1
		for i in tabla_examinar:
			if self.moneda == 'soles':
				if i['cargo_mn'] - i['abono_mn'] + i['debe'] - i['haber'] != 0:
					if i['debe']  != 0:
						worksheet.write(pos,1,i['fechaj'],normal)
						worksheet.write(pos,3,i['debe'],numberdos)
						worksheet.write(pos,4,i['comprobante'],normal)
						worksheet.write(pos,5,i['ref_conciliacion'],normal)
						pos+=1
			else:
				if i['cargo_me'] - i['abono_me'] + i['debe'] - i['haber'] != 0:
					if i['debe']  != 0:
						worksheet.write(pos,1,i['fechaj'],normal)
						worksheet.write(pos,3,i['debe'],numberdos)
						worksheet.write(pos,4,i['comprobante'],normal)
						worksheet.write(pos,5,i['ref_conciliacion'],normal)
						pos+=1

		worksheet.write(pos,2,'Total',bold)
		worksheet.write(pos,3,-a3,numberdos)
		pos += 2


		worksheet.merge_range(pos,1,pos,5,'d) Cobros Contabilidad no Banco',boldbord)
		pos+=2
		worksheet.write(pos,1,'Fecha',boldbord)
		worksheet.write(pos,2,'Concepto',boldbord)
		worksheet.write(pos,3,'Importe',boldbord)
		worksheet.write(pos,4,'Comprobante',boldbord)
		worksheet.write(pos,5,u'Clave Conciliación',boldbord)

		pos +=1
		for i in tabla_examinar:
			if self.moneda == 'soles':
				if i['cargo_mn'] - i['abono_mn'] + i['debe'] - i['haber'] != 0:
					if i['haber'] != 0:
						worksheet.write(pos,1,i['fechaj'],normal)
						worksheet.write(pos,3,i['haber'],numberdos)
						worksheet.write(pos,4,i['comprobante'],normal)
						worksheet.write(pos,5,i['ref_conciliacion'],normal)
						pos+=1
			else:
				if i['cargo_me'] - i['abono_me'] + i['debe'] - i['haber'] != 0:
					if i['haber'] != 0:
						worksheet.write(pos,1,i['fechaj'],normal)
						worksheet.write(pos,3,i['haber'],numberdos)
						worksheet.write(pos,4,i['comprobante'],normal)
						worksheet.write(pos,5,i['ref_conciliacion'],normal)
						pos+=1

		worksheet.write(pos,2,'Total',bold)
		worksheet.write(pos,3,a5,numberdos)
		pos += 2


		worksheet.set_column('A:A', 8.43)
		worksheet.set_column('B:B', 16)
		worksheet.set_column('C:C', 23)
		worksheet.set_column('D:D', 28)
		worksheet.set_column('E:E', 28)
		worksheet.set_column('F:F', 28)


		workbook.close()
		
		f = open( direccion + 'tempo_account_move_line.xlsx', 'rb')
		
		
		sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
		vals = {
			'output_name': 'AsientoContable.xlsx',
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

class account_move(models.Model):
	_inherit = 'account.move'

	ref_conci_eb = fields.Char(u'Referencia Conciliación E.B.')


class account_voucher(models.Model):
	_inherit = 'account.voucher'

	ref_conci_eb = fields.Char(u'Referencia Conciliación E.B.')

	@api.one
	def write(self,vals):
		t = super(account_voucher,self).write(vals)
		self.refresh()
		if self.move_id.id:
			self.move_id.write({'ref_conci_eb':self.ref_conci_eb})
		return t

	@api.one
	def proforma_voucher(self):
		t = super(account_voucher,self).proforma_voucher()
		self.refresh()
		if self.move_id.id:
			self.move_id.write({'ref_conci_eb':self.ref_conci_eb})
		return t