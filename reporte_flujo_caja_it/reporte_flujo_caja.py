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

class config_flujo_caja(models.Model):
	_name = 'config.flujo.caja'

	fefectivo_id = fields.Many2one('account.config.efective','Flujo Efectivo',required=True)
	n_ingreso = fields.Char('Ingreso',required=True)
	n_egreso = fields.Char('Egreso',required=True)


class reporte_flujo_caja_wizard(osv.TransientModel):
	_name='reporte.flujo.caja.wizard'

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
		worksheet = workbook.add_worksheet(u"Flujo Caja")
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
		boldbordtitle.set_text_wrap()
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


		worksheet.write(1,1, self.env["res.company"].search([])[0].name.upper(), boldbordtitle)
		worksheet.write(2,1, u"ESTADO DE FLUJOS DE CAJA", boldbordtitle)
		worksheet.write(3,1, u"(Expresado en Nuevos Soles)", boldbordtitle)
	

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
			select
c1.id, 
"order",
code,
concept,
"group",
coalesce(c2.ingreso,0.00) as ingresoapertura,
coalesce(c2.egreso,0.00) as egresoapertura,
coalesce(c2.monto,0.00) as apertura,

coalesce(c3.ingreso,0.00) as ingresoenero,
coalesce(c3.egreso,0.00) as egresoenero,
coalesce(c3.monto,0.00) as enero,

coalesce(c4.ingreso,0.00) as ingresofebrero,
coalesce(c4.egreso,0.00) as egresofebrero,
coalesce(c4.monto,0.00) as febrero,

coalesce(c5.ingreso,0.00) as ingresomarzo,
coalesce(c5.egreso,0.00) as egresomarzo,
coalesce(c5.monto,0.00) as marzo,

coalesce(c6.ingreso,0.00) as ingresoabril,
coalesce(c6.egreso,0.00) as egresoabril,
coalesce(c6.monto,0.00) as abril,

coalesce(c7.ingreso,0.00) as ingresomayo,
coalesce(c7.egreso,0.00) as egresomayo,
coalesce(c7.monto,0.00) as mayo,

coalesce(c8.ingreso,0.00) as ingresojunio,
coalesce(c8.egreso,0.00) as egresojunio,
coalesce(c8.monto,0.00) as junio,

coalesce(c9.ingreso,0.00) as ingresojulio,
coalesce(c9.egreso,0.00) as egresojulio,
coalesce(c9.monto,0.00) as julio,

coalesce(c10.ingreso,0.00) as ingresoagosto,
coalesce(c10.egreso,0.00) as egresoagosto,
coalesce(c10.monto,0.00) as agosto,

coalesce(c11.ingreso,0.00) as ingresoseptiembre,
coalesce(c11.egreso,0.00) as egresoseptiembre,
coalesce(c11.monto,0.00) as septiembre,

coalesce(c12.ingreso,0.00) as ingresooctubre,
coalesce(c12.egreso,0.00) as egresooctubre,
coalesce(c12.monto,0.00) as octubre,

coalesce(c13.ingreso,0.00) as ingresonoviembre,
coalesce(c13.egreso,0.00) as egresonoviembre,
coalesce(c13.monto,0.00) as noviembre,

coalesce(c14.ingreso,0.00) as ingresodiciembre,
coalesce(c14.egreso,0.00) as egresodiciembre,
coalesce(c14.monto,0.00) as diciembre 
from account_config_efective c1

left join (

	select b2.id as flujo_id,sum(credit) as ingreso,sum(debit) as egreso,sum(credit-debit)as monto from account_move_line bb
	left join account_account b1 on b1.id=bb.account_id
	left join account_config_efective b2 on b2.id=b1.fefectivo_id 
	where move_id in (
	select move_id from account_move_line aa
	left join account_account a1 on a1.id=aa.account_id
	left join account_move a2 on a2.id=aa.move_id
	left join account_period a3 on a3.id=a2.period_id
	where a3.code = '00/""" +self.fiscalyear_id.name+ """' and left(a1.code,2)='10')
	and
	left(b1.code,2)<>'10'

	group by b2.id 
)c2 on c2.flujo_id=c1.id

