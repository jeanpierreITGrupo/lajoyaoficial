# -*- encoding: utf-8 -*-
from openerp.osv import osv
from tempfile    import TemporaryFile
from openerp     import models, fields, api
import csv
import base64
import codecs
import datetime
import openerp.addons.decimal_precision as dp

class tareo_importador(models.Model):
	_name = 'tareo.importador'

	period_id    = fields.Many2one('account.period', 'Periodo', required=True)
	name         = fields.Char('Nombre',size=50, default='Importar Tareo')
	product_file = fields.Binary('Tareo (CSV)')
	delimiter    = fields.Char('Delimitador', size=1, required=True, default=",")
	imported 	 = fields.Boolean('importado', default=False)
	state 		 = fields.Selection([('draft','Borrador'),('not_imported','No Importado'),('imported',"Importado")], 'Estado', default="draft")

	noimp_lines = fields.One2many('tareo.no.importado','importador_id','lineas')

	# def init(self, cr):
	# 	cr.execute('select id from res_users')
	# 	uid = cr.dictfetchall()
	# 	cr.execute('select id from tareo_importador')
	# 	ids = cr.fetchall()
		
	# 	if len(ids) == 0:
	# 		cr.execute("""INSERT INTO tareo_importador (create_uid, name) VALUES (""" + str(uid[0]['id']) + """, 'Importar Tareo');""")

	def string2float(self, s):
		try:
			float(s)
			return True
		except:
			return False

	@api.one
	def show_file_fields(self):
		self.state = 'not_imported'

	@api.one
	def unlink(self):
		if self.imported:
			raise osv.except_osv('Alerta!', 'No se puede eliminar el importador del periodo '+self.period_id.code+'.\nExiste una importación con este periodo')
		t = super(tareo_importador, self).unlink()
		return t

	@api.model
	def create(self, vals):
		ti = self.env['tareo.importador'].search([('period_id','=',vals['period_id'])])
		if len(ti):
			ap = self.env['account.period'].search([('id','=',vals['period_id'])])[0]
			raise osv.except_osv('Alerta!', 'Ya existe un importador para el periodo '+ap.code)
		return super(tareo_importador, self).create(vals)

	@api.one
	def write(self, vals):
		t = super(tareo_importador, self).write(vals)
		self.refresh()
		ti = self.env['tareo.importador'].search([('period_id','=',self.period_id.id)])
		if len(ti) > 1:
			raise osv.except_osv('Alerta!', 'Ya existe un importador para el periodo '+self.period_id.code)
		return t

	@api.one
	def import_tareo(self):
		if self.product_file == None:
			raise osv.except_osv('Alerta!', 'Debe cargar un archivo csv.')
		elif not self.delimiter:
			raise osv.except_osv('Alerta!', 'Debe seleccionar un delimitador.')
		else:
			self.env.cr.execute("set client_encoding ='UTF8';")
			data = self.read()[0]
			fileobj = TemporaryFile('w+')
			fileobj.write(base64.decodestring(data['product_file']))
			fileobj.seek(0)
			c=base64.decodestring(data['product_file'])
			fic = csv.reader(fileobj,delimiter=str(self.delimiter),quotechar='"')

			skip_titles = True
			for row in fic:
				if skip_titles:
					skip_titles = False
					continue
				detalle = ""

				# VALIDACIONES
				if not len(self.env['account.period'].search([('code','=',row[0].strip())])): #SI NO HAY PERIODO CONTABLE
					detalle += u"- periodo contable incorrecto\n"
				if not len(self.env['hr.employee'].search([('identification_id','=',row[1].strip())])): #SI NO HAY DNI
					detalle += u"- dni incorrecto\n"
				if not self.string2float(row[2].strip()): #SI NO HAY HE 25%
					detalle += u"- he 25% incorrecto\n"
				if not self.string2float(row[3].strip()): #SI NO HAY HE 35%
					detalle += u"- he 35% incorrecto\n"
				if not self.string2float(row[4].strip()): #SI NO HAY HE 100%
					detalle += u"- he 100% incorrecto\n"
				if not self.string2float(row[5].strip()): #SI NO HE FERIADO DIURNAS
					detalle += u"- he feriado diurnos incorrecto\n"
				if not self.string2float(row[6].strip()): #SI NO HAY HE FERIADOS NOCTURNAS
					detalle += u"- he feriado nocturnos incorrecto\n"
				if not self.string2float(row[7].strip()): #SI NO HAY HE FERIADO
					detalle += u"- he feriado incorrecto\n"
				if not self.string2float(row[8].strip()): #SI NO HAY HE DESCANSO DIURNAS
					detalle += u"- he descanso diurnos incorrecto\n"
				if not self.string2float(row[9].strip()): #SI NO HAY HE DESCANSO NOCTURNAS
					detalle += u"- he descanso nocturnos incorrecto\n"
				if not self.string2float(row[10].strip()): #SI NO HAY DIAS DE FALTAS
					detalle += u"- días de faltas incorrecto\n"
				if not self.string2float(row[11].strip()): #SI NO HAY DIAS SUSPENSION IMPERFECTAS
					detalle += u"- días suspensión imperfectas incorrecto\n"
				if not self.string2float(row[12].strip()): #SI NO HAY TARDANZA HORAS
					detalle += u"- tardanzas horas incorrecta\n"
				if not self.string2float(row[13].strip()): #SI NO HAY remuneración permanente
					detalle += u"- remuneración permanente incorrecta\n"
				if not self.string2float(row[14].strip()): #SI NO HAY asignación familiar
					detalle += u"- asignación familiar incorrecto\n"
				if not self.string2float(row[15].strip()): #SI NO HAY vacaciones truncas
					detalle += u"- vacaciones truncas incorrecto\n"
				if not self.string2float(row[16].strip()): #SI NO HAY condiciones de trabajo
					detalle += u"- condiciones de trabajo incorrecto\n"
				if not self.string2float(row[17].strip()): #SI NO HAY gratificación proporcional
					detalle += u"- gratificación proporcional incorrecto\n"
				if not self.string2float(row[18].strip()): #SI NO HAY bonificación de gratificación
					detalle += u"- bonificación de gratificación incorrecto\n"
				if not self.string2float(row[19].strip()): #SI NO HAY C.T.S.
					detalle += u"- C.T.S. incorrecto\n"
				if not self.string2float(row[20].strip()): #SI NO HAY RMB
					detalle += u"- RMB incorrecto\n"
				if not self.string2float(row[21].strip()): #SI NO HAY importe aporte
					detalle += u"- importe aporte incorrecto\n"
				if not self.string2float(row[22].strip()): #SI NO HAY importe prima
					detalle += u"- importe prima incorrecto\n"
				if not self.string2float(row[23].strip()): #SI NO HAY importe comisión
					detalle += u"- importe comisión incorrecto\n"
				if not self.string2float(row[24].strip()): #SI NO HAY renta 5ta categoría
					detalle += u"- renta 5ta categoría incorrecto\n"
				if not self.string2float(row[25].strip()): #SI NO HAY adelantos de sueldo
					detalle += u"- adelantos de sueldo incorrecto\n"
				if not self.string2float(row[26].strip()): #SI NO HAY total descuentos
					detalle += u"- total descuentos incorrecto\n"
				if not self.string2float(row[27].strip()): #SI NO HAY neto a pagar
					detalle += u"- neto a pagar incorrecto\n"
				if not self.string2float(row[28].strip()): #SI NO HAY essalud 9%
					detalle += u"- essalud 9% incorrecto\n"
				if not self.string2float(row[29].strip()): #SI NO HAY total aportación
					detalle += u"- total aportación incorrecto\n"
				if not self.string2float(row[30].strip()): #SI NO HAY he 25% grilla
					detalle += u"- he 25% grilla incorrecto\n"
				if not self.string2float(row[31].strip()): #SI NO HAY he 35% grilla
					detalle += u"- he 35% grilla incorrecto\n"
				if not self.string2float(row[32].strip()): #SI NO HAY he 100% grilla
					detalle += u"- he 100% grilla incorrecto\n"
				if not self.string2float(row[33].strip()): #SI NO HAY COMISIONES
					detalle += u"- COMISIONES incorrecto\n"
				if not self.string2float(row[34].strip()): #SI NO HAY VACACIONES
					detalle += u"- VACACIONES incorrecto\n"
				if not self.string2float(row[35].strip()): #SI NO HAY MOVILIDAD
					detalle += u"- MOVILIDAD incorrecto\n"
				if not self.string2float(row[36].strip()): #SI NO HAY REEMBOLSO DE MOVILIDAD
					detalle += u"- REEMBOLSO DE MOVILIDAD incorrecto\n"
				if not self.string2float(row[37].strip()): #SI NO HAY ONP
					detalle += u"- ONP incorrecto\n"
				if not self.string2float(row[38].strip()): #SI NO HAY ALIMENTACION
					detalle += u"- ALIMENTACION incorrecto\n"
				if not self.string2float(row[39].strip()): #SI NO HAY INDEMNIZACION DE VACACIONES
					detalle += u"- INDEMNIZACION DE VACACIONES incorrecto\n"
				if not self.string2float(row[40].strip()): #SI NO HAY SUBSIDIO MATERNIDAD
					detalle += u"- SUBSIDIO MATERNIDAD incorrecto\n"
				if not self.string2float(row[41].strip()): #SI NO HAY SUBSIDIO INCAPACIDAD
					detalle += u"- SUBSIDIO INCAPACIDAD incorrecto\n"
				if not self.string2float(row[42].strip()): #SI NO HAY GRATIFICACION
					detalle += u"- GRATIFICACION incorrecto\n"
				if not self.string2float(row[43].strip()): #SI NO HAY BONO DE GRATIFICACION
					detalle += u"- BONO DE GRATIFICACION incorrecto\n"
				if not self.string2float(row[44].strip()): #SI NO HAY CTS
					detalle += u"- CTS incorrecto\n"
				if not self.string2float(row[45].strip()): #SI NO HAY NETO SUELDO
					detalle += u"- NETO SUELDO incorrecto\n"
				if not self.string2float(row[46].strip()): #SI NO HAY NETO VACACIONES
					detalle += u"- NETO VACACIONES incorrecto\n"
				if not self.string2float(row[47].strip()): #SI NO HAY bonificación regular
					detalle += u"- bonificación regular incorrecto\n"
				if not self.string2float(row[48].strip()): #SI NO HAY 1ro de mayo
					detalle += u"- 1ro de mayo incorrecto\n"
				if not self.string2float(row[49].strip()): #SI NO HAY compensación vacacional
					detalle += u"- compensación vacacional incorrecto\n"
				if not self.string2float(row[50].strip()): #SI NO HAY remuneración practicante
					detalle += u"- remuneración practicante incorrecto\n"
				if not self.string2float(row[51].strip()): #SI NO HAY canasta
					detalle += u"- canasta incorrecto\n"
				if not self.string2float(row[52].strip()): #SI NO HAY reintegro
					detalle += u"- reintegro incorrecto\n"
				if not self.string2float(row[53].strip()): #SI NO HAY gratificación extraordinaria
					detalle += u"- gratificación extraordinaria incorrecto\n"
				if not self.string2float(row[54].strip()): #SI NO HAY participación de utilidades
					detalle += u"- participación de utilidades incorrecto\n"
				if not self.string2float(row[55].strip()): #SI NO HAY tardanza
					detalle += u"- tardanza incorrecto\n"
				if not self.string2float(row[56].strip()): #SI NO HAY inasistencia
					detalle += u"- inasistencia incorrecto\n"
				if not self.string2float(row[57].strip()): #SI NO HAY permisos dscto. autorizado
					detalle += u"- permisos dscto. autorizado incorrecto\n"
				if not self.string2float(row[58].strip()): #SI NO HAY dscto. dominical
					detalle += u"- dscto. dominical incorrecto\n"
				if not self.string2float(row[59].strip()): #SI NO HAY spp voluntaria
					detalle += u"- spp voluntaria incorrecto\n"
				if not self.string2float(row[60].strip()): #SI NO HAY essalud vida
					detalle += u"- essalud vida incorrecto\n"
				if not self.string2float(row[61].strip()): #SI NO HAY retencion judicial
					detalle += u"- retencion judicial incorrecto\n"
				if not self.string2float(row[62].strip()): #SI NO HAY fondo de jubilacion
					detalle += u"- fondo de jubilacion incorrecto\n"
				if not self.string2float(row[63].strip()): #SI NO HAY otros dsctos. eps
					detalle += u"- otros dsctos. eps incorrecto\n"
				if not self.string2float(row[64].strip()): #SI NO HAY sctr pension
					detalle += u"- sctr pension incorrecto\n"
				if not self.string2float(row[65].strip()): #SI NO HAY eps
					detalle += u"- eps incorrecto\n"
				if not self.string2float(row[66].strip()): #SI NO HAY senati
					detalle += u"- senati incorrecto\n"
				if not self.string2float(row[67].strip()): #SI NO HAY spp aportación voluntaria
					detalle += u"- spp aportación voluntaria incorrecto\n"
				if not self.string2float(row[68].strip()): #SI NO HAY afp 2% empleado
					detalle += u"- afp 2% empleado incorrecto\n"
				if not self.string2float(row[69].strip()): #SI NO HAY prestamos
					detalle += u"- prestamos incorrecto\n"
				if not self.string2float(row[70].strip()): #SI NO HAY afp 2% trabajador
					detalle += u"- afp 2% trabajador incorrecto\n"
				if not self.string2float(row[71].strip()): #SI NO HAY dias laborados
					detalle += u"- dias laborados incorrecto\n"
				if not self.string2float(row[72].strip()): #SI NO HAY dias subsidiados
					detalle += u"- dias subsidiados incorrecto\n"
				if not self.string2float(row[73].strip()): #SI NO HAY horas efectivas
					detalle += u"- horas efectivas incorrecto\n"
				if not self.string2float(row[74].strip()): #SI NO HAY dias de vacaciones
					detalle += u"- dias de vacaciones incorrecto\n"
				if not self.string2float(row[75].strip()): #SI NO HAY bonificación por mudanza
					detalle += u"- bonificación por mudanza incorrecto\n"
				if not self.string2float(row[76].strip()): #SI NO HAY otros descuentos
					detalle += u"- otros descuentos incorrecto\n"
				if not self.string2float(row[77].strip()): #SI NO HAY feriados trabajados
					detalle += u"- feriados trabajados incorrecto\n"

				if len(detalle):
					vals = {
						'importador_id': self.id,
						
						'periodo'      : row[0],
						'dni'          : row[1],
						'he_25'        : row[2],
						'he_35'        : row[3],
						'he_100'       : row[4],
						'he_fer_duir'  : row[5],
						'he_fer_noct'  : row[6],
						'he_fer'       : row[7],
						'he_desc_diur' : row[8],
						'he_desc_noct' : row[9],
						'dias_faltas'  : row[10],
						'dias_sus_per' : row[11],
						'tardanzas'    : row[12],
						'rem_perm'     : row[13],
						'asig_fam'     : row[14],
						'vaca_trun'    : row[15],
						'cond_trab'    : row[16],
						'grati_prop'   : row[17],
						'boni_grat'    : row[18],
						'cts_trun'     : row[19],
						'rmb'          : row[20],
						'impo_apor'    : row[21],
						'impo_prim'    : row[22],
						'impo_comi'    : row[23],
						'renta_5c'     : row[24],
						'adelanto'     : row[25],
						'tot_desc'     : row[26],
						'neto'         : row[27],
						'essalud'      : row[28],
						'tot_apor'     : row[29],
						'he25'         : row[30],
						'he35'         : row[31],
						'he100'        : row[32],
						'comision'     : row[33],
						'vacacion'     : row[34],
						'movilidad'    : row[35],
						'reembolso_mov': row[36],
						'onp'          : row[37],
						'alimetacion'  : row[38],
						'indem_vaca'   : row[39],
						'subsid_mat'   : row[40],
						'subsid_inca'  : row[41],
						'grati'        : row[42],
						'bono_grati'   : row[43],
						'cts'          : row[44],
						'neto_sueldo'  : row[45],
						'neto_vaca'    : row[46],
						'bon_regular'  : row[47],
						'primero_mayo' : row[48],
						'comp_vaca'    : row[49],
						'rem_practica' : row[50],
						'canasta'      : row[51],
						'reintegro'    : row[52],
						'grati_extra'  : row[53],
						'part_utilidad': row[54],
						'tardanza'     : row[55],
						'inasistencia' : row[56],
						'dsto_auto'    : row[57],
						'dsto_dominic' : row[58],
						'spp_volunt'   : row[59],
						'essalud_vida' : row[60],
						'ret_judicial' : row[61],
						'fondo_jubi'   : row[62],
						'dsto_eps'     : row[63],
						'sctr_pension' : row[64],
						'eps'          : row[65],
						'senati'       : row[66],
						'spp_aporta'   : row[67],
						'afp_2p_emp'   : row[68],
						'prestamos'    : row[69],
						'afp_2p_trab'  : row[70],
						'dias_labor'   : row[71],
						'dias_subs'    : row[72],
						'horas_efect'  : row[73],
						'dias_vaca'    : row[74],
						'boni_mudanza' : row[75],
						'otros_descu'  : row[76],
						'feriados_trab': row[77],
						'detalle'      : detalle,
					}
					self.env['tareo.no.importado'].create(vals)
				else:
					# VALIDACIONES SECUNDARIAS
					ht = self.env['hr.tareo'].search([('periodo.code','=',row[0].strip())])
					if len(ht) > 0:
						ht = ht[0]
					else:
						ap = self.env['account.period'].search([('code','=',row[0].strip())])[0]
						ht = self.env['hr.tareo'].create({'periodo':ap.id})

					htl = self.env['hr.tareo.line'].search([('employee_id.identification_id','=',row[1].strip()),('tareo_id','=',ht.id)])
					if len(htl):
						htl = htl[0]
					else:
						he_e = self.env['hr.employee'].search([('identification_id','=',row[1].strip())])[0]
						awt = self.env['add.worker.tareo'].create({'employee':he_e.id})
						awt.with_context({'active_id':ht.id}).new_worker()
						htl = self.env['hr.tareo.line'].search([('employee_id.identification_id','=',row[1].strip()),('tareo_id','=',ht.id)])[0]

					he25          = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','007')])
					he35          = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','008')])
					he100         = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','009')])
					rem_perm      = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','001')])
					asig_fam      = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','002')])
					vaca_trun     = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','006')])
					cond_trab     = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','057')])
					grati_prop    = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','019')])
					boni_grat     = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','058')])
					cts_trun      = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','059')])
					rmb           = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','047')])
					impo_apor     = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','029')])
					impo_prim     = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','030')])
					impo_comi     = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','031')])
					renta_5c      = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','033')])
					adelanto      = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','045')])
					tot_desc      = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','048')])
					neto          = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','049')])
					essalud       = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','038')])
					tot_apor      = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','054')])
					comision      = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','011')])
					vacacion      = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','004')])
					movi          = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','013')])
					reem_mov      = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','060')])
					onp           = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','028')])
					alimetacion   = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','061')])
					indem_vaca    = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','014')])
					subsid_mat    = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','022')])
					subsid_inca   = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','023')])
					grati         = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','018')])
					bono_grati    = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','020')])
					cts           = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','017')])
					neto_sueldo   = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','050')])
					neto_vaca     = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','051')])
					bon_regular   = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','010')])
					primero_mayo  = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','003')])
					comp_vaca     = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','005')])
					rem_practica  = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','012')])
					canasta       = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','015')])
					reintegro     = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','016')])
					grati_extra   = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','021')])
					part_utilidad = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','056')])
					tardanza      = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','024')])
					inasistencia  = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','025')])
					dsto_auto     = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','026')])
					dsto_dominic  = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','027')])
					spp_volunt    = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','032')])
					essalud_vida  = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','034')])
					ret_judicial  = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','035')])
					fondo_jubi    = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','036')])
					dsto_eps      = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','037')])
					sctr_pension  = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','039')])
					eps           = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','040')])
					senati        = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','041')])
					spp_aporta    = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','043')])
					afp_2p_emp    = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','044')])
					prestamos     = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','046')])
					afp_2p_trab   = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','055')])
					boni_mudanza  = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','062')])
					otros_descu   = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','064')])
					feriados_trab = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','063')])

					if len(rem_perm) > 0:
						rem_perm[0].monto = float(row[13])
					if len(asig_fam) > 0:
						asig_fam[0].monto = float(row[14])
					if len(vaca_trun) > 0:
						vaca_trun[0].monto = float(row[15])
					if len(cond_trab) > 0:
						cond_trab[0].monto = float(row[16])
					if len(grati_prop) > 0:
						grati_prop[0].monto = float(row[17])
					if len(boni_grat) > 0:
						boni_grat[0].monto = float(row[18])
					if len(cts_trun) > 0:
						cts_trun[0].monto = float(row[19])
					if len(rmb) > 0:
						rmb[0].monto = float(row[20])
					if len(impo_apor) > 0:
						impo_apor[0].monto = float(row[21])
					if len(impo_prim) > 0:
						impo_prim[0].monto = float(row[22])
					if len(impo_comi) > 0:
						impo_comi[0].monto = float(row[23])
					if len(renta_5c) > 0:
						renta_5c[0].monto = float(row[24])
					if len(adelanto) > 0:
						adelanto[0].monto = float(row[25])
					if len(tot_desc) > 0:
						tot_desc[0].monto = float(row[26])
					if len(neto) > 0:
						neto[0].monto = float(row[27])
					if len(essalud) > 0:
						essalud[0].monto = float(row[28])
					if len(tot_apor) > 0:
						tot_apor[0].monto = float(row[29])
					if len(he25) > 0:
						he25[0].monto = float(row[30])
					if len(he35) > 0:
						he35[0].monto = float(row[31])
					if len(he100) > 0:
						he100[0].monto = float(row[32])
					if len(comision) > 0:
						comision[0].monto = float(row[33])
					if len(vacacion) > 0:
						vacacion[0].monto = float(row[34])
					if len(movi) > 0:
						movi[0].monto = float(row[35])
					if len(reem_mov) > 0:
						reem_mov[0].monto = float(row[36])
					if len(onp) > 0:
						onp[0].monto = float(row[37])
					if len(alimetacion) > 0:
						alimetacion[0].monto = float(row[38])
					if len(indem_vaca) > 0:
						indem_vaca[0].monto = float(row[39])
					if len(subsid_mat) > 0:
						subsid_mat[0].monto = float(row[40])
					if len(subsid_inca) > 0:
						subsid_inca[0].monto = float(row[41])
					if len(grati) > 0:
						grati[0].monto = float(row[42])
					if len(bono_grati) > 0:
						bono_grati[0].monto = float(row[43])
					if len(cts) > 0:
						cts[0].monto = float(row[44])
					if len(neto_sueldo) > 0:
						neto_sueldo[0].monto = float(row[45])
					if len(neto_vaca) > 0:
						neto_vaca[0].monto = float(row[46])
					if len(bon_regular) > 0:
						bon_regular[0].monto = float(row[47])
					if len(primero_mayo) > 0:
						primero_mayo[0].monto = float(row[48])
					if len(comp_vaca) > 0:
						comp_vaca[0].monto = float(row[49])
					if len(rem_practica) > 0:
						rem_practica[0].monto = float(row[50])
					if len(canasta) > 0:
						canasta[0].monto = float(row[51])
					if len(reintegro) > 0:
						reintegro[0].monto = float(row[52])
					if len(grati_extra) > 0:
						grati_extra[0].monto = float(row[53])
					if len(part_utilidad) > 0:
						part_utilidad[0].monto = float(row[54])
					if len(tardanza) > 0:
						tardanza[0].monto = float(row[55])
					if len(inasistencia) > 0:
						inasistencia[0].monto = float(row[56])
					if len(dsto_auto) > 0:
						dsto_auto[0].monto = float(row[57])
					if len(dsto_dominic) > 0:
						dsto_dominic[0].monto = float(row[58])
					if len(spp_volunt) > 0:
						spp_volunt[0].monto = float(row[59])
					if len(essalud_vida) > 0:
						essalud_vida[0].monto = float(row[60])
					if len(ret_judicial) > 0:
						ret_judicial[0].monto = float(row[61])
					if len(fondo_jubi) > 0:
						fondo_jubi[0].monto = float(row[62])
					if len(dsto_eps) > 0:
						dsto_eps[0].monto = float(row[63])
					if len(sctr_pension) > 0:
						sctr_pension[0].monto = float(row[64])
					if len(eps) > 0:
						eps[0].monto = float(row[65])
					if len(senati) > 0:
						senati[0].monto = float(row[66])
					if len(spp_aporta) > 0:
						spp_aporta[0].monto = float(row[67])
					if len(afp_2p_emp) > 0:
						afp_2p_emp[0].monto = float(row[68])
					if len(prestamos) > 0:
						prestamos[0].monto = float(row[69])
					if len(afp_2p_trab) > 0:
						afp_2p_trab[0].monto = float(row[70])
					if len(boni_mudanza) > 0:
						boni_mudanza[0].monto = float(row[75])
					if len(otros_descu) > 0:
						otros_descu[0].monto = float(row[76])
					if len(feriados_trab) > 0:
						feriados_trab[0].monto = float(row[77])

					htl.horas_extra_diurna             = float(row[2])
					htl.horas_extra_nocturna           = float(row[3])
					htl.horas_extra_descanso           = float(row[4])
					htl.horas_extra_feriado_diur       = float(row[5])
					htl.horas_extra_feriado_noct       = float(row[6])
					htl.horas_extra_feriado            = float(row[7])
					htl.horas_extra_descanso_diurnas   = float(row[8])
					htl.horas_extra_descanso_nocturnas = float(row[9])
					htl.dias_suspension_perfecta       = int(float(row[10]))
					htl.dias_suspension_imperfecta     = int(float(row[11]))
					htl.tardanza_horas                 = float(row[12])
					htl.dias_trabajador                = int(float(row[71]))
					htl.num_days_subs                  = int(float(row[72]))
					htl.horas_ordinarias_trabajadas    = float(row[73])
					htl.dias_vacaciones                = float(row[74])
		self.imported = True
		self.state = 'imported'

	@api.one
	def procesar(self):
		for line in self.noimp_lines:
			# VALIDACIONES SECUNDARIAS
			detalle = ""

			if line.periodo: #SI NO HAY PERIODO CONTABLE
				if not len(self.env['account.period'].search([('code','=',line.periodo.strip())])):
					detalle += u"- periodo contable incorrecto\n"
			else:
				detalle += u"- periodo contable incorrecto\n"
			if line.dni: #SI NO HAY DNI
				if not len(self.env['hr.employee'].search([('identification_id','=',line.dni.strip())])):
					detalle += u"- dni incorrecto\n"
			else:
				detalle += u"- dni incorrecto\n"				
			if not line.he_25 and not line.importador_id.string2float(line.he_25.strip()): #SI NO HAY HE 25%
				detalle += u"- he 25% incorrecto\n"
			if not line.he_35 and not line.importador_id.string2float(line.he_35.strip()): #SI NO HAY HE 35%
				detalle += u"- he 35% incorrecto\n"
			if not line.he_100 and not line.importador_id.string2float(line.he_100.strip()): #SI NO HAY HE 100%
				detalle += u"- he 100% incorrecto\n"
			if not line.he_fer_duir and not line.importador_id.string2float(line.he_fer_duir.strip()): #SI NO HE FERIADO DIURNAS
				detalle += u"- he feriado diurnos incorrecto\n"
			if not line.he_fer_noct and not line.importador_id.string2float(line.he_fer_noct.strip()): #SI NO HAY HE FERIADOS NOCTURNAS
				detalle += u"- he feriado nocturnos incorrecto\n"
			if not line.he_fer and not line.importador_id.string2float(line.he_fer.strip()): #SI NO HAY HE FERIADO
				detalle += u"- he feriado incorrecto\n"
			if not line.he_desc_diur and not line.importador_id.string2float(line.he_desc_diur.strip()): #SI NO HAY HE DESCANSO DIURNAS
				detalle += u"- he descanso diurnos incorrecto\n"
			if not line.he_desc_noct and not line.importador_id.string2float(line.he_desc_noct.strip()): #SI NO HAY HE DESCANSO NOCTURNAS
				detalle += u"- he descanso nocturnos incorrecto\n"
			if not line.dias_faltas and not line.importador_id.string2float(line.dias_faltas.strip()): #SI NO HAY DIAS DE FALTAS
				detalle += u"- días de faltas incorrecto\n"
			if not line.dias_sus_per and not line.importador_id.string2float(line.dias_sus_per.strip()): #SI NO HAY DIAS SUSPENSION IMPERFECTAS
				detalle += u"- días suspensión imperfectas incorrecto\n"
			if not line.tardanzas and not line.importador_id.string2float(line.tardanzas.strip()): #SI NO HAY TARDANZA HORAS
				detalle += u"- tardanzas horas incorrecta\n"
			if not line.rem_perm and not self.string2float(line.rem_perm.strip()): #SI NO HAY remuneración permanente
				detalle += u"- remuneración permanente incorrecta\n"
			if not line.asig_fam and not self.string2float(line.asig_fam.strip()): #SI NO HAY asignación familiar
				detalle += u"- asignación familiar incorrecto\n"
			if not line.vaca_trun and not self.string2float(line.vaca_trun.strip()): #SI NO HAY vacaciones truncas
				detalle += u"- vacaciones truncas incorrecto\n"
			if not line.cond_trab and not self.string2float(line.cond_trab.strip()): #SI NO HAY condiciones de trabajo
				detalle += u"- condiciones de trabajo incorrecto\n"
			if not line.grati_prop and not self.string2float(line.grati_prop.strip()): #SI NO HAY gratificación proporcional
				detalle += u"- gratificación proporcional incorrecto\n"
			if not line.boni_grat and not self.string2float(line.boni_grat.strip()): #SI NO HAY bonificación de gratificación
				detalle += u"- bonificación de gratificación incorrecto\n"
			if not line.cts_trun and not self.string2float(line.cts_trun.strip()): #SI NO HAY C.T.S.
				detalle += u"- C.T.S. incorrecto\n"
			if not line.rmb and not self.string2float(line.rmb.strip()): #SI NO HAY RMB
				detalle += u"- RMB incorrecto\n"
			if not line.impo_apor and not self.string2float(line.impo_apor.strip()): #SI NO HAY importe aporte
				detalle += u"- importe aporte incorrecto\n"
			if not line.impo_prim and not self.string2float(line.impo_prim.strip()): #SI NO HAY importe prima
				detalle += u"- importe prima incorrecto\n"
			if not line.impo_comi and not self.string2float(line.impo_comi.strip()): #SI NO HAY importe comisión
				detalle += u"- importe comisión incorrecto\n"
			if not line.renta_5c and not self.string2float(line.renta_5c.strip()): #SI NO HAY renta 5ta categoría
				detalle += u"- renta 5ta categoría incorrecto\n"
			if not line.adelanto and not self.string2float(line.adelanto.strip()): #SI NO HAY adelantos de sueldo
				detalle += u"- adelantos de sueldo incorrecto\n"
			if not line.tot_desc and not self.string2float(line.tot_desc.strip()): #SI NO HAY total descuentos
				detalle += u"- total descuentos incorrecto\n"
			if not line.neto and not self.string2float(line.neto.strip()): #SI NO HAY neto a pagar
				detalle += u"- neto a pagar incorrecto\n"
			if not line.essalud and not self.string2float(line.essalud.strip()): #SI NO HAY essalud 9%
				detalle += u"- essalud 9% incorrecto\n"
			if not line.tot_apor and not self.string2float(line.tot_apor.strip()): #SI NO HAY total aportación
				detalle += u"- total aportación incorrecto\n"
			if not line.he25 and not self.string2float(line.he25.strip()): #SI NO HAY he 25% grilla
				detalle += u"- he 25% grilla incorrecto\n"
			if not line.he35 and not self.string2float(line.he35.strip()): #SI NO HAY he 35% grilla
				detalle += u"- he 35% grilla incorrecto\n"
			if not line.he100 and not self.string2float(line.he100.strip()): #SI NO HAY he 100% grilla
				detalle += u"- he 100% grilla incorrecto\n"
			if not line.comision and not self.string2float(line.comision.strip()): #SI NO HAY COMISIONES
				detalle += u"- COMISIONES incorrecto\n"
			if not line.vacacion and not self.string2float(line.vacacion.strip()): #SI NO HAY VACACIONES
				detalle += u"- VACACIONES incorrecto\n"
			if not line.movilidad and not self.string2float(line.movilidad.strip()): #SI NO HAY MOVILIDAD
				detalle += u"- MOVILIDAD incorrecto\n"
			if not line.reembolso_mov and not self.string2float(line.reembolso_mov.strip()): #SI NO HAY REEMBOLSO DE MOVILIDAD
				detalle += u"- REEMBOLSO DE MOVILIDAD incorrecto\n"
			if not line.onp and not self.string2float(line.onp.strip()): #SI NO HAY ONP
				detalle += u"- ONP incorrecto\n"
			if not line.alimetacion and not self.string2float(line.alimetacion.strip()): #SI NO HAY ALIMENTACION
				detalle += u"- ALIMENTACION incorrecto\n"
			if not line.indem_vaca and not self.string2float(line.indem_vaca.strip()): #SI NO HAY INDEMNIZACION DE VACACIONES
				detalle += u"- INDEMNIZACION DE VACACIONES incorrecto\n"
			if not line.subsid_mat and not self.string2float(line.subsid_mat.strip()): #SI NO HAY SUBSIDIO MATERNIDAD
				detalle += u"- SUBSIDIO MATERNIDAD incorrecto\n"
			if not line.subsid_inca and not self.string2float(line.subsid_inca.strip()): #SI NO HAY SUBSIDIO INCAPACIDAD
				detalle += u"- SUBSIDIO INCAPACIDAD incorrecto\n"
			if not line.grati and not self.string2float(line.grati.strip()): #SI NO HAY GRATIFICACION
				detalle += u"- GRATIFICACION incorrecto\n"
			if not line.bono_grati and not self.string2float(line.bono_grati.strip()): #SI NO HAY BONO DE GRATIFICACION
				detalle += u"- BONO DE GRATIFICACION incorrecto\n"
			if not line.cts and not self.string2float(line.cts.strip()): #SI NO HAY CTS
				detalle += u"- CTS incorrecto\n"
			if not line.neto_sueldo and not self.string2float(line.neto_sueldo.strip()): #SI NO HAY NETO SUELDO
				detalle += u"- NETO SUELDO incorrecto\n"
			if not line.neto_vaca and not self.string2float(line.neto_vaca.strip()): #SI NO HAY NETO VACACIONES
				detalle += u"- NETO VACACIONES incorrecto\n"
			if not line.bon_regular and not self.string2float(line.bon_regular.strip()): #SI NO HAY bonificación regular
				detalle += u"- bonificación regular incorrecto\n"
			if not line.primero_mayo and not self.string2float(line.primero_mayo.strip()): #SI NO HAY 1ro de mayo
				detalle += u"- 1ro de mayo incorrecto\n"
			if not line.comp_vaca and not self.string2float(line.comp_vaca.strip()): #SI NO HAY compensación vacacional
				detalle += u"- compensación vacacional incorrecto\n"
			if not line.rem_practica and not self.string2float(line.rem_practica.strip()): #SI NO HAY remuneración practicante
				detalle += u"- remuneración practicante incorrecto\n"
			if not line.canasta and not self.string2float(line.canasta.strip()): #SI NO HAY canasta
				detalle += u"- canasta incorrecto\n"
			if not line.reintegro and not self.string2float(line.reintegro.strip()): #SI NO HAY reintegro
				detalle += u"- reintegro incorrecto\n"
			if not line.grati_extra and not self.string2float(line.grati_extra.strip()): #SI NO HAY gratificación extraordinaria
				detalle += u"- gratificación extraordinaria incorrecto\n"
			if not line.part_utilidad and not self.string2float(line.part_utilidad.strip()): #SI NO HAY participación de utilidades
				detalle += u"- participación de utilidades incorrecto\n"
			if not line.tardanza and not self.string2float(line.tardanza.strip()): #SI NO HAY tardanza
				detalle += u"- tardanza incorrecto\n"
			if not line.inasistencia and not self.string2float(line.inasistencia.strip()): #SI NO HAY inasistencia
				detalle += u"- inasistencia incorrecto\n"
			if not line.dsto_auto and not self.string2float(line.dsto_auto.strip()): #SI NO HAY permisos dscto. autorizado
				detalle += u"- permisos dscto. autorizado incorrecto\n"
			if not line.dsto_dominic and not self.string2float(line.dsto_dominic.strip()): #SI NO HAY dscto. dominical
				detalle += u"- dscto. dominical incorrecto\n"
			if not line.spp_volunt and not self.string2float(line.spp_volunt.strip()): #SI NO HAY spp voluntaria
				detalle += u"- spp voluntaria incorrecto\n"
			if not line.essalud_vida and not self.string2float(line.essalud_vida.strip()): #SI NO HAY essalud vida
				detalle += u"- essalud vida incorrecto\n"
			if not line.ret_judicial and not self.string2float(line.ret_judicial.strip()): #SI NO HAY retencion judicial
				detalle += u"- retencion judicial incorrecto\n"
			if not line.fondo_jubi and not self.string2float(line.fondo_jubi.strip()): #SI NO HAY fondo de jubilacion
				detalle += u"- fondo de jubilacion incorrecto\n"
			if not line.dsto_eps and not self.string2float(line.dsto_eps.strip()): #SI NO HAY otros dsctos. eps
				detalle += u"- otros dsctos. eps incorrecto\n"
			if not line.sctr_pension and not self.string2float(line.sctr_pension.strip()): #SI NO HAY sctr pension
				detalle += u"- sctr pension incorrecto\n"
			if not line.eps and not self.string2float(line.eps.strip()): #SI NO HAY eps
				detalle += u"- eps incorrecto\n"
			if not line.senati and not self.string2float(line.senati.strip()): #SI NO HAY senati
				detalle += u"- senati incorrecto\n"
			if not line.spp_aporta and not self.string2float(line.spp_aporta.strip()): #SI NO HAY spp aportación voluntaria
				detalle += u"- spp aportación voluntaria incorrecto\n"
			if not line.afp_2p_emp and not self.string2float(line.afp_2p_emp.strip()): #SI NO HAY afp 2% empleado
				detalle += u"- afp 2% empleado incorrecto\n"
			if not line.prestamos and not self.string2float(line.prestamos.strip()): #SI NO HAY prestamos
				detalle += u"- prestamos incorrecto\n"
			if not line.afp_2p_trab and not self.string2float(line.afp_2p_trab.strip()): #SI NO HAY afp 2% trabajador
				detalle += u"- afp 2% trabajador incorrecto\n"
			if not line.dias_labor and not self.string2float(line.dias_labor.strip()): #SI NO HAY dias laborados
				detalle += u"- dias laborados incorrecto\n"
			if not line.dias_subs and not self.string2float(line.dias_subs.strip()): #SI NO HAY dias subsidiados
				detalle += u"- dias subsidiados incorrecto\n"
			if not line.horas_efect and not self.string2float(line.horas_efect.strip()): #SI NO HAY horas efectivas
				detalle += u"- horas efectivas incorrecto\n"
			if not line.dias_vaca and not self.string2float(line.dias_vaca.strip()): #SI NO HAY dias de vacaciones
				detalle += u"- dias de vacaciones incorrecto\n"

			if len(detalle):
				self.detalle = detalle
			else:
				ht = self.env['hr.tareo'].search([('periodo.code','=',line.periodo.strip())])
				if len(ht) > 0:
					ht = ht[0]
				else:
					ap = self.env['account.period'].search([('code','=',line.periodo.strip())])[0]
					ht = self.env['hr.tareo'].create({'periodo':ap.id})

				htl = self.env['hr.tareo.line'].search([('employee_id.identification_id','=',line.dni.strip()),('tareo_id','=',ht.id)])
				if len(htl):
					htl = htl[0]
				else:
					he_e = self.env['hr.employee'].search([('identification_id','=',line.dni.strip())])[0]
					awt = self.env['add.worker.tareo'].create({'employee':he_e.id})
					awt.with_context({'active_id':ht.id}).new_worker()
					htl = self.env['hr.tareo.line'].search([('employee_id.identification_id','=',line.dni.strip()),('tareo_id','=',ht.id)])[0]

				he25          = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','007')])
				he35          = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','008')])
				he100         = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','009')])
				rem_perm      = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','001')])
				asig_fam      = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','002')])
				vaca_trun     = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','006')])
				cond_trab     = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','057')])
				grati_prop    = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','019')])
				boni_grat     = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','058')])
				cts_trun      = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','059')])
				rmb           = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','047')])
				impo_apor     = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','029')])
				impo_prim     = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','030')])
				impo_comi     = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','031')])
				renta_5c      = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','033')])
				adelanto      = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','045')])
				tot_desc      = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','048')])
				neto          = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','049')])
				essalud       = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','038')])
				tot_apor      = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','054')])
				comision      = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','011')])
				vacacion      = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','004')])
				movilidad     = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','013')])
				reembolso_mov = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','060')])
				onp           = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','028')])
				alimetacion   = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','061')])
				indem_vaca    = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','014')])
				subsid_mat    = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','022')])
				subsid_inca   = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','023')])
				grati         = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','018')])
				bono_grati    = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','020')])
				cts           = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','017')])
				neto_sueldo   = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','050')])
				neto_vaca     = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','051')])
				bon_regular   = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','010')])
				primero_mayo  = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','003')])
				comp_vaca     = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','005')])
				rem_practica  = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','012')])
				canasta       = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','015')])
				reintegro     = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','016')])
				grati_extra   = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','021')])
				part_utilidad = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','056')])
				tardanza      = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','024')])
				inasistencia  = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','025')])
				dsto_auto     = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','026')])
				dsto_dominic  = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','027')])
				spp_volunt    = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','032')])
				essalud_vida  = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','034')])
				ret_judicial  = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','035')])
				fondo_jubi    = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','036')])
				dsto_eps      = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','037')])
				sctr_pension  = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','039')])
				eps           = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','040')])
				senati        = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','041')])
				spp_aporta    = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','043')])
				afp_2p_emp    = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','044')])
				prestamos     = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','046')])
				afp_2p_trab   = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','055')])
				boni_mudanza  = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','062')])
				otros_descu   = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','064')])
				feriados_trab = self.env['hr.concepto.line'].search([('tareo_line_id','=',htl.id),('concepto_id.code','=','063')])

				if len(rem_perm) > 0:
					rem_perm[0].monto = float(line.rem_perm)
				if len(asig_fam) > 0:
					asig_fam[0].monto = float(line.asig_fam)
				if len(vaca_trun) > 0:
					vaca_trun[0].monto = float(line.vaca_trun)
				if len(cond_trab) > 0:
					cond_trab[0].monto = float(line.cond_trab)
				if len(grati_prop) > 0:
					grati_prop[0].monto = float(line.grati_prop)
				if len(boni_grat) > 0:
					boni_grat[0].monto = float(line.boni_grat)
				if len(cts_trun) > 0:
					cts_trun[0].monto = float(line.cts_trun)
				if len(rmb) > 0:
					rmb[0].monto = float(line.rmb)
				if len(impo_apor) > 0:
					impo_apor[0].monto = float(line.impo_apor)
				if len(impo_prim) > 0:
					impo_prim[0].monto = float(line.impo_prim)
				if len(impo_comi) > 0:
					impo_comi[0].monto = float(line.impo_comi)
				if len(renta_5c) > 0:
					renta_5c[0].monto = float(line.renta_5c)
				if len(adelanto) > 0:
					adelanto[0].monto = float(line.adelanto)
				if len(tot_desc) > 0:
					tot_desc[0].monto = float(line.tot_desc)
				if len(neto) > 0:
					neto[0].monto = float(line.neto)
				if len(essalud) > 0:
					essalud[0].monto = float(line.essalud)
				if len(tot_apor) > 0:
					tot_apor[0].monto = float(line.tot_apor)
				if len(he25) > 0:
					he25[0].monto = float(line.he25)
				if len(he35) > 0:
					he35[0].monto = float(line.he35)
				if len(he100) > 0:
					he100[0].monto = float(line.he100)
				if len(comision) > 0:
					comision[0].monto = float(line.comision)
				if len(vacacion) > 0:
					vacacion[0].monto = float(line.vacacion)
				if len(movilidad) > 0:
					movilidad[0].monto = float(line.movilidad)
				if len(reembolso_mov) > 0:
					reembolso_mov[0].monto = float(line.reembolso_mov)
				if len(onp) > 0:
					onp[0].monto = float(line.onp)
				if len(alimetacion) > 0:
					alimetacion[0].monto = float(line.alimetacion)
				if len(indem_vaca) > 0:
					indem_vaca[0].monto = float(line.indem_vaca)
				if len(subsid_mat) > 0:
					subsid_mat[0].monto = float(line.subsid_mat)
				if len(subsid_inca) > 0:
					subsid_inca[0].monto = float(line.subsid_inca)
				if len(grati) > 0:
					grati[0].monto = float(line.grati)
				if len(bono_grati) > 0:
					bono_grati[0].monto = float(line.bono_grati)
				if len(cts) > 0:
					cts[0].monto = float(line.cts)
				if len(neto_sueldo) > 0:
					neto_sueldo[0].monto = float(line.neto_sueldo)
				if len(neto_vaca) > 0:
					neto_vaca[0].monto = float(line.neto_vaca)
				if len(bon_regular) > 0:
					bon_regular[0].monto = float(line.bon_regular)
				if len(primero_mayo) > 0:
					primero_mayo[0].monto = float(line.primero_mayo)
				if len(comp_vaca) > 0:
					comp_vaca[0].monto = float(line.comp_vaca)
				if len(rem_practica) > 0:
					rem_practica[0].monto = float(line.rem_practica)
				if len(canasta) > 0:
					canasta[0].monto = float(line.canasta)
				if len(reintegro) > 0:
					reintegro[0].monto = float(line.reintegro)
				if len(grati_extra) > 0:
					grati_extra[0].monto = float(line.grati_extra)
				if len(part_utilidad) > 0:
					part_utilidad[0].monto = float(line.part_utilidad)
				if len(tardanza) > 0:
					tardanza[0].monto = float(line.tardanza)
				if len(inasistencia) > 0:
					inasistencia[0].monto = float(line.inasistencia)
				if len(dsto_auto) > 0:
					dsto_auto[0].monto = float(line.dsto_auto)
				if len(dsto_dominic) > 0:
					dsto_dominic[0].monto = float(line.dsto_dominic)
				if len(spp_volunt) > 0:
					spp_volunt[0].monto = float(line.spp_volunt)
				if len(essalud_vida) > 0:
					essalud_vida[0].monto = float(line.essalud_vida)
				if len(ret_judicial) > 0:
					ret_judicial[0].monto = float(line.ret_judicial)
				if len(fondo_jubi) > 0:
					fondo_jubi[0].monto = float(line.fondo_jubi)
				if len(dsto_eps) > 0:
					dsto_eps[0].monto = float(line.dsto_eps)
				if len(sctr_pension) > 0:
					sctr_pension[0].monto = float(line.sctr_pension)
				if len(eps) > 0:
					eps[0].monto = float(line.eps)
				if len(senati) > 0:
					senati[0].monto = float(line.senati)
				if len(spp_aporta) > 0:
					spp_aporta[0].monto = float(line.spp_aporta)
				if len(afp_2p_emp) > 0:
					afp_2p_emp[0].monto = float(line.afp_2p_emp)
				if len(prestamos) > 0:
					prestamos[0].monto = float(line.prestamos)
				if len(afp_2p_trab) > 0:
					afp_2p_trab[0].monto = float(line.afp_2p_trab)
				if len(boni_mudanza) > 0:
					boni_mudanza[0].monto = float(line.boni_mudanza)
				if len(otros_descu) > 0:
					otros_descu[0].monto = float(line.otros_descu)
				if len(feriados_trab) > 0:
					feriados_trab[0].monto = float(line.feriados_trab)

				htl.horas_extra_diurna             = float(line.he_25)
				htl.horas_extra_nocturna           = float(line.he_35)
				htl.horas_extra_descanso           = float(line.he_100)
				htl.horas_extra_feriado_diur       = float(line.he_fer_duir)
				htl.horas_extra_feriado_noct       = float(line.he_fer_noct)
				htl.horas_extra_feriado            = float(line.he_fer)
				htl.horas_extra_descanso_diurnas   = float(line.he_desc_diur)
				htl.horas_extra_descanso_nocturnas = float(line.he_desc_noct)
				htl.dias_suspension_perfecta       = int(float(line.dias_faltas))
				htl.dias_suspension_imperfecta     = int(float(line.dias_sus_per))
				htl.tardanza_horas                 = float(line.tardanzas)
				htl.dias_trabajador                = int(float(line.dias_labor))
				htl.num_days_subs                  = int(float(line.dias_subs))
				htl.horas_ordinarias_trabajadas    = float(line.horas_efect)
				htl.dias_vacaciones                = float(line.dias_vaca)

				line.unlink()

	@api.one
	def clean(self):
		for i in self.noimp_lines:
			i.unlink()

