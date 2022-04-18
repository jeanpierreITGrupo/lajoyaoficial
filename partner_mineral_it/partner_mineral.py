# -*- encoding: utf-8 -*-

from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
import pprint

class res_partner(models.Model):
	_inherit = 'res.partner'

	tipo_proveedor = fields.Selection([('Mineral','Mineral'),('Otros','Otros')],"Tipo de Proveedor")
	






class account_contable_fch_wizard(osv.TransientModel):
	_inherit ='account.contable.fch.wizard'
	

	type_partner = fields.Selection([('Mineral','Mineral'),('Otros','Otros')],'Tipo Partner')

	@api.onchange('type_partner')
	def _onchange_type_partner(self):
		if self.type_partner:
			return {'domain':{'partner_id':[('tipo_proveedor','=',self.type_partner)]}}			
		else:
			return {'domain':{'partner_id':[]}}

	@api.multi
	def do_rebuild(self):		
		tipef = self.type_account
		cont_txt = ''
		con_elem = 0


		if self.partner_id:
			cont_txt += ( ' and ' if con_elem > 0 else ' ') + "partner = '" + self.partner_id.name + "' "
			con_elem += 1
			#filtro.append( ('partner','=',self.partner_id.name) )

		cuenta_txt = ' '

		if self.cuenta_id:
			cuenta_txt = " and cuentas.code = '" + self.cuenta_id.code + "' "
			#filtro.append( ('cuenta','=',self.cuenta_id.code) )

		tipo_filtro_def = " cuentas.type='payable' or cuentas.type='receivable' "
		if str(tipef) == 'cc1':
			tipo_filtro_def = " cuentas.type='payable' "
			#filtro.append( ('tipofiltro','=','payable') )
		if str(tipef) == 'cc2':
			tipo_filtro_def = " cuentas.type='receivable' "
			#filtro.append( ('tipofiltro','=','receivable') )

		if self.pendiente:
			cont_txt += ( ' and ' if con_elem > 0 else ' ') + "saldo_filter != 0 "
			con_elem += 1
			#filtro.append( ('saldo_filter','!=',0) )

		if con_elem > 0:
			cont_txt = ' where ' + cont_txt
		
		partnerwhere = ''
		if self.type_partner:
			partnerwhere = " where t6.tipo_proveedor = '"+self.type_partner+"'"


		self.env.cr.execute(""" 

			DROP VIEW IF EXISTS account_contable_period;
			create or replace view account_contable_period as (

select * from ( 
select 
t0.id ,
t0.ide,
t4.code as periodo,
t5.code as libro,
t2.name as voucher,
t6.name as partner,
t6.type_number as ruc,
t7.code as type_document,
t0.nro_comprobante as comprobante,
t3.code as cuenta,
t2.date as fecha,
t0.debit as debe,
t0.credit as haber,
t1.saldo as saldo_filter,
t3.type as tipofiltro
from 
(
select ab.id,concat(ab.partner_id,ab.account_id,ab.type_document_id,ab.nro_comprobante)as ide,ab.move_id,ab.partner_id,ab.account_id,ab.type_document_id,ab.nro_comprobante,ab.debit,ab.credit from account_move_line ab
left join account_account cuentas on cuentas.id=ab.account_id
left join account_move am on ab.move_id = am.id
left join account_period ap on ap.id = am.period_id
where ( """ +tipo_filtro_def+ """ ) and am.state != 'draft' and cuentas.reconcile=TRUE  """ +cuenta_txt+ """
-------------- colocar en estas lineas la condicion de los periodos inicial y final ------------------------------
and (ap.id in (select id from account_period where periodo_num(code)>= periodo_num('""" + self.period_ini.code +"""') and periodo_num(code) <= periodo_num('""" + self.period_end.code + """') ) ) 

----------------------------------------------------------------------------------------------------

) t0


left join (

select concat(xx.partner_id,xx.account_id,xx.type_document_id,xx.nro_comprobante)as ide,sum(debit)-sum(credit) as saldo from account_move_line xx
left join account_account cuentas on cuentas.id=xx.account_id
left join account_move am on am.id = xx.move_id
left join account_period ap on ap.id = am.period_id
where ( """ +tipo_filtro_def+ """ ) and cuentas.reconcile=TRUE  """ +cuenta_txt+ """

-------------- colocar en estas lineas la condicion de los periodos  inicial y final ------------------------------
and ( periodo_num(ap.code)>= periodo_num('""" + self.period_ini.code +"""') and periodo_num(ap.code) <= periodo_num('""" + self.period_end.code + """') )

----------------------------------------------------------------------------------------------------

group by concat(xx.partner_id,xx.account_id,xx.type_document_id,xx.nro_comprobante) 

) t1 on t1.ide=t0.ide

left join account_move t2 on t2.id=t0.move_id
left join account_account t3 on t3.id=t0.account_id
left join account_period t4 on t4.id=t2.period_id
left join account_journal t5 on t5.id=t2.journal_id 
left join res_partner t6 on t6.id=t0.partner_id
left join it_type_document t7 on t7.id=t0.type_document_id
""" + partnerwhere+  """
order by partner,cuenta,type_document,comprobante,fecha
)TT """ + cont_txt + """
			)""")

		print "llegue feliz y contento"

		move_obj = self.env['account.contable.period']
		filtro = []


		lstidsmove= move_obj.search(filtro)
		
		if (len(lstidsmove) == 0):
			raise osv.except_osv('Alerta','No contiene datos.')
		
		if self.type_show == 'pantalla':
			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window'] 

			result = mod_obj.get_object_reference('repaccount_contable_period_it', 'account_contable_period_action')
			
			id = result[1]
			
			return {
				'domain' : filtro,
				'type': 'ir.actions.act_window',
				'res_model': 'account.contable.period',
				'view_mode': 'tree',
				'view_type': 'form',
				'res_id': id,
				'views': [(False, 'tree')],
			}

		else:

			import io
			from xlsxwriter.workbook import Workbook
			output = io.BytesIO()
			########### PRIMERA HOJA DE LA DATA EN TABLA
			#workbook = Workbook(output, {'in_memory': True})
			direccion = self.env['main.parameter'].search([])[0].dir_create_file
			workbook = Workbook( direccion + 'tempo_cuentacorriente.xlsx')
			worksheet = workbook.add_worksheet("Cuenta Corriente")
			bold = workbook.add_format({'bold': True})
			normal = workbook.add_format()
			boldbord = workbook.add_format({'bold': True})
			boldbord.set_border(style=2)
			boldbord.set_align('center')
			boldbord.set_align('vcenter')
			boldbord.set_text_wrap()
			boldbord.set_font_size(9)
			boldbord.set_bg_color('#DCE6F1')


			title = workbook.add_format({'bold': True})
			title.set_align('center')
			title.set_align('vcenter')
			title.set_text_wrap()
			title.set_font_size(18)
			numbertres = workbook.add_format({'num_format':'0.000'})
			numberdos = workbook.add_format({'num_format':'0.00'})
			bord = workbook.add_format()
			bord.set_border(style=1)
			numberdos.set_border(style=1)
			numbertres.set_border(style=1)			
			x= 5				
			tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			tam_letra = 1.2
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')


			worksheet.merge_range(0,0,0,15,"Cuenta Corriente",title)

			worksheet.write(1,0, "Cuenta Corriente:", bold)
			
			worksheet.write(1,1, self.period_ini.name, normal)
			
			worksheet.write(1,2, self.period_end.name, normal)
			
			worksheet.write(2,0, "Fecha:",bold)
			
			#worksheet.write(1,1, total.date.strftime('%Y-%m-%d %H:%M'),bord)
			import datetime
			worksheet.write(2,1, str(datetime.datetime.today())[:10], normal)
			

			worksheet.write(4,0, "Periodo",boldbord)
			
			worksheet.write(4,1, "Libro",boldbord)
			worksheet.write(4,2, "Voucher",boldbord)
			worksheet.write(4,3, u"RUC",boldbord)

			worksheet.write(4,4, u"Partner",boldbord)
			worksheet.write(4,5, "Tipo Doc.",boldbord)

			worksheet.write(4,6, "Comprobante",boldbord)
			worksheet.write(4,7, u"Fecha",boldbord)
			worksheet.write(4,8, "Cuenta",boldbord)
			worksheet.write(4,9, "Debe",boldbord)
			worksheet.write(4,10, u"Haber",boldbord)
			worksheet.write(4,11, u"Saldo.",boldbord)


			for line in lstidsmove:
				worksheet.write(x,0,line.periodo if line.periodo else '' ,bord )
				worksheet.write(x,1,line.libro if line.libro  else '',bord )
				worksheet.write(x,2,line.voucher if line.voucher  else '',bord)
				worksheet.write(x,3,line.ruc if line.ruc else '',bord)
				worksheet.write(x,4,line.partner if line.partner else '',bord)
				worksheet.write(x,5,line.type_document if line.type_document else '',bord)
				worksheet.write(x,6,line.comprobante if line.comprobante else '',bord)
				worksheet.write(x,7,line.fecha if line.fecha  else '',bord)
				worksheet.write(x,8,line.cuenta if line.cuenta  else '',bord)
				worksheet.write(x,9,line.debe ,numberdos)
				worksheet.write(x,10,line.haber ,numberdos)
				worksheet.write(x,11,line.saldo ,numberdos)
				
				x = x +1

			tam_col = [16.14,7,12.2,13.5,26,3.5,16,14,14,11,11,11,8,11,9,10]
			worksheet.set_row(0, 30)

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

			workbook.close()
			
			f = open(direccion + 'tempo_cuentacorriente.xlsx', 'rb')
			
			
			sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
			vals = {
				'output_name': 'CuentaCorriente.xlsx',
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

		


class saldo_comprobante_empresa_wizard(osv.TransientModel):
	_inherit='saldo.comprobante.empresa.wizard'



	type_partner = fields.Selection([('Mineral','Mineral'),('Otros','Otros')],'Tipo Partner')

	@api.onchange('type_partner')
	def _onchange_type_partner(self):
		if self.type_partner:
			return {'domain':{'empresa':[('tipo_proveedor','=',self.type_partner)]}}			
		else:
			return {'domain':{'empresa':[]}}



	@api.multi
	def do_rebuild(self):		


		partnerwhere = ''
		if self.type_partner:
			partnerwhere = " where t3.tipo_proveedor = '"+self.type_partner+"'"

		self.env.cr.execute("""  DROP VIEW IF EXISTS saldo_comprobante_empresa;
			create or replace view saldo_comprobante_empresa as (

select t1.id as id, ap.name as periodo,t3.type_number as ruc,t3.name as empresa,t4.code as code,t4.name as descripcion,
CASE WHEN t4.type= 'payable' THEN 'A pagar'  ELSE 'A cobrar' END as tipo_cuenta
,t_debe as debe,t_haber as haber,t_debe-t_haber as saldo  from ( 
select min(aml.id) as id, concat(aml.partner_id,aml.account_id) as identificador,sum(aml.debit) as t_debe,sum(aml.credit) as t_haber from account_move_line aml
inner join account_move am on am.id = aml.move_id
inner join account_period api on api.id = am.period_id
inner join account_account aa on aa.id = aml.account_id
where aa.reconcile = true and periodo_num(api.code) >= periodo_num('""" + str(self.periodo_ini.code) + """') and periodo_num(api.code) <= periodo_num('""" + str(self.periodo_fin.code) + """')
and am.state != 'draft'
group by identificador) t1

left join account_move_line t2 on t2.id=t1.id
left join account_move am on am.id = t2.move_id
left join account_period ap on ap.id = am.period_id
left join res_partner t3 on t3.id=t2.partner_id
left join account_account t4 on t4.id=t2.account_id

""" + partnerwhere+  """

order by code,empresa

						)""")
		filtro = []
		if self.check== True:
			filtro.append( ('saldo','!=',0) )
		if self.cuenta.id:
			filtro.append( ('code','=', self.cuenta.code ) )

		if self.empresa.id:
			filtro.append( ('empresa','=', self.empresa.name ) )

		if self.tipo:
			filtro.append( ('tipo_cuenta','=',self.tipo) )

		move_obj = self.env['saldo.comprobante.empresa']
		lstidsmove= move_obj.search(filtro)		
		if (len(lstidsmove) == 0):
			raise osv.except_osv('Alerta','No contiene datos.')		

		if self.mostrar == 'pantalla':
			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']			
			return {
				'domain' : filtro,
				'type': 'ir.actions.act_window',
				'res_model': 'saldo.comprobante.empresa',
				'view_mode': 'tree',
				'view_type': 'form',
				'views': [(False, 'tree')],
			}

			
		if self.mostrar == 'excel':
			import io
			from xlsxwriter.workbook import Workbook
			output = io.BytesIO()
			########### PRIMERA HOJA DE LA DATA EN TABLA
			#workbook = Workbook(output, {'in_memory': True})

			direccion = self.env['main.parameter'].search([])[0].dir_create_file

			workbook = Workbook(direccion +'saldoperiodo.xlsx')
			worksheet = workbook.add_worksheet("Analisis Saldo x Empresa")
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


			title = workbook.add_format({'bold': True})
			title.set_align('center')
			title.set_align('vcenter')
			title.set_text_wrap()
			title.set_font_size(18)
			worksheet.set_row(0, 30)

			x= 9				
			tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			tam_letra = 1.2
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')

			worksheet.merge_range(0,0,0,8, u"Análisis de Saldos x Empresa", title)

			worksheet.write(1,0, u"Año Fiscal", bold)
			worksheet.write(1,1, self.fiscal_id.name, normal)

			worksheet.write(2,0, u"Periodo Inicial", bold)
			worksheet.write(2,1, self.periodo_ini.name, normal)

			worksheet.write(3,0, u"Periodo Final", bold)
			worksheet.write(3,1, self.periodo_fin.name, normal)

			worksheet.write(4,0, u"Solo Pendientes", bold)
			worksheet.write(4,1, 'Si' if self.check else 'No', normal)

			worksheet.write(5,0, u"Empresa", bold)
			worksheet.write(5,1, self.empresa.name if self.empresa.name else '', normal)

			worksheet.write(6,0, u"Cuenta", bold)
			worksheet.write(6,1, self.cuenta.name if self.cuenta.name else '', normal)


			worksheet.write(8,0, "Periodo",boldbord)
			worksheet.write(8,1, "Empresa",boldbord)
			worksheet.write(8,2, "RUC",boldbord)
			worksheet.write(8,3, "Tipo Cuenta",boldbord)
			worksheet.write(8,4, u"Cuenta",boldbord)
			worksheet.write(8,5, u"Descripción",boldbord)
			worksheet.write(8,6, "Debe",boldbord)
			worksheet.write(8,7, "Haber",boldbord)
			worksheet.write(8,8, "Saldo",boldbord)




			for line in self.env['saldo.comprobante.empresa'].search(filtro):
				worksheet.write(x,0,line.periodo if line.periodo else '' ,bord )
				worksheet.write(x,1,line.empresa if line.empresa  else '',bord )
				worksheet.write(x,2,line.ruc if line.ruc  else '',bord)
				worksheet.write(x,3,line.tipo_cuenta if line.tipo_cuenta  else '',bord)
				worksheet.write(x,4,line.code if line.code  else '',bord)
				worksheet.write(x,5,line.descripcion if line.descripcion  else '',bord)
				worksheet.write(x,6,line.debe ,numberdos)
				worksheet.write(x,7,line.haber ,numberdos)
				worksheet.write(x,8,line.saldo ,numberdos)

				x = x +1

			tam_col = [11,6,8.8,7.14,38,11,11,11,10,11,14,10,11,14,14,10,16,16,20,36]


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

			workbook.close()
			
			f = open(direccion + 'saldoperiodo.xlsx', 'rb')
			
			
			sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
			vals = {
				'output_name': 'SaldoEmpresa.xlsx',
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




class saldo_comprobante_wizard(osv.TransientModel):
	_inherit='saldo.comprobante.wizard'






	type_partner = fields.Selection([('Mineral','Mineral'),('Otros','Otros')],'Tipo Partner')

	@api.onchange('type_partner')
	def _onchange_type_partner(self):
		if self.type_partner:
			return {'domain':{'empresa':[('tipo_proveedor','=',self.type_partner)]}}			
		else:
			return {'domain':{'empresa':[]}}



	@api.multi
	def do_rebuild(self):

		partnerwhere = ''
		if self.type_partner:
			partnerwhere = " where rp.tipo_proveedor = '"+self.type_partner+"'"

		self.env.cr.execute("""  DROP VIEW IF EXISTS saldo_comprobante;
			create or replace view saldo_comprobante as (

select row_number() OVER () AS id,* from
(
	select 
am.date as fecha_emision,
rp.type_number as ruc,
rp.name as empresa,
CASE WHEN aa.type= 'payable' THEN 'A pagar'  ELSE 'A cobrar' END as tipo_cuenta,
aa.code,
itd.code as tipo,
aml.nro_comprobante as nro_comprobante,
T.debe,
T.haber,
T.saldo,
rc.name as divisa,
T.amount_currency
from (
select concat(account_move_line.partner_id,account_id,type_document_id,nro_comprobante) as identifica,min(account_move_line.id),sum(debit)as debe,sum(credit) as haber, sum(debit)-sum(credit) as saldo, sum(amount_currency) as amount_currency from account_move_line
inner join account_move ami on ami.id = account_move_line.move_id
left join account_account on account_account.id=account_move_line.account_id
where (account_account.type='receivable' or account_account.type='payable' ) and account_account.reconcile = true
and ami.date >= '""" + str(self.fecha_ini) + """' and ami.date <= '""" + str(self.fecha_fin) + """' and ami.state != 'draft'
group by identifica) as T
inner join account_move_line aml on aml.id = T.min
inner join account_move am on am.id = aml.move_id
left join res_partner rp on rp.id = aml.partner_id
left join it_type_document itd on itd.id = aml.type_document_id
left join res_currency rc on rc.id = aml.currency_id
left join account_account aa on aa.id = aml.account_id
""" + partnerwhere+  """

order by empresa, code, nro_comprobante
) T

						)""")
		filtro = []

		if self.check == True:
			filtro.append( ('saldo','!=',0) )
		if self.cuenta.id:
			filtro.append( ('code','=', self.cuenta.code ) )

		if self.empresa.id:
			filtro.append( ('empresa','=', self.empresa.name ) )

		if self.tipo:
			filtro.append( ('tipo_cuenta','=',self.tipo) )

		move_obj = self.env['saldo.comprobante']
		lstidsmove= move_obj.search(filtro)		
		if (len(lstidsmove) == 0):
			raise osv.except_osv('Alerta','No contiene datos.')		

		if self.mostrar == 'pantalla':

			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']			
			return {
				'domain' : filtro,
				'type': 'ir.actions.act_window',
				'res_model': 'saldo.comprobante',
				'view_mode': 'tree',
				'view_type': 'form',
				'views': [(False, 'tree')],
			}

		
		if self.mostrar == 'excel':
			import io
			from xlsxwriter.workbook import Workbook
			output = io.BytesIO()
			########### PRIMERA HOJA DE LA DATA EN TABLA
			#workbook = Workbook(output, {'in_memory': True})

			direccion = self.env['main.parameter'].search([])[0].dir_create_file

			workbook = Workbook(direccion +'saldoperiodo.xlsx')
			worksheet = workbook.add_worksheet("Analisis Saldo x Periodo")
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

			title = workbook.add_format({'bold': True})
			title.set_align('center')
			title.set_align('vcenter')
			title.set_text_wrap()
			title.set_font_size(18)
			worksheet.set_row(0, 30)

			x= 10				
			tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			tam_letra = 1.2
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')

			worksheet.merge_range(0,0,0,10, u"Análisis de Saldos x Fecha", title)


			worksheet.write(2,0, u"Fecha Inicial", bold)
			worksheet.write(2,1, self.fecha_ini, normal)

			worksheet.write(3,0, u"Fecha Final", bold)
			worksheet.write(3,1, self.fecha_fin, normal)

			worksheet.write(4,0, u"Solo Pendientes", bold)
			worksheet.write(4,1, 'Si' if self.check else 'No', normal)

			worksheet.write(5,0, u"Empresa", bold)
			worksheet.write(5,1, self.empresa.name if self.empresa.name else '', normal)

			worksheet.write(6,0, u"Cuenta", bold)
			worksheet.write(6,1, self.cuenta.name if self.cuenta.name else '', normal)

			worksheet.write(7,0, u"Tipo", bold)
			worksheet.write(7,1, self.tipo if self.tipo else '', normal)


			worksheet.write(9,0, "Fecha Emisión",boldbord)
			worksheet.write(9,1, "Empresa",boldbord)
			worksheet.write(9,2, "Tipo Cuenta",boldbord)
			worksheet.write(9,3, u"Cuenta",boldbord)
			worksheet.write(9,4, "Tipo Documento",boldbord)
			worksheet.write(9,5, "Nro. Comprobante",boldbord)
			worksheet.write(9,6, "Debe",boldbord)
			worksheet.write(9,7, "Haber",boldbord)
			worksheet.write(9,8, "Saldo",boldbord)
			worksheet.write(9,9, "Divisa",boldbord)
			worksheet.write(9,10, u"Importe",boldbord)


			for line in self.env['saldo.comprobante'].search(filtro):
				worksheet.write(x,0,line.fecha_emision if line.fecha_emision  else '',bord )
				worksheet.write(x,1,line.empresa if line.empresa  else '',bord)
				worksheet.write(x,2,line.tipo_cuenta if line.tipo_cuenta  else '',bord)
				worksheet.write(x,3,line.code if line.code  else '',bord)
				worksheet.write(x,4,line.tipo if line.tipo  else '',bord)
				worksheet.write(x,5,line.nro_comprobante if line.nro_comprobante  else '',bord)
				worksheet.write(x,6,line.debe ,numberdos)
				worksheet.write(x,7,line.haber ,numberdos)
				worksheet.write(x,8,line.saldo ,numberdos)
				worksheet.write(x,9,line.divisa if  line.divisa else '',bord)
				worksheet.write(x,10,line.amount_currency ,numberdos)

				x = x +1

			tam_col = [11,6,8.8,7.14,38,11,11,11,10,11,14,10,11,14,14,10,16,16,20,36]


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

			workbook.close()
			
			f = open(direccion + 'saldoperiodo.xlsx', 'rb')
			
			
			sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
			vals = {
				'output_name': 'SaldoFecha.xlsx',
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


	

class saldo_comprobante_periodo_wizard(osv.TransientModel):
	_inherit='saldo.comprobante.periodo.wizard'


	type_partner = fields.Selection([('Mineral','Mineral'),('Otros','Otros')],'Tipo Partner')

	@api.onchange('type_partner')
	def _onchange_type_partner(self):
		if self.type_partner:
			return {'domain':{'empresa':[('tipo_proveedor','=',self.type_partner)]}}			
		else:
			return {'domain':{'empresa':[]}}



	@api.multi
	def do_rebuild(self):	

		partnerwhere = ''
		if self.type_partner:
			partnerwhere = " where rp.tipo_proveedor = '"+self.type_partner+"'"

		self.env.cr.execute("""  DROP VIEW IF EXISTS saldo_comprobante_periodo;
			create or replace view saldo_comprobante_periodo as (

select row_number() OVER () AS id,* from
(
	select 
ap.name as periodo,
am.date as fecha_emision,
rp.type_number as ruc,
rp.name as empresa,
CASE WHEN aa.type= 'payable' THEN 'A pagar'  ELSE 'A cobrar' END as tipo_cuenta,
aa.code,
itd.code as tipo,
aml.nro_comprobante as nro_comprobante,
T.debe,
T.haber,
T.saldo,
rc.name as divisa,
T.amount_currency
from (
select concat(account_move_line.partner_id,account_id,type_document_id,nro_comprobante) as identifica,min(account_move_line.id),sum(debit)as debe,sum(credit) as haber, sum(debit)-sum(credit) as saldo, sum(amount_currency) as amount_currency from account_move_line
inner join account_move ami on ami.id = account_move_line.move_id
inner join account_period api on api.id = ami.period_id
left join account_account on account_account.id=account_move_line.account_id
where account_account.reconcile = true and (account_account.type='receivable' or account_account.type='payable' ) and ami.state != 'draft'
and periodo_num(api.code) >= periodo_num('""" + str(self.periodo_ini.code) + """') and periodo_num(api.code) <= periodo_num('""" + str(self.periodo_fin.code) + """')
group by identifica) as T
inner join account_move_line aml on aml.id = T.min
inner join account_move am on am.id = aml.move_id
inner join account_period ap on ap.id = am.period_id
left join res_partner rp on rp.id = aml.partner_id
left join it_type_document itd on itd.id = aml.type_document_id
left join res_currency rc on rc.id = aml.currency_id
left join account_account aa on aa.id = aml.account_id
""" + partnerwhere+  """
order by empresa, code, nro_comprobante
) T

						)""")
		filtro = []
		if self.check== True:
			filtro.append( ('saldo','!=',0) )
		if self.cuenta.id:
			filtro.append( ('code','=', self.cuenta.code ) )

		if self.empresa.id:
			filtro.append( ('empresa','=', self.empresa.name ) )

		if self.tipo:
			filtro.append( ('tipo_cuenta','=',self.tipo) )

		move_obj = self.env['saldo.comprobante.periodo']
		lstidsmove= move_obj.search(filtro)		
		if (len(lstidsmove) == 0):
			raise osv.except_osv('Alerta','No contiene datos.')		

		if self.mostrar == 'pantalla':
			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']			
			return {
				'domain' : filtro,
				'type': 'ir.actions.act_window',
				'res_model': 'saldo.comprobante.periodo',
				'view_mode': 'tree',
				'view_type': 'form',
				'views': [(False, 'tree')],
			}

			
		if self.mostrar == 'excel':
			import io
			from xlsxwriter.workbook import Workbook
			output = io.BytesIO()
			########### PRIMERA HOJA DE LA DATA EN TABLA
			#workbook = Workbook(output, {'in_memory': True})

			direccion = self.env['main.parameter'].search([])[0].dir_create_file

			workbook = Workbook(direccion +'saldoperiodo.xlsx')
			worksheet = workbook.add_worksheet("Analisis Saldo x Periodo")
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


			title = workbook.add_format({'bold': True})
			title.set_align('center')
			title.set_align('vcenter')
			title.set_text_wrap()
			title.set_font_size(18)
			worksheet.set_row(0, 30)

			x= 10				
			tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			tam_letra = 1.2
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')

			worksheet.merge_range(0,0,0,11, u"Análisis de Saldos x Periodo", title)

			worksheet.write(1,0, u"Año Fiscal", bold)
			worksheet.write(1,1, self.fiscal_id.name, normal)

			worksheet.write(2,0, u"Periodo Inicial", bold)
			worksheet.write(2,1, self.periodo_ini.name, normal)

			worksheet.write(3,0, u"Periodo Final", bold)
			worksheet.write(3,1, self.periodo_fin.name, normal)

			worksheet.write(4,0, u"Solo Pendientes", bold)
			worksheet.write(4,1, 'Si' if self.check else 'No', normal)

			worksheet.write(5,0, u"Empresa", bold)
			worksheet.write(5,1, self.empresa.name if self.empresa.name else '', normal)

			worksheet.write(6,0, u"Cuenta", bold)
			worksheet.write(6,1, self.cuenta.name if self.cuenta.name else '', normal)

			worksheet.write(7,0, u"Tipo", bold)
			worksheet.write(7,1, self.tipo if self.tipo else '', normal)


			worksheet.write(9,0, "Periodo",boldbord)
			worksheet.write(9,1, "Fecha Emisión",boldbord)
			worksheet.write(9,2, "Empresa",boldbord)
			worksheet.write(9,3, "Ruc",boldbord)
			worksheet.write(9,4, "Tipo Cuenta",boldbord)
			worksheet.write(9,5, u"Cuenta",boldbord)
			worksheet.write(9,6, "Tipo Documento",boldbord)
			worksheet.write(9,7, "Nro. Comprobante",boldbord)
			worksheet.write(9,8, "Debe",boldbord)
			worksheet.write(9,9, "Haber",boldbord)
			worksheet.write(9,10, "Saldo",boldbord)
			worksheet.write(9,11, "Divisa",boldbord)
			worksheet.write(9,12, u"Importe",boldbord)



			for line in self.env['saldo.comprobante.periodo'].search(filtro):
				worksheet.write(x,0,line.periodo if line.periodo else '' ,bord )
				worksheet.write(x,1,line.fecha_emision if line.fecha_emision  else '',bord )
				worksheet.write(x,2,line.empresa if line.empresa  else '',bord)
				worksheet.write(x,3,line.tipo_cuenta if line.tipo_cuenta  else '',bord)
				worksheet.write(x,4,line.ruc if line.ruc  else '',bord)
				worksheet.write(x,5,line.code if line.code  else '',bord)
				worksheet.write(x,6,line.tipo if line.tipo  else '',bord)
				worksheet.write(x,7,line.nro_comprobante if line.nro_comprobante  else '',bord)
				worksheet.write(x,8,line.debe ,numberdos)
				worksheet.write(x,9,line.haber ,numberdos)
				worksheet.write(x,10,line.saldo ,numberdos)
				worksheet.write(x,11,line.divisa if  line.divisa else '',bord)
				worksheet.write(x,12,line.amount_currency ,numberdos)

				x = x +1

			tam_col = [11,6,8.8,7.14,38,11,11,11,10,11,14,10,11,14,14,10,16,16,20,36]


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

			workbook.close()
			
			f = open(direccion + 'saldoperiodo.xlsx', 'rb')
			
			
			sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
			vals = {
				'output_name': 'SaldoPeriodo.xlsx',
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


		