left join (

	select b2.id as flujo_id,sum(credit) as ingreso,sum(debit) as egreso,sum(credit-debit)as monto from account_move_line bb
	left join account_account b1 on b1.id=bb.account_id
	left join account_config_efective b2 on b2.id=b1.fefectivo_id 
	where move_id in (
	select move_id from account_move_line aa
	left join account_account a1 on a1.id=aa.account_id
	left join account_move a2 on a2.id=aa.move_id
	left join account_period a3 on a3.id=a2.period_id
	where a3.code = '01/""" +self.fiscalyear_id.name+ """' and left(a1.code,2)='10')
	and
	left(b1.code,2)<>'10'

	group by b2.id 
)c3 on c3.flujo_id=c1.id

left join (

	select b2.id as flujo_id,sum(credit) as ingreso,sum(debit) as egreso,sum(credit-debit)as monto from account_move_line bb
	left join account_account b1 on b1.id=bb.account_id
	left join account_config_efective b2 on b2.id=b1.fefectivo_id 
	where move_id in (
	select move_id from account_move_line aa
	left join account_account a1 on a1.id=aa.account_id
	left join account_move a2 on a2.id=aa.move_id
	left join account_period a3 on a3.id=a2.period_id
	where a3.code = '02/""" +self.fiscalyear_id.name+ """' and left(a1.code,2)='10')
	and
	left(b1.code,2)<>'10'

	group by b2.id 
)c4 on c4.flujo_id=c1.id

left join (

	select b2.id as flujo_id,sum(credit) as ingreso,sum(debit) as egreso,sum(credit-debit)as monto from account_move_line bb
	left join account_account b1 on b1.id=bb.account_id
	left join account_config_efective b2 on b2.id=b1.fefectivo_id 
	where move_id in (
	select move_id from account_move_line aa
	left join account_account a1 on a1.id=aa.account_id
	left join account_move a2 on a2.id=aa.move_id
	left join account_period a3 on a3.id=a2.period_id
	where a3.code = '03/""" +self.fiscalyear_id.name+ """' and left(a1.code,2)='10')
	and
	left(b1.code,2)<>'10'

	group by b2.id 
)c5 on c5.flujo_id=c1.id

left join (

	select b2.id as flujo_id,sum(credit) as ingreso,sum(debit) as egreso,sum(credit-debit)as monto from account_move_line bb
	left join account_account b1 on b1.id=bb.account_id
	left join account_config_efective b2 on b2.id=b1.fefectivo_id 
	where move_id in (
	select move_id from account_move_line aa
	left join account_account a1 on a1.id=aa.account_id
	left join account_move a2 on a2.id=aa.move_id
	left join account_period a3 on a3.id=a2.period_id
	where a3.code = '04/""" +self.fiscalyear_id.name+ """' and left(a1.code,2)='10')
	and
	left(b1.code,2)<>'10'

	group by b2.id 
)c6 on c6.flujo_id=c1.id

left join (

	select b2.id as flujo_id,sum(credit) as ingreso,sum(debit) as egreso,sum(credit-debit)as monto from account_move_line bb
	left join account_account b1 on b1.id=bb.account_id
	left join account_config_efective b2 on b2.id=b1.fefectivo_id 
	where move_id in (
	select move_id from account_move_line aa
	left join account_account a1 on a1.id=aa.account_id
	left join account_move a2 on a2.id=aa.move_id
	left join account_period a3 on a3.id=a2.period_id
	where a3.code = '05/""" +self.fiscalyear_id.name+ """' and left(a1.code,2)='10')
	and
	left(b1.code,2)<>'10'

	group by b2.id 
)c7 on c7.flujo_id=c1.id

left join (

	select b2.id as flujo_id,sum(credit) as ingreso,sum(debit) as egreso,sum(credit-debit)as monto from account_move_line bb
	left join account_account b1 on b1.id=bb.account_id
	left join account_config_efective b2 on b2.id=b1.fefectivo_id 
	where move_id in (
	select move_id from account_move_line aa
	left join account_account a1 on a1.id=aa.account_id
	left join account_move a2 on a2.id=aa.move_id
	left join account_period a3 on a3.id=a2.period_id
	where a3.code = '06/""" +self.fiscalyear_id.name+ """' and left(a1.code,2)='10')
	and
	left(b1.code,2)<>'10'

	group by b2.id 
)c8 on c8.flujo_id=c1.id

left join (

	select b2.id as flujo_id,sum(credit) as ingreso,sum(debit) as egreso,sum(credit-debit)as monto from account_move_line bb
	left join account_account b1 on b1.id=bb.account_id
	left join account_config_efective b2 on b2.id=b1.fefectivo_id 
	where move_id in (
	select move_id from account_move_line aa
	left join account_account a1 on a1.id=aa.account_id
	left join account_move a2 on a2.id=aa.move_id
	left join account_period a3 on a3.id=a2.period_id
	where a3.code = '07/""" +self.fiscalyear_id.name+ """' and left(a1.code,2)='10')
	and
	left(b1.code,2)<>'10'

	group by b2.id 
)c9 on c9.flujo_id=c1.id

left join (

	select b2.id as flujo_id,sum(credit) as ingreso,sum(debit) as egreso,sum(credit-debit)as monto from account_move_line bb
	left join account_account b1 on b1.id=bb.account_id
	left join account_config_efective b2 on b2.id=b1.fefectivo_id 
	where move_id in (
	select move_id from account_move_line aa
	left join account_account a1 on a1.id=aa.account_id
	left join account_move a2 on a2.id=aa.move_id
	left join account_period a3 on a3.id=a2.period_id
	where a3.code = '08/""" +self.fiscalyear_id.name+ """' and left(a1.code,2)='10')
	and
	left(b1.code,2)<>'10'

	group by b2.id 
)c10 on c10.flujo_id=c1.id

left join (

	select b2.id as flujo_id,sum(credit) as ingreso,sum(debit) as egreso,sum(credit-debit)as monto from account_move_line bb
	left join account_account b1 on b1.id=bb.account_id
	left join account_config_efective b2 on b2.id=b1.fefectivo_id 
	where move_id in (
	select move_id from account_move_line aa
	left join account_account a1 on a1.id=aa.account_id
	left join account_move a2 on a2.id=aa.move_id
	left join account_period a3 on a3.id=a2.period_id
	where a3.code = '09/""" +self.fiscalyear_id.name+ """' and left(a1.code,2)='10')
	and
	left(b1.code,2)<>'10'

	group by b2.id 
)c11 on c11.flujo_id=c1.id

left join (

	select b2.id as flujo_id,sum(credit) as ingreso,sum(debit) as egreso,sum(credit-debit)as monto from account_move_line bb
	left join account_account b1 on b1.id=bb.account_id
	left join account_config_efective b2 on b2.id=b1.fefectivo_id 
	where move_id in (
	select move_id from account_move_line aa
	left join account_account a1 on a1.id=aa.account_id
	left join account_move a2 on a2.id=aa.move_id
	left join account_period a3 on a3.id=a2.period_id
	where a3.code = '10/""" +self.fiscalyear_id.name+ """' and left(a1.code,2)='10')
	and
	left(b1.code,2)<>'10'

	group by b2.id 
)c12 on c12.flujo_id=c1.id

left join (

	select b2.id as flujo_id,sum(credit) as ingreso,sum(debit) as egreso,sum(credit-debit)as monto from account_move_line bb
	left join account_account b1 on b1.id=bb.account_id
	left join account_config_efective b2 on b2.id=b1.fefectivo_id 
	where move_id in (
	select move_id from account_move_line aa
	left join account_account a1 on a1.id=aa.account_id
	left join account_move a2 on a2.id=aa.move_id
	left join account_period a3 on a3.id=a2.period_id
	where a3.code = '11/""" +self.fiscalyear_id.name+ """' and left(a1.code,2)='10')
	and
	left(b1.code,2)<>'10'

	group by b2.id 
)c13 on c13.flujo_id=c1.id