class tareo_no_importado(models.Model):
	_name = 'tareo.no.importado'

	importador_id = fields.Many2one('tareo.importador','importador Padre')

	periodo       = fields.Char(u'Periodo Contable')
	dni           = fields.Char(u'DNI')
	he_25         = fields.Char(u'Horas Extras Diurnas')
	he_35         = fields.Char(u'Horas Extras Nocturnas')
	he_100        = fields.Char(u'Horas Extras Descanso')
	he_fer_duir   = fields.Char(u'HE Feriados Diurnas')
	he_fer_noct   = fields.Char(u'HE Feriados Nocturnas')
	he_fer        = fields.Char(u'HE Feriados')
	he_desc_diur  = fields.Char(u'HE Descoanso Diurnas')
	he_desc_noct  = fields.Char(u'HE Descanso Nocturnas')
	dias_faltas   = fields.Char(u'Días de Faltas')
	dias_sus_per  = fields.Char(u'Días Suspensión Imperfecta')
	tardanzas     = fields.Char(u'Tardanza Horas')
	rem_perm      = fields.Char(u'Remuneración Permanente')
	asig_fam      = fields.Char(u'Asignación Familiar')
	vaca_trun     = fields.Char(u'Vacaciones Truncas')
	cond_trab     = fields.Char(u'Condicionas de Trabajo')
	grati_prop    = fields.Char(u'Gratificación Proporcional')
	boni_grat     = fields.Char(u'Bonificación Gratificación')
	cts_trun      = fields.Char(u'C.T.S.')
	rmb           = fields.Char(u'RMB')
	impo_apor     = fields.Char(u'Importe Aporte')
	impo_prim     = fields.Char(u'Importe Prima')
	impo_comi     = fields.Char(u'Importe Comisión')
	renta_5c      = fields.Char(u'Renta 5ta Categoría')
	adelanto      = fields.Char(u'Adelantos Sueldo')
	tot_desc      = fields.Char(u'Total Descuentos')
	neto          = fields.Char(u'Neto a Pagar')
	essalud       = fields.Char(u'EsSalud 9%')
	tot_apor      = fields.Char(u'Total Aportación')
	he25          = fields.Char(u'Horas Extras 25%')
	he35          = fields.Char(u'Horas Extras 35%')
	he100         = fields.Char(u'Horas Extras 100%')
	comision      = fields.Char(u'Comisión')
	vacacion      = fields.Char(u'Vacación')
	movilidad     = fields.Char(u'Movilidad')
	reembolso_mov = fields.Char(u'Reembolso Movilidad')
	onp           = fields.Char(u'ONP')
	alimetacion   = fields.Char(u'Alimentación')
	indem_vaca    = fields.Char(u'Indemnización de Vacaciones')
	subsid_mat    = fields.Char(u'Subsidio Maternidad')
	subsid_inca   = fields.Char(u'Subsidio Incapacidad')
	grati         = fields.Char(u'Gratificación')
	bono_grati    = fields.Char(u'Bono de Gratificación')
	cts           = fields.Char(u'CTS')
	neto_sueldo   = fields.Char(u'Neto Sueldo')
	neto_vaca     = fields.Char(u'Neto Vacaciones')
	bon_regular   = fields.Char(u'Bonificación Regular')
	primero_mayo  = fields.Char(u'Primero de Mayo')
	comp_vaca     = fields.Char(u'Compensación Vacacional')
	rem_practica  = fields.Char(u'Remuneración Practicante')
	canasta       = fields.Char(u'Canasta')
	reintegro     = fields.Char(u'Reintegro')
	grati_extra   = fields.Char(u'Gratifiación Extraordinaria')
	part_utilidad = fields.Char(u'Participación de Utilidades')
	tardanza      = fields.Char(u'Tardanza')
	inasistencia  = fields.Char(u'Inasistencia')
	dsto_auto     = fields.Char(u'Permisos Dscto. Autorizado')
	dsto_dominic  = fields.Char(u'Dscto. Dominical')
	spp_volunt    = fields.Char(u'SPP Voluntaria')
	essalud_vida  = fields.Char(u'EsSalud Vida')
	ret_judicial  = fields.Char(u'Retención Judicial')
	fondo_jubi    = fields.Char(u'Fondo Jubilación')
	dsto_eps      = fields.Char(u'Otros Dsctos. EPS')
	sctr_pension  = fields.Char(u'SCTR Pensión')
	eps           = fields.Char(u'EPS')
	senati        = fields.Char(u'Senati')
	spp_aporta    = fields.Char(u'SPP Aportación Voluntaria')
	afp_2p_emp    = fields.Char(u'AFP 2% Empleado')
	prestamos     = fields.Char(u'Prestamos')
	afp_2p_trab   = fields.Char(u'AFP 2% Trabajador')
	dias_labor	  = fields.Char(u'Días Laborados')
	dias_subs	  = fields.Char(u'Días Subsidiados')
	horas_efect   = fields.Char(u'Horas Efectivas')
	dias_vaca     = fields.Char(u'Días de Vacaciones')
	boni_mudanza  = fields.Char(u'Bonificación por Mudanza')
	otros_descu   = fields.Char(u'Otros Descuentos')
	feriados_trab = fields.Char(u'Feriados Trabajados')
	detalle       = fields.Char(u'Detalle')