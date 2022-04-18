# -*- coding: utf-8 -*-
from openerp import models, fields, api
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
from cgi import escape
import base64


class reporte_flujo_cajacuenta_wizard(osv.TransientModel):
	_name='reporte.flujo.cajacuenta.wizard'

	fiscalyear_id = fields.Many2one('account.fiscalyear','Año Fiscal',required=True)

	@api.model
	def redondear(self,entrada):
		op = round(entrada + 0.00001,2)
		return op

	@api.multi
	def do_rebuild(self):	

		import io
		from xlsxwriter.workbook import Workbook
		from xlsxwriter.utility import xl_rowcol_to_cell

		import sys
		reload(sys)
		sys.setdefaultencoding('iso-8859-1')

		output = io.BytesIO()
		########### PRIMERA HOJA DE LA DATA EN TABLA
		#workbook = Workbook(output, {'in_memory': True})

		direccion = self.env['main.parameter'].search([])[0].dir_create_file
		if not direccion:
			raise osv.except_osv('Alerta!', u"No fue configurado el directorio para los archivos en Configuracion.")

		workbook = Workbook(direccion +'Reporte_state_efective.xlsx')
		worksheet = workbook.add_worksheet(u"Flujo Caja Detallado")
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
		numberdos = workbook.add_format({'num_format':'#,##0.00'})
		bord = workbook.add_format()
		bord.set_border(style=1)



		boldbordtitle = workbook.add_format({'bold': True})
		boldbordtitle.set_align('center')
		boldbordtitle.set_align('vcenter')
		#boldbordtitle.set_text_wrap()
		numbertresbold = workbook.add_format({'num_format':'0.000','bold': True})
		numberdosbold = workbook.add_format({'num_format':'#,##0.00','bold': True})
		numberdosbold.set_border(style=1)
		numbertresbold.set_border(style=1)	

		numberdoscon = workbook.add_format({'num_format':'#,##0.00'})

		boldtotal = workbook.add_format({'bold': True})
		boldtotal.set_align('right')
		boldtotal.set_align('vright')

		merge_format = workbook.add_format({
											'bold': 1,
											'border': 1,
											'align': 'center',
											'valign': 'vcenter',
											})	
		merge_format.set_bg_color('#DCE6F1')
		merge_format.set_text_wrap()
		merge_format.set_font_size(9)


		worksheet.write(1,2, self.env["res.company"].search([])[0].name.upper(), boldbordtitle)
		worksheet.write(2,2, u"ESTADO DE FLUJOS DE CAJA DETALLADO", boldbordtitle)
		worksheet.write(3,2, u"(Expresado en Nuevos Soles)", boldbordtitle)
	

		colum = {
			1: "Enero",
			2: "Febrero",
			3: "Marzo",
			4: "Abril",
			5: "Mayo",
			6: "Junio",
			7: "Julio",
			8: "Agosto",
			9: "Septiembre",
			10: "Octubre",
			11: "Noviembre",
			12: "Diciembre",
		}




		#### INICIO

		x=7



		self.env.cr.execute(""" 

	select row_number() OVER () AS id,* from ( 
select 
t1.id as id_cta,
t1.code as cuenta,
t1.name as descripcion,
t2.group as grupo_fe,
coalesce(t3.balance,0.00) as enero,
coalesce(t4.balance,0.00) as febrero,
coalesce(t5.balance,0.00) as marzo, 
coalesce(t6.balance,0.00) as abril,
coalesce(t7.balance,0.00) as mayo,
coalesce(t8.balance,0.00) as junio,
coalesce(t9.balance,0.00) as julio,
coalesce(t10.balance,0.00) as agosto,
coalesce(t11.balance,0.00) as setiembre,
coalesce(t12.balance,0.00) as octubre,
coalesce(t13.balance,0.00) as noviembre,
coalesce(t14.balance,0.00) as diciembre
 
from account_account t1
left join account_config_efective t2 on t2.id=t1.fefectivo_id
left join 
	(
	select account_id,sum(credit-debit) as balance from account_move_line 
	where move_id in (select move_id from account_move_line B1 
	left join account_account B2 on b2.ID=B1.account_id
	left join account_move B3 on B3.id=B1.move_id 
	left join account_period ap on ap.id = B3.period_id
	where left(B2.code,2)='10' and ap.code = '01/""" +self.fiscalyear_id.name+ """' and  B3.state='posted') 
	group by account_id
	) t3 on t3.account_id=t1.id

left join 
	(
	select account_id,sum(credit-debit) as balance from account_move_line 
	where move_id in (select move_id from account_move_line B1 
	left join account_account B2 on b2.ID=B1.account_id
	left join account_move B3 on B3.id=B1.move_id 
	left join account_period ap on ap.id = B3.period_id
	where left(B2.code,2)='10' and ap.code = '02/""" +self.fiscalyear_id.name+ """' and  B3.state='posted') 
	group by account_id
	) t4 on t4.account_id=t1.id

left join 
	(
	select account_id,sum(credit-debit) as balance from account_move_line 
	where move_id in (select move_id from account_move_line B1 
	left join account_account B2 on b2.ID=B1.account_id
	left join account_move B3 on B3.id=B1.move_id 
	left join account_period ap on ap.id = B3.period_id
	where left(B2.code,2)='10' and ap.code = '03/""" +self.fiscalyear_id.name+ """' and  B3.state='posted') 
	group by account_id
	) t5 on t5.account_id=t1.id

left join 
	(
	select account_id,sum(credit-debit) as balance from account_move_line 
	where move_id in (select move_id from account_move_line B1 
	left join account_account B2 on b2.ID=B1.account_id
	left join account_move B3 on B3.id=B1.move_id 
	left join account_period ap on ap.id = B3.period_id
	where left(B2.code,2)='10' and ap.code = '04/""" +self.fiscalyear_id.name+ """' and  B3.state='posted') 
	group by account_id
	) t6 on t6.account_id=t1.id

left join 
	(
	select account_id,sum(credit-debit) as balance from account_move_line 
	where move_id in (select move_id from account_move_line B1 
	left join account_account B2 on b2.ID=B1.account_id
	left join account_move B3 on B3.id=B1.move_id 
	left join account_period ap on ap.id = B3.period_id
	where left(B2.code,2)='10' and ap.code = '05/""" +self.fiscalyear_id.name+ """' and  B3.state='posted') 
	group by account_id
	) t7 on t7.account_id=t1.id

left join 
	(
	select account_id,sum(credit-debit) as balance from account_move_line 
	where move_id in (select move_id from account_move_line B1 
	left join account_account B2 on b2.ID=B1.account_id
	left join account_move B3 on B3.id=B1.move_id 
	left join account_period ap on ap.id = B3.period_id
	where left(B2.code,2)='10' and ap.code = '06/""" +self.fiscalyear_id.name+ """' and  B3.state='posted') 
	group by account_id
	) t8 on t8.account_id=t1.id

left join 
	(
	select account_id,sum(credit-debit) as balance from account_move_line 
	where move_id in (select move_id from account_move_line B1 
	left join account_account B2 on b2.ID=B1.account_id
	left join account_move B3 on B3.id=B1.move_id 
	left join account_period ap on ap.id = B3.period_id
	where left(B2.code,2)='10' and ap.code = '07/""" +self.fiscalyear_id.name+ """' and  B3.state='posted') 
	group by account_id
	) t9 on t9.account_id=t1.id

left join 
	(
	select account_id,sum(credit-debit) as balance from account_move_line 
	where move_id in (select move_id from account_move_line B1 
	left join account_account B2 on b2.ID=B1.account_id
	left join account_move B3 on B3.id=B1.move_id 
	left join account_period ap on ap.id = B3.period_id
	where left(B2.code,2)='10' and ap.code = '08/""" +self.fiscalyear_id.name+ """' and  B3.state='posted') 
	group by account_id
	) t10 on t10.account_id=t1.id

left join 
	(
	select account_id,sum(credit-debit) as balance from account_move_line 
	where move_id in (select move_id from account_move_line B1 
	left join account_account B2 on b2.ID=B1.account_id
	left join account_move B3 on B3.id=B1.move_id 
	left join account_period ap on ap.id = B3.period_id
	where left(B2.code,2)='10' and ap.code = '09/""" +self.fiscalyear_id.name+ """' and  B3.state='posted') 
	group by account_id
	) t11 on t11.account_id=t1.id

left join 
	(
	select account_id,sum(credit-debit) as balance from account_move_line 
	where move_id in (select move_id from account_move_line B1 
	left join account_account B2 on b2.ID=B1.account_id
	left join account_move B3 on B3.id=B1.move_id 
	left join account_period ap on ap.id = B3.period_id
	where left(B2.code,2)='10' and ap.code = '10/""" +self.fiscalyear_id.name+ """' and  B3.state='posted') 
	group by account_id
	) t12 on t12.account_id=t1.id

left join 
	(
	select account_id,sum(credit-debit) as balance from account_move_line 
	where move_id in (select move_id from account_move_line B1 
	left join account_account B2 on b2.ID=B1.account_id
	left join account_move B3 on B3.id=B1.move_id 
	left join account_period ap on ap.id = B3.period_id
	where left(B2.code,2)='10' and ap.code = '11/""" +self.fiscalyear_id.name+ """' and  B3.state='posted') 
	group by account_id
	) t13 on t13.account_id=t1.id
	
left join 
	(
	select account_id,sum(credit-debit) as balance from account_move_line 
	where move_id in (select move_id from account_move_line B1 
	left join account_account B2 on b2.ID=B1.account_id
	left join account_move B3 on B3.id=B1.move_id 
	left join account_period ap on ap.id = B3.period_id
	where left(B2.code,2)='10' and ap.code = '12/""" +self.fiscalyear_id.name+ """' and  B3.state='posted') 
	group by account_id
	) t14 on t14.account_id=t1.id	
	


where t1.fefectivo_id is not null
order by t2.group,t1.code) tt


  """)
		contenedor_total = []
		for i in self.env.cr.fetchall():
			tmp = []
			for j in range(1,len(i)):
				tmp.append(i[j])
			contenedor_total.append( tmp )


		contenedor_1 = []
		contenedor_2 = []
		contenedor_3 = []
		contenedor_4 = []
		contenedor_5 = []
		contenedor_6 = []
		contenedor_7 = []
		contenedor_8 = []

		for i in contenedor_total:
			if i[3] == 'E1':
				contenedor_1.append(i)
			elif i[3] == 'E2':
				contenedor_2.append(i)
			elif i[3] == 'E3':
				contenedor_3.append(i)
			elif i[3] == 'E4':
				contenedor_4.append(i)
			elif i[3] == 'E5':
				contenedor_5.append(i)
			elif i[3] == 'E6':
				contenedor_6.append(i)
			elif i[3] == 'E7':
				contenedor_7.append(i)
			elif i[3] == 'E8':
				contenedor_8.append(i)

		contenedor_1.sort(key = lambda r: r[0])
		contenedor_2.sort(key = lambda r: r[0])
		contenedor_3.sort(key = lambda r: r[0])
		contenedor_4.sort(key = lambda r: r[0])
		contenedor_5.sort(key = lambda r: r[0])
		contenedor_6.sort(key = lambda r: r[0])
		contenedor_7.sort(key = lambda r: r[0])
		contenedor_8.sort(key = lambda r: r[0])




		#self.env.cr.execute(""" select concept as code,'' as concept,'' as grupo,sum(saldo),orden from account_state_efective
		#	where grupo = 'E1'
		#	group by concept,grupo,orden
		#	order by orden,concept   """)
		#listobjetosF1 =  self.env.cr.fetchall()

		#worksheet.write(x,2, self.fiscalyear_id.name, bold)




		pos_saldo_inicial = x
		worksheet.write(x-1,1, u"CUENTA", boldbord)
		worksheet.write(x-1,2, u"DESCRIPCION", boldbord)

		worksheet.write(x-1,3, u"ENERO", boldbord)
		worksheet.write(x-1,4, u"FEBRERO", boldbord)
		worksheet.write(x-1,5, u"MARZO", boldbord)
		worksheet.write(x-1,6, u"ABRIL", boldbord)
		worksheet.write(x-1,7, u"MAYO", boldbord)
		worksheet.write(x-1,8, u"JUNIO", boldbord)
		worksheet.write(x-1,9, u"JULIO", boldbord)
		worksheet.write(x-1,10, u"AGOSTO", boldbord)
		worksheet.write(x-1,11, u"SEPTIEMBRE", boldbord)
		worksheet.write(x-1,12, u"OCTUBRE", boldbord)
		worksheet.write(x-1,13, u"NOVIEMBRE", boldbord)
		worksheet.write(x-1,14, u"DICIEMBRE", boldbord)


		worksheet.write(x,1, u"SALDO INICIAL", boldbord)
				

		x+=1
		worksheet.write(x,1, u"ACTIVIDADES DE OPERACIÓN", bold)
		x+=1


		sumgrupo1 = None
		for i in contenedor_1:

			worksheet.write(x,1, i[1], normal)
			worksheet.write(x,2, i[2], normal)
			worksheet.write(x,3, i[4], numberdos)
			worksheet.write(x,4, i[5], numberdos)
			worksheet.write(x,5, i[6], numberdos)
			worksheet.write(x,6, i[7], numberdos)
			worksheet.write(x,7, i[8], numberdos)
			worksheet.write(x,8, i[9], numberdos)
			worksheet.write(x,9, i[10], numberdos)
			worksheet.write(x,10, i[11], numberdos)
			worksheet.write(x,11, i[12], numberdos)
			worksheet.write(x,12, i[13], numberdos)
			worksheet.write(x,13, i[14], numberdos)
			worksheet.write(x,14, i[15], numberdos)
			x += 1


		worksheet.write(x,1, "Menos:", bold)
		x+=1


		#self.env.cr.execute(""" select concept as code,'' as concept,'' as grupo,sum(saldo),orden from account_state_efective
		#	where grupo = 'E2'
		#	group by concept,grupo,orden
		#	order by orden,concept   """)
		#listobjetosF2 =  self.env.cr.fetchall()

		sumgrupo2 = None
		for i in contenedor_2:
			worksheet.write(x,1, i[1], normal)
			worksheet.write(x,2, i[2], normal)
			worksheet.write(x,3, i[4], numberdos)
			worksheet.write(x,4, i[5], numberdos)
			worksheet.write(x,5, i[6], numberdos)
			worksheet.write(x,6, i[7], numberdos)
			worksheet.write(x,7, i[8], numberdos)
			worksheet.write(x,8, i[9], numberdos)
			worksheet.write(x,9, i[10], numberdos)
			worksheet.write(x,10, i[11], numberdos)
			worksheet.write(x,11, i[12], numberdos)
			worksheet.write(x,12, i[13], numberdos)
			worksheet.write(x,13, i[14], numberdos)
			worksheet.write(x,14, i[15], numberdos)
			x += 1


		#self.env.cr.execute(""" select coalesce(sum(coalesce(saldo,0)),0) from account_state_efective
		#	where grupo = 'E2' or grupo='E1' """)
		#listtotalF1F2 =  self.env.cr.fetchall()
		
		contenedor_1_2 = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

		for i in contenedor_1:
			for j in range(4,16):
				contenedor_1_2[j] += i[j]

		for i in contenedor_2:
			for j in range(4,16):
				contenedor_1_2[j] += i[j]



		x+= 1

		worksheet.write(x,1, u"Aumento(Dism) del efectivo y equivalente de efectivo proveniente de actividades de operación", bold)

		worksheet.write(x,3, contenedor_1_2[4], numberdosbold)
		worksheet.write(x,4, contenedor_1_2[5], numberdosbold)
		worksheet.write(x,5, contenedor_1_2[6], numberdosbold)
		worksheet.write(x,6, contenedor_1_2[7], numberdosbold)
		worksheet.write(x,7, contenedor_1_2[8], numberdosbold)
		worksheet.write(x,8, contenedor_1_2[9], numberdosbold)
		worksheet.write(x,9, contenedor_1_2[10], numberdosbold)
		worksheet.write(x,10, contenedor_1_2[11], numberdosbold)
		worksheet.write(x,11, contenedor_1_2[12], numberdosbold)
		worksheet.write(x,12, contenedor_1_2[13], numberdosbold)
		worksheet.write(x,13, contenedor_1_2[14], numberdosbold)
		worksheet.write(x,14, contenedor_1_2[15], numberdosbold)

		x += 1


		#self.env.cr.execute(""" select concept as code,'' as concept,'' as grupo,sum(saldo),orden from account_state_efective
		#	where grupo = 'E3'
		#	group by concept,grupo,orden
		#	order by orden,concept   """)
		#listobjetosF1 =  self.env.cr.fetchall()

		x+=1


		worksheet.write(x,1, u"ACTIVIDADES DE INVERSIÓN", bold)
		x+=1
			
		sumgrupo1 = None
		for i in contenedor_3:
			worksheet.write(x,1, i[1], normal)
			worksheet.write(x,2, i[2], normal)
			worksheet.write(x,3, i[4], numberdos)
			worksheet.write(x,4, i[5], numberdos)
			worksheet.write(x,5, i[6], numberdos)
			worksheet.write(x,6, i[7], numberdos)
			worksheet.write(x,7, i[8], numberdos)
			worksheet.write(x,8, i[9], numberdos)
			worksheet.write(x,9, i[10], numberdos)
			worksheet.write(x,10, i[11], numberdos)
			worksheet.write(x,11, i[12], numberdos)
			worksheet.write(x,12, i[13], numberdos)
			worksheet.write(x,13, i[14], numberdos)
			worksheet.write(x,14, i[15], numberdos)
			x += 1

		worksheet.write(x,1, u"Menos:", bold)
		x+=1
		

		#self.env.cr.execute(""" select concept as code,'' as concept,'' as grupo,sum(saldo),orden from account_state_efective
		#	where grupo = 'E4'
		#	group by concept,grupo,orden
		#	order by orden,concept   """)
		#listobjetosF2 =  self.env.cr.fetchall()

		sumgrupo2 = None
		for i in contenedor_4:
			worksheet.write(x,1, i[1], normal)
			worksheet.write(x,2, i[2], normal)
			worksheet.write(x,3, i[4], numberdos)
			worksheet.write(x,4, i[5], numberdos)
			worksheet.write(x,5, i[6], numberdos)
			worksheet.write(x,6, i[7], numberdos)
			worksheet.write(x,7, i[8], numberdos)
			worksheet.write(x,8, i[9], numberdos)
			worksheet.write(x,9, i[10], numberdos)
			worksheet.write(x,10, i[11], numberdos)
			worksheet.write(x,11, i[12], numberdos)
			worksheet.write(x,12, i[13], numberdos)
			worksheet.write(x,13, i[14], numberdos)
			worksheet.write(x,14, i[15], numberdos)
			x += 1


		#self.env.cr.execute(""" select coalesce(sum(coalesce(saldo,0)),0)   from account_state_efective
		#	where grupo = 'E3' or grupo='E4' """)
		#listtotalF1F2 =  self.env.cr.fetchall()

		x+=1

		contenedor_3_4 = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

		for i in contenedor_3:
			for j in range(4,16):
				contenedor_3_4[j] += i[j]

		for i in contenedor_4:
			for j in range(4,16):
				contenedor_3_4[j] += i[j]



		x+= 1

		worksheet.write(x,1, u"Aumento(Dism) del efectivo y equiv. de efectivo prov. de activ. de inversión", bold)

		worksheet.write(x,3, contenedor_3_4[4], numberdosbold)
		worksheet.write(x,4, contenedor_3_4[5], numberdosbold)
		worksheet.write(x,5, contenedor_3_4[6], numberdosbold)
		worksheet.write(x,6, contenedor_3_4[7], numberdosbold)
		worksheet.write(x,7, contenedor_3_4[8], numberdosbold)
		worksheet.write(x,8, contenedor_3_4[9], numberdosbold)
		worksheet.write(x,9, contenedor_3_4[10], numberdosbold)
		worksheet.write(x,10, contenedor_3_4[11], numberdosbold)
		worksheet.write(x,11, contenedor_3_4[12], numberdosbold)
		worksheet.write(x,12, contenedor_3_4[13], numberdosbold)
		worksheet.write(x,13, contenedor_3_4[14], numberdosbold)
		worksheet.write(x,14, contenedor_3_4[15], numberdosbold)

		x += 1




		#self.env.cr.execute(""" select concept as code,'' as concept,'' as grupo,sum(saldo),orden from account_state_efective
		#	where grupo = 'E5'
		#	group by concept,grupo,orden
		#	order by orden,concept  """)
		#listobjetosF1 =  self.env.cr.fetchall()

		x+=1


		worksheet.write(x,1, u"ACTIVIDADES DE FINANCIAMIENTO", bold)
		x+=1

		sumgrupo1 = None
		for i in contenedor_5:
			worksheet.write(x,1, i[1], normal)
			worksheet.write(x,2, i[2], normal)
			worksheet.write(x,3, i[4], numberdos)
			worksheet.write(x,4, i[5], numberdos)
			worksheet.write(x,5, i[6], numberdos)
			worksheet.write(x,6, i[7], numberdos)
			worksheet.write(x,7, i[8], numberdos)
			worksheet.write(x,8, i[9], numberdos)
			worksheet.write(x,9, i[10], numberdos)
			worksheet.write(x,10, i[11], numberdos)
			worksheet.write(x,11, i[12], numberdos)
			worksheet.write(x,12, i[13], numberdos)
			worksheet.write(x,13, i[14], numberdos)
			worksheet.write(x,14, i[15], numberdos)
			x += 1
		
		worksheet.write(x,1, u"Menos:", bold)
		x+=1


		#self.env.cr.execute(""" select concept as code,'' as concept,'' as grupo,sum(saldo),orden from account_state_efective
		#	where grupo = 'E6'
		#	group by concept,grupo,orden
		#	order by orden,concept  """)
		#listobjetosF2 =  self.env.cr.fetchall()

		sumgrupo2 = None
		for i in contenedor_6:
			worksheet.write(x,1, i[1], normal)
			worksheet.write(x,2, i[2], normal)
			worksheet.write(x,3, i[4], numberdos)
			worksheet.write(x,4, i[5], numberdos)
			worksheet.write(x,5, i[6], numberdos)
			worksheet.write(x,6, i[7], numberdos)
			worksheet.write(x,7, i[8], numberdos)
			worksheet.write(x,8, i[9], numberdos)
			worksheet.write(x,9, i[10], numberdos)
			worksheet.write(x,10, i[11], numberdos)
			worksheet.write(x,11, i[12], numberdos)
			worksheet.write(x,12, i[13], numberdos)
			worksheet.write(x,13, i[14], numberdos)
			worksheet.write(x,14, i[15], numberdos)
			x += 1


		#self.env.cr.execute(""" select coalesce(sum(coalesce(saldo,0)),0) from account_state_efective
		#	where grupo = 'E5' or grupo='E6' """)
		#listtotalF1F2 =  self.env.cr.fetchall()


		contenedor_5_6 = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

		for i in contenedor_5:
			for j in range(4,16):
				contenedor_5_6[j] += i[j]

		for i in contenedor_6:
			for j in range(4,16):
				contenedor_5_6[j] += i[j]



		x+= 1

		worksheet.write(x,1, u"Aumento(Dism) de efectivo y equiv. de efect. proven. de activ. de financiamiento", bold)

		worksheet.write(x,3, contenedor_5_6[4], numberdosbold)
		worksheet.write(x,4, contenedor_5_6[5], numberdosbold)
		worksheet.write(x,5, contenedor_5_6[6], numberdosbold)
		worksheet.write(x,6, contenedor_5_6[7], numberdosbold)
		worksheet.write(x,7, contenedor_5_6[8], numberdosbold)
		worksheet.write(x,8, contenedor_5_6[9], numberdosbold)
		worksheet.write(x,9, contenedor_5_6[10], numberdosbold)
		worksheet.write(x,10, contenedor_5_6[11], numberdosbold)
		worksheet.write(x,11, contenedor_5_6[12], numberdosbold)
		worksheet.write(x,12, contenedor_5_6[13], numberdosbold)
		worksheet.write(x,13, contenedor_5_6[14], numberdosbold)
		worksheet.write(x,14, contenedor_5_6[15], numberdosbold)
		x += 1


		contenedor_1_2_3_4_5_6 = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]


		for i in contenedor_1:
			for j in range(4,16):
				contenedor_1_2_3_4_5_6[j] += i[j]

		for i in contenedor_2:
			for j in range(4,16):
				contenedor_1_2_3_4_5_6[j] += i[j]

		for i in contenedor_3:
			for j in range(4,16):
				contenedor_1_2_3_4_5_6[j] += i[j]

		for i in contenedor_4:
			for j in range(4,16):
				contenedor_1_2_3_4_5_6[j] += i[j]

		for i in contenedor_5:
			for j in range(4,16):
				contenedor_1_2_3_4_5_6[j] += i[j]

		for i in contenedor_6:
			for j in range(4,16):
				contenedor_1_2_3_4_5_6[j] += i[j]



		x+= 1

		worksheet.write(x,1, u"AUMENTOS(DIM) NETO DE EFECTIVO Y EQUIVALENTE DE EFECTIVO", bold)

		worksheet.write(x,3, contenedor_1_2_3_4_5_6[4], numberdosbold)
		worksheet.write(x,4, contenedor_1_2_3_4_5_6[5], numberdosbold)
		worksheet.write(x,5, contenedor_1_2_3_4_5_6[6], numberdosbold)
		worksheet.write(x,6, contenedor_1_2_3_4_5_6[7], numberdosbold)
		worksheet.write(x,7, contenedor_1_2_3_4_5_6[8], numberdosbold)
		worksheet.write(x,8, contenedor_1_2_3_4_5_6[9], numberdosbold)
		worksheet.write(x,9, contenedor_1_2_3_4_5_6[10], numberdosbold)
		worksheet.write(x,10, contenedor_1_2_3_4_5_6[11], numberdosbold)
		worksheet.write(x,11, contenedor_1_2_3_4_5_6[12], numberdosbold)
		worksheet.write(x,12, contenedor_1_2_3_4_5_6[13], numberdosbold)
		worksheet.write(x,13, contenedor_1_2_3_4_5_6[14], numberdosbold)
		worksheet.write(x,14, contenedor_1_2_3_4_5_6[15], numberdosbold)
		x += 1




		contenedor_total_7 = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

		for i in contenedor_7:
			for j in range(4,16):
				contenedor_total_7[j] += i[j]

		worksheet.write(x,1, u"Saldo Efectivo y Equivalente de Efectivo al Inicio de Ejercicio", normal)
		
		worksheet.write(x,3, contenedor_total_7[4], numberdosbold)
		worksheet.write(x,4, contenedor_total_7[5], numberdosbold)
		worksheet.write(x,5, contenedor_total_7[6], numberdosbold)
		worksheet.write(x,6, contenedor_total_7[7], numberdosbold)
		worksheet.write(x,7, contenedor_total_7[8], numberdosbold)
		worksheet.write(x,8, contenedor_total_7[9], numberdosbold)
		worksheet.write(x,9, contenedor_total_7[10], numberdosbold)
		worksheet.write(x,10, contenedor_total_7[11], numberdosbold)
		worksheet.write(x,11, contenedor_total_7[12], numberdosbold)
		worksheet.write(x,12, contenedor_total_7[13], numberdosbold)
		worksheet.write(x,13, contenedor_total_7[14], numberdosbold)
		worksheet.write(x,14, contenedor_total_7[15], numberdosbold)
		x += 1



		contenedor_total_8 = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

		for i in contenedor_8:
			for j in range(4,16):
				contenedor_total_8[j] += i[j]

		worksheet.write(x,1, u"Ajuste por diferencia de Cambio", normal)
		
		worksheet.write(x,3, contenedor_total_8[4], numberdosbold)
		worksheet.write(x,4, contenedor_total_8[5], numberdosbold)
		worksheet.write(x,5, contenedor_total_8[6], numberdosbold)
		worksheet.write(x,6, contenedor_total_8[7], numberdosbold)
		worksheet.write(x,7, contenedor_total_8[8], numberdosbold)
		worksheet.write(x,8, contenedor_total_8[9], numberdosbold)
		worksheet.write(x,9, contenedor_total_8[10], numberdosbold)
		worksheet.write(x,10, contenedor_total_8[11], numberdosbold)
		worksheet.write(x,11, contenedor_total_8[12], numberdosbold)
		worksheet.write(x,12, contenedor_total_8[13], numberdosbold)
		worksheet.write(x,13, contenedor_total_8[14], numberdosbold)
		worksheet.write(x,14, contenedor_total_8[15], numberdosbold)
		x += 1
		


		contenedor_total_1al8 = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

		for i in contenedor_1:
			for j in range(4,16):
				contenedor_total_1al8[j] += i[j]
		for i in contenedor_2:
			for j in range(4,16):
				contenedor_total_1al8[j] += i[j]
		for i in contenedor_3:
			for j in range(4,16):
				contenedor_total_1al8[j] += i[j]
		for i in contenedor_4:
			for j in range(4,16):
				contenedor_total_1al8[j] += i[j]
		for i in contenedor_5:
			for j in range(4,16):
				contenedor_total_1al8[j] += i[j]
		for i in contenedor_6:
			for j in range(4,16):
				contenedor_total_1al8[j] += i[j]
		for i in contenedor_7:
			for j in range(4,16):
				contenedor_total_1al8[j] += i[j]
		for i in contenedor_8:
			for j in range(4,16):
				contenedor_total_1al8[j] += i[j]


		pos_saldo_final = x
		worksheet.write(x,1, u"Saldo al finalizar de efectivo y equivalente de efectivo al finalizar el ejercicio", bold)
		
		worksheet.write(x,3, contenedor_total_1al8[4], numberdosbold)
		worksheet.write(x,4, contenedor_total_1al8[5], numberdosbold)
		worksheet.write(x,5, contenedor_total_1al8[6], numberdosbold)
		worksheet.write(x,6, contenedor_total_1al8[7], numberdosbold)
		worksheet.write(x,7, contenedor_total_1al8[8], numberdosbold)
		worksheet.write(x,8, contenedor_total_1al8[9], numberdosbold)
		worksheet.write(x,9, contenedor_total_1al8[10], numberdosbold)
		worksheet.write(x,10, contenedor_total_1al8[11], numberdosbold)
		worksheet.write(x,11, contenedor_total_1al8[12], numberdosbold)
		worksheet.write(x,12, contenedor_total_1al8[13], numberdosbold)
		worksheet.write(x,13, contenedor_total_1al8[14], numberdosbold)
		worksheet.write(x,14, contenedor_total_1al8[15], numberdosbold)
		x += 1


		worksheet.write(x,1, u"SALDO FINAL", bold)
		
		worksheet.write(x,3, '=sum(' + xl_rowcol_to_cell(pos_saldo_inicial,3) +'+' +xl_rowcol_to_cell(pos_saldo_final,3) + ')' , numberdosbold)
		worksheet.write(x,4, '=sum(' + xl_rowcol_to_cell(pos_saldo_inicial,4) +'+' +xl_rowcol_to_cell(pos_saldo_final,4) + ')' , numberdosbold)
		worksheet.write(x,5, '=sum(' + xl_rowcol_to_cell(pos_saldo_inicial,5) +'+' +xl_rowcol_to_cell(pos_saldo_final,5) + ')' , numberdosbold)
		worksheet.write(x,6, '=sum(' + xl_rowcol_to_cell(pos_saldo_inicial,6) +'+' +xl_rowcol_to_cell(pos_saldo_final,6) + ')' , numberdosbold)
		worksheet.write(x,7, '=sum(' + xl_rowcol_to_cell(pos_saldo_inicial,7) +'+' +xl_rowcol_to_cell(pos_saldo_final,7) + ')' , numberdosbold)
		worksheet.write(x,8, '=sum(' + xl_rowcol_to_cell(pos_saldo_inicial,8) +'+' +xl_rowcol_to_cell(pos_saldo_final,8) + ')' , numberdosbold)
		worksheet.write(x,9, '=sum(' + xl_rowcol_to_cell(pos_saldo_inicial,9) +'+' +xl_rowcol_to_cell(pos_saldo_final,9) + ')' , numberdosbold)
		worksheet.write(x,10, '=sum(' + xl_rowcol_to_cell(pos_saldo_inicial,10) +'+' +xl_rowcol_to_cell(pos_saldo_final,10) + ')' , numberdosbold)
		worksheet.write(x,11, '=sum(' + xl_rowcol_to_cell(pos_saldo_inicial,11) +'+' +xl_rowcol_to_cell(pos_saldo_final,11) + ')' , numberdosbold)
		worksheet.write(x,12, '=sum(' + xl_rowcol_to_cell(pos_saldo_inicial,12) +'+' +xl_rowcol_to_cell(pos_saldo_final,12) + ')' , numberdosbold)
		worksheet.write(x,13, '=sum(' + xl_rowcol_to_cell(pos_saldo_inicial,13) +'+' +xl_rowcol_to_cell(pos_saldo_final,13) + ')' , numberdosbold)
		worksheet.write(x,14, '=sum(' + xl_rowcol_to_cell(pos_saldo_inicial,14) +'+' +xl_rowcol_to_cell(pos_saldo_final,14) + ')' , numberdosbold)
		x += 1
		

		saldo_ini_ini = 0


		self.env.cr.execute("""
			select sum(aml.debit - aml.credit) from 
			account_move_line aml 
			inner join account_move am on am.id = aml.move_id
			inner join account_period ap on ap.id = am.period_id
			inner join account_account aa on aa.id = aml.account_id
			where aa.code like '10%' and ap.code = '00/""" +self.fiscalyear_id.name+ """'
		""")

		for i in self.env.cr.fetchall():
			saldo_ini_ini += i[0]

		worksheet.write(pos_saldo_inicial,3, saldo_ini_ini, numberdosbold)
		worksheet.write(pos_saldo_inicial,4, '=(' + xl_rowcol_to_cell(pos_saldo_final+1,3) + ')' , numberdosbold)
		worksheet.write(pos_saldo_inicial,5, '=(' + xl_rowcol_to_cell(pos_saldo_final+1,4) + ')' , numberdosbold)
		worksheet.write(pos_saldo_inicial,6, '=(' + xl_rowcol_to_cell(pos_saldo_final+1,5) + ')' , numberdosbold)
		worksheet.write(pos_saldo_inicial,7, '=(' + xl_rowcol_to_cell(pos_saldo_final+1,6) + ')' , numberdosbold)
		worksheet.write(pos_saldo_inicial,8, '=(' + xl_rowcol_to_cell(pos_saldo_final+1,7) + ')' , numberdosbold)
		worksheet.write(pos_saldo_inicial,9, '=(' + xl_rowcol_to_cell(pos_saldo_final+1,8) + ')' , numberdosbold)
		worksheet.write(pos_saldo_inicial,10, '=(' + xl_rowcol_to_cell(pos_saldo_final+1,9) + ')' , numberdosbold)
		worksheet.write(pos_saldo_inicial,11, '=(' + xl_rowcol_to_cell(pos_saldo_final+1,10) + ')' , numberdosbold)
		worksheet.write(pos_saldo_inicial,12, '=(' + xl_rowcol_to_cell(pos_saldo_final+1,11) + ')' , numberdosbold)
		worksheet.write(pos_saldo_inicial,13, '=(' + xl_rowcol_to_cell(pos_saldo_final+1,12) + ')' , numberdosbold)
		worksheet.write(pos_saldo_inicial,14, '=(' + xl_rowcol_to_cell(pos_saldo_final+1,13) + ')' , numberdosbold)
		


		worksheet.set_column('B:B',12)
		worksheet.set_column('C:C',87)
		worksheet.set_column('D:AZ',24)

		#### FIN

		workbook.close()
		
		f = open(direccion + 'Reporte_state_efective.xlsx', 'rb')
		
		vals = {
			'output_name': 'EstadoEfectivo.xlsx',
			'output_file': base64.encodestring(''.join(f.readlines())),		
		}

		sfs_id = self.env['export.file.save'].create(vals)
		return {
			"type": "ir.actions.act_window",
			"res_model": "export.file.save",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}