left join (

	select b2.id as flujo_id,sum(credit) as ingreso,sum(debit) as egreso,sum(credit-debit)as monto from account_move_line bb
	left join account_account b1 on b1.id=bb.account_id
	left join account_config_efective b2 on b2.id=b1.fefectivo_id 
	where move_id in (
	select move_id from account_move_line aa
	left join account_account a1 on a1.id=aa.account_id
	left join account_move a2 on a2.id=aa.move_id
	left join account_period a3 on a3.id=a2.period_id
	where a3.code = '12/""" +self.fiscalyear_id.name+ """' and left(a1.code,2)='10')
	and
	left(b1.code,2)<>'10'

	group by b2.id 
)c14 on c14.flujo_id=c1.id

order by c1.group,c1.order

  """)
		contenedor_total = []
		for i in self.env.cr.fetchall():
			tmp = []
			for j in range(0,len(i)):
				tmp.append(i[j])
			contenedor_total.append( tmp )

		contenedor_tmp = []
		for i in self.env['config.flujo.caja'].search([]):
			for j in contenedor_total:
				if j[0] == i.fefectivo_id.id:
					tmp = list(j)
					j[3] = i.n_ingreso
					j[6+1] = j[5]
					j[9+1] = j[8]
					j[12+1] = j[11]
					j[15+1] = j[14]
					j[18+1] = j[17]
					j[21+1] = j[20]
					j[24+1] = j[23]
					j[27+1] = j[26]
					j[30+1] = j[29]
					j[33+1] = j[32]
					j[36+1] = j[35]
					j[39+1] = j[38]
					j[42+1] = j[41]


					tmp[3] = i.n_egreso
					if tmp[4] == 'E1':
						tmp[4] = 'E2'
					elif tmp[4] == 'E2':
						tmp[4] = 'E1'
					elif tmp[4] == 'E3':
						tmp[4] = 'E4'
					elif tmp[4] == 'E4':
						tmp[4] = 'E3'
					elif tmp[4] == 'E5':
						tmp[4] = 'E6'
					elif tmp[4] == 'E6':
						tmp[4] = 'E5'
					elif tmp[4] == 'E7':
						tmp[4] = 'E8'
					elif tmp[4] == 'E8':
						tmp[4] = 'E7'
					tmp[6+1] = -tmp[6]
					tmp[9+1] = -tmp[9]
					tmp[12+1] = -tmp[12]
					tmp[15+1] = -tmp[15]
					tmp[18+1] = -tmp[18]
					tmp[21+1] = -tmp[21]
					tmp[24+1] = -tmp[24]
					tmp[27+1] = -tmp[27]
					tmp[30+1] = -tmp[30]
					tmp[33+1] = -tmp[33]
					tmp[36+1] = -tmp[36]
					tmp[39+1] = -tmp[39]
					tmp[42+1] = -tmp[42]
					contenedor_tmp.append(tmp)

		for m in contenedor_tmp:
			contenedor_total.append(m)


		newcon = list (contenedor_total)
		contenedor_total = []
		for i in newcon:
			contenedor_total.append(i[1:])

			




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
		worksheet.write(x,1, u"SALDO INICIAL", bold)

		worksheet.write(x-1,2, u"ENERO", bold)
		worksheet.write(x-1,3, u"FEBRERO", bold)
		worksheet.write(x-1,4, u"MARZO", bold)
		worksheet.write(x-1,5, u"ABRIL", bold)
		worksheet.write(x-1,6, u"MAYO", bold)
		worksheet.write(x-1,7, u"JUNIO", bold)
		worksheet.write(x-1,8, u"JULIO", bold)
		worksheet.write(x-1,9, u"AGOSTO", bold)
		worksheet.write(x-1,10, u"SEPTIEMBRE", bold)
		worksheet.write(x-1,11, u"OCTUBRE", bold)
		worksheet.write(x-1,12, u"NOVIEMBRE", bold)
		worksheet.write(x-1,13, u"DICIEMBRE", bold)
		

		x+=1
		worksheet.write(x,1, u"ACTIVIDADES DE OPERACIÓN", bold)
		x+=1


		sumgrupo1 = None
		for i in contenedor_1:

			worksheet.write(x,1, i[2], normal)
			worksheet.write(x,2, i[9], numberdos)
			worksheet.write(x,3, i[12], numberdos)
			worksheet.write(x,4, i[15], numberdos)
			worksheet.write(x,5, i[18], numberdos)
			worksheet.write(x,6, i[21], numberdos)
			worksheet.write(x,7, i[24], numberdos)
			worksheet.write(x,8, i[27], numberdos)
			worksheet.write(x,9, i[30], numberdos)
			worksheet.write(x,10, i[33], numberdos)
			worksheet.write(x,11, i[36], numberdos)
			worksheet.write(x,12, i[39], numberdos)
			worksheet.write(x,13, i[42], numberdos)
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
			worksheet.write(x,1, i[2], normal)
			worksheet.write(x,2, i[9], numberdos)
			worksheet.write(x,3, i[12], numberdos)
			worksheet.write(x,4, i[15], numberdos)
			worksheet.write(x,5, i[18], numberdos)
			worksheet.write(x,6, i[21], numberdos)
			worksheet.write(x,7, i[24], numberdos)
			worksheet.write(x,8, i[27], numberdos)
			worksheet.write(x,9, i[30], numberdos)
			worksheet.write(x,10, i[33], numberdos)
			worksheet.write(x,11, i[36], numberdos)
			worksheet.write(x,12, i[39], numberdos)
			worksheet.write(x,13, i[42], numberdos)
			x += 1


		#self.env.cr.execute(""" select coalesce(sum(coalesce(saldo,0)),0) from account_state_efective
		#	where grupo = 'E2' or grupo='E1' """)
		#listtotalF1F2 =  self.env.cr.fetchall()
		
		contenedor_1_2 = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

		for i in contenedor_1:
			for j in range(4,43):
				contenedor_1_2[j] += i[j]

		for i in contenedor_2:
			for j in range(4,43):
				contenedor_1_2[j] += i[j]



		x+= 1

		worksheet.write(x,1, u"Aumento(Dism) del efectivo y equivalente de efectivo proveniente de actividades de operación", bold)

		worksheet.write(x,2, contenedor_1_2[9], numberdosbold)
		worksheet.write(x,3, contenedor_1_2[12], numberdosbold)
		worksheet.write(x,4, contenedor_1_2[15], numberdosbold)
		worksheet.write(x,5, contenedor_1_2[18], numberdosbold)
		worksheet.write(x,6, contenedor_1_2[21], numberdosbold)
		worksheet.write(x,7, contenedor_1_2[24], numberdosbold)
		worksheet.write(x,8, contenedor_1_2[27], numberdosbold)
		worksheet.write(x,9, contenedor_1_2[30], numberdosbold)
		worksheet.write(x,10, contenedor_1_2[33], numberdosbold)
		worksheet.write(x,11, contenedor_1_2[36], numberdosbold)
		worksheet.write(x,12, contenedor_1_2[39], numberdosbold)
		worksheet.write(x,13, contenedor_1_2[42], numberdosbold)

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
			worksheet.write(x,1, i[2], normal)
			worksheet.write(x,2, i[9], numberdos)
			worksheet.write(x,3, i[12], numberdos)
			worksheet.write(x,4, i[15], numberdos)
			worksheet.write(x,5, i[18], numberdos)
			worksheet.write(x,6, i[21], numberdos)
			worksheet.write(x,7, i[24], numberdos)
			worksheet.write(x,8, i[27], numberdos)
			worksheet.write(x,9, i[30], numberdos)
			worksheet.write(x,10, i[33], numberdos)
			worksheet.write(x,11, i[36], numberdos)
			worksheet.write(x,12, i[39], numberdos)
			worksheet.write(x,13, i[42], numberdos)
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
			worksheet.write(x,1, i[2], normal)
			worksheet.write(x,2, i[9], numberdos)
			worksheet.write(x,3, i[12], numberdos)
			worksheet.write(x,4, i[15], numberdos)
			worksheet.write(x,5, i[18], numberdos)
			worksheet.write(x,6, i[21], numberdos)
			worksheet.write(x,7, i[24], numberdos)
			worksheet.write(x,8, i[27], numberdos)
			worksheet.write(x,9, i[30], numberdos)
			worksheet.write(x,10, i[33], numberdos)
			worksheet.write(x,11, i[36], numberdos)
			worksheet.write(x,12, i[39], numberdos)
			worksheet.write(x,13, i[42], numberdos)
			x += 1


		#self.env.cr.execute(""" select coalesce(sum(coalesce(saldo,0)),0)   from account_state_efective
		#	where grupo = 'E3' or grupo='E4' """)
		#listtotalF1F2 =  self.env.cr.fetchall()

		x+=1

		contenedor_3_4 = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

		for i in contenedor_3:
			for j in range(4,43):
				contenedor_3_4[j] += i[j]

		for i in contenedor_4:
			for j in range(4,43):
				contenedor_3_4[j] += i[j]



		x+= 1

		worksheet.write(x,1, u"Aumento(Dism) del efectivo y equiv. de efectivo prov. de activ. de inversión", bold)

		worksheet.write(x,2, contenedor_3_4[9], numberdosbold)
		worksheet.write(x,3, contenedor_3_4[12], numberdosbold)
		worksheet.write(x,4, contenedor_3_4[15], numberdosbold)
		worksheet.write(x,5, contenedor_3_4[18], numberdosbold)
		worksheet.write(x,6, contenedor_3_4[21], numberdosbold)
		worksheet.write(x,7, contenedor_3_4[24], numberdosbold)
		worksheet.write(x,8, contenedor_3_4[27], numberdosbold)
		worksheet.write(x,9, contenedor_3_4[30], numberdosbold)
		worksheet.write(x,10, contenedor_3_4[33], numberdosbold)
		worksheet.write(x,11, contenedor_3_4[36], numberdosbold)
		worksheet.write(x,12, contenedor_3_4[39], numberdosbold)
		worksheet.write(x,13, contenedor_3_4[42], numberdosbold)

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
			worksheet.write(x,1, i[2], normal)
			worksheet.write(x,2, i[9], numberdos)
			worksheet.write(x,3, i[12], numberdos)
			worksheet.write(x,4, i[15], numberdos)
			worksheet.write(x,5, i[18], numberdos)
			worksheet.write(x,6, i[21], numberdos)
			worksheet.write(x,7, i[24], numberdos)
			worksheet.write(x,8, i[27], numberdos)
			worksheet.write(x,9, i[30], numberdos)
			worksheet.write(x,10, i[33], numberdos)
			worksheet.write(x,11, i[36], numberdos)
			worksheet.write(x,12, i[39], numberdos)
			worksheet.write(x,13, i[42], numberdos)
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
			worksheet.write(x,1, i[2], normal)
			worksheet.write(x,2, i[9], numberdos)
			worksheet.write(x,3, i[12], numberdos)
			worksheet.write(x,4, i[15], numberdos)
			worksheet.write(x,5, i[18], numberdos)
			worksheet.write(x,6, i[21], numberdos)
			worksheet.write(x,7, i[24], numberdos)
			worksheet.write(x,8, i[27], numberdos)
			worksheet.write(x,9, i[30], numberdos)
			worksheet.write(x,10, i[33], numberdos)
			worksheet.write(x,11, i[36], numberdos)
			worksheet.write(x,12, i[39], numberdos)
			worksheet.write(x,13, i[42], numberdos)
			x += 1


		#self.env.cr.execute(""" select coalesce(sum(coalesce(saldo,0)),0) from account_state_efective
		#	where grupo = 'E5' or grupo='E6' """)
		#listtotalF1F2 =  self.env.cr.fetchall()


		contenedor_5_6 = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

		for i in contenedor_5:
			for j in range(4,43):
				contenedor_5_6[j] += i[j]

		for i in contenedor_6:
			for j in range(4,43):
				contenedor_5_6[j] += i[j]



		x+= 1

		worksheet.write(x,1, u"Aumento(Dism) de efectivo y equiv. de efect. proven. de activ. de financiamiento", bold)

		worksheet.write(x,2, contenedor_5_6[9], numberdosbold)
		worksheet.write(x,3, contenedor_5_6[12], numberdosbold)
		worksheet.write(x,4, contenedor_5_6[15], numberdosbold)
		worksheet.write(x,5, contenedor_5_6[18], numberdosbold)
		worksheet.write(x,6, contenedor_5_6[21], numberdosbold)
		worksheet.write(x,7, contenedor_5_6[24], numberdosbold)
		worksheet.write(x,8, contenedor_5_6[27], numberdosbold)
		worksheet.write(x,9, contenedor_5_6[30], numberdosbold)
		worksheet.write(x,10, contenedor_5_6[33], numberdosbold)
		worksheet.write(x,11, contenedor_5_6[36], numberdosbold)
		worksheet.write(x,12, contenedor_5_6[39], numberdosbold)
		worksheet.write(x,13, contenedor_5_6[42], numberdosbold)
		x += 1


		contenedor_1_2_3_4_5_6 = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]


		for i in contenedor_1:
			for j in range(4,43):
				contenedor_1_2_3_4_5_6[j] += i[j]

		for i in contenedor_2:
			for j in range(4,43):
				contenedor_1_2_3_4_5_6[j] += i[j]

		for i in contenedor_3:
			for j in range(4,43):
				contenedor_1_2_3_4_5_6[j] += i[j]

		for i in contenedor_4:
			for j in range(4,43):
				contenedor_1_2_3_4_5_6[j] += i[j]

		for i in contenedor_5:
			for j in range(4,43):
				contenedor_1_2_3_4_5_6[j] += i[j]

		for i in contenedor_6:
			for j in range(4,43):
				contenedor_1_2_3_4_5_6[j] += i[j]



		x+= 1

		worksheet.write(x,1, u"AUMENTOS(DIM) NETO DE EFECTIVO Y EQUIVALENTE DE EFECTIVO", bold)

		worksheet.write(x,2, contenedor_1_2_3_4_5_6[9], numberdosbold)
		worksheet.write(x,3, contenedor_1_2_3_4_5_6[12], numberdosbold)
		worksheet.write(x,4, contenedor_1_2_3_4_5_6[15], numberdosbold)
		worksheet.write(x,5, contenedor_1_2_3_4_5_6[18], numberdosbold)
		worksheet.write(x,6, contenedor_1_2_3_4_5_6[21], numberdosbold)
		worksheet.write(x,7, contenedor_1_2_3_4_5_6[24], numberdosbold)
		worksheet.write(x,8, contenedor_1_2_3_4_5_6[27], numberdosbold)
		worksheet.write(x,9, contenedor_1_2_3_4_5_6[30], numberdosbold)
		worksheet.write(x,10, contenedor_1_2_3_4_5_6[33], numberdosbold)
		worksheet.write(x,11, contenedor_1_2_3_4_5_6[36], numberdosbold)
		worksheet.write(x,12, contenedor_1_2_3_4_5_6[39], numberdosbold)
		worksheet.write(x,13, contenedor_1_2_3_4_5_6[42], numberdosbold)
		x += 1




		contenedor_total_7 = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

		for i in contenedor_7:
			for j in range(4,43):
				contenedor_total_7[j] += i[j]

		worksheet.write(x,1, u"Saldo Efectivo y Equivalente de Efectivo al Inicio de Ejercicio", normal)
		
		worksheet.write(x,2, contenedor_total_7[9], numberdosbold)
		worksheet.write(x,3, contenedor_total_7[12], numberdosbold)
		worksheet.write(x,4, contenedor_total_7[15], numberdosbold)
		worksheet.write(x,5, contenedor_total_7[18], numberdosbold)
		worksheet.write(x,6, contenedor_total_7[21], numberdosbold)
		worksheet.write(x,7, contenedor_total_7[24], numberdosbold)
		worksheet.write(x,8, contenedor_total_7[27], numberdosbold)
		worksheet.write(x,9, contenedor_total_7[30], numberdosbold)
		worksheet.write(x,10, contenedor_total_7[33], numberdosbold)
		worksheet.write(x,11, contenedor_total_7[36], numberdosbold)
		worksheet.write(x,12, contenedor_total_7[39], numberdosbold)
		worksheet.write(x,13, contenedor_total_7[42], numberdosbold)
		x += 1



		contenedor_total_8 = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

		for i in contenedor_8:
			for j in range(4,43):
				contenedor_total_8[j] += i[j]

		worksheet.write(x,1, u"Ajuste por diferencia de Cambio", normal)
		
		worksheet.write(x,2, contenedor_total_8[9], numberdosbold)
		worksheet.write(x,3, contenedor_total_8[12], numberdosbold)
		worksheet.write(x,4, contenedor_total_8[15], numberdosbold)
		worksheet.write(x,5, contenedor_total_8[18], numberdosbold)
		worksheet.write(x,6, contenedor_total_8[21], numberdosbold)
		worksheet.write(x,7, contenedor_total_8[24], numberdosbold)
		worksheet.write(x,8, contenedor_total_8[27], numberdosbold)
		worksheet.write(x,9, contenedor_total_8[30], numberdosbold)
		worksheet.write(x,10, contenedor_total_8[33], numberdosbold)
		worksheet.write(x,11, contenedor_total_8[36], numberdosbold)
		worksheet.write(x,12, contenedor_total_8[39], numberdosbold)
		worksheet.write(x,13, contenedor_total_8[42], numberdosbold)
		x += 1
		


		contenedor_total_1al8 = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

		for i in contenedor_1:
			for j in range(4,43):
				contenedor_total_1al8[j] += i[j]
		for i in contenedor_2:
			for j in range(4,43):
				contenedor_total_1al8[j] += i[j]
		for i in contenedor_3:
			for j in range(4,43):
				contenedor_total_1al8[j] += i[j]
		for i in contenedor_4:
			for j in range(4,43):
				contenedor_total_1al8[j] += i[j]
		for i in contenedor_5:
			for j in range(4,43):
				contenedor_total_1al8[j] += i[j]
		for i in contenedor_6:
			for j in range(4,43):
				contenedor_total_1al8[j] += i[j]
		for i in contenedor_7:
			for j in range(4,43):
				contenedor_total_1al8[j] += i[j]
		for i in contenedor_8:
			for j in range(4,43):
				contenedor_total_1al8[j] += i[j]


		pos_saldo_final = x
		worksheet.write(x,1, u"Saldo al finalizar de efectivo y equivalente de efectivo al finalizar el ejercicio", bold)
		
		worksheet.write(x,2, contenedor_total_1al8[9], numberdosbold)
		worksheet.write(x,3, contenedor_total_1al8[12], numberdosbold)
		worksheet.write(x,4, contenedor_total_1al8[15], numberdosbold)
		worksheet.write(x,5, contenedor_total_1al8[18], numberdosbold)
		worksheet.write(x,6, contenedor_total_1al8[21], numberdosbold)
		worksheet.write(x,7, contenedor_total_1al8[24], numberdosbold)
		worksheet.write(x,8, contenedor_total_1al8[27], numberdosbold)
		worksheet.write(x,9, contenedor_total_1al8[30], numberdosbold)
		worksheet.write(x,10, contenedor_total_1al8[33], numberdosbold)
		worksheet.write(x,11, contenedor_total_1al8[36], numberdosbold)
		worksheet.write(x,12, contenedor_total_1al8[39], numberdosbold)
		worksheet.write(x,13, contenedor_total_1al8[42], numberdosbold)
		x += 1


		worksheet.write(x,1, u"SALDO FINAL", bold)
		
		worksheet.write(x,2, '=sum(' + xl_rowcol_to_cell(pos_saldo_inicial,2) +'+' +xl_rowcol_to_cell(pos_saldo_final,2) + ')' , numberdosbold)
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

		worksheet.write(pos_saldo_inicial,2, saldo_ini_ini, numberdosbold)
		worksheet.write(pos_saldo_inicial,3, '=(' + xl_rowcol_to_cell(pos_saldo_final+1,2) + ')' , numberdosbold)
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
		


		worksheet.set_column('B:B',97)
		worksheet.set_column('C:AZ',24)

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

