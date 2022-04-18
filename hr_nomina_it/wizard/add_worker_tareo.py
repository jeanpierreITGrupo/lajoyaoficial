# -*- encoding: utf-8 -*-
import base64
from openerp import models, fields, api
from openerp.osv import osv

from calendar    import monthrange

class add_worker_tareo(models.TransientModel):
	_name = 'add.worker.tareo'

	employee = fields.Many2one('hr.employee','Trabajador')

	@api.one
	def new_worker(self):
		x=self.env['hr.tareo'].browse(self.env.context['active_id'])
		p=self.env['hr.tareo.line'].search([('tareo_id','=',self.env.context['active_id']),('dni','=',self.employee.identification_id)])
		if len(p)!=0:
			raise osv.except_osv('Alerta', 'El trabajador ya pertenece al tareo')
		if self.employee:
			i = self.employee
			a_f = self.env['hr.parameters'].search([('num_tipo','=','10001')])[0].monto if i.children_number>0 else 0


			act=self.env['hr.tareo'].search([('id','=',self.env.context['active_id'])])
			
			monto_grati=0
			monto_boni_grati=0
			monto_boni_grati_liq=0
			monto_cts=0
			monto_5category=0
			vacaciones=0
			vacaciones_trunca=0
			vacaciones_indem=0
			prestamos=0
			adelantos=0
			monto_grati_trun=0
			cta_prestamo=None

			a_f = self.env['hr.parameters'].search([('num_tipo','=','10001')])[0].monto if i.children_number>0 else 0
			grati=False
			if act.periodo.code[0:2]=='07':
				grati=self.env['hr.reward'].search([('year','=',act.periodo.fiscalyear_id.id),('period','=','07')])
			if act.periodo.code[0:2]=='12':
				grati=self.env['hr.reward'].search([('year','=',act.periodo.fiscalyear_id.id),('period','=','12')])
			gratie=False
			if grati:
				gratie=self.env['hr.reward.line'].search([('reward','=',grati.id),('employee_id','=',i.id)])
			if gratie:
				monto_grati=gratie.total_reward
				monto_boni_grati=gratie.plus_9
			periodo=False
			if act.periodo.code[0:2]=='05':
				periodo='05'
			if act.periodo.code[0:2]=='11':
				periodo='11'
			ctsheader=False
			ctsline=False
			ctsheader=self.env['hr.cts'].search([('year','=',act.periodo.fiscalyear_id.id),('period','=',periodo)])
			if len(ctsheader)>0:
				ctsline=self.env['hr.cts.line'].search([('cts','=',ctsheader.id),('employee_id','=',i.id)])
				if len(ctsline)>0:
					monto_cts=ctsline.cts_soles

			liquidaciones=self.env['hr.liquidaciones'].search([('period_id','=',act.periodo.id)])
			if len(liquidaciones)>0:
				ctsliq=self.env['hr.liquidaciones.lines.cts'].search([('liquidacion_id','=',liquidaciones.id),('employee_id','=',i.id)])
				if len(ctsliq)>0:
					monto_cts=ctsliq.total_payment

				gratiliq=self.env['hr.liquidaciones.lines.grat'].search([('liquidacion_id','=',liquidaciones.id),('employee_id','=',i.id)])
				if len(gratiliq)>0:
					monto_grati_trun=gratiliq.total_months				
					monto_boni_grati=monto_boni_grati+gratiliq.bonus
					# monto_boni_grati_liq=gratiliq.bonus

				vacailiq=self.env['hr.liquidaciones.lines.vac'].search([('liquidacion_id','=',liquidaciones.id),('employee_id','=',i.id)])
				if len(vacailiq)>0:
					vacaciones=vacailiq.fall_due_holidays
					vacaciones_trunca=vacailiq.total_holidays_sinva
					vacaciones_indem=vacailiq.compensation


			# prestamosheader=self.env['hr.prestamo.header'].search([('employee_id','=',i.id)])
			# if len(prestamosheader)>0:
			# 	cta_prestamo = prestamosheader.account_id.id
			# 	for deta in prestamosheader.prestamo_lines_ids:
			# 		if deta.validacion=='2':
			# 			aperioddate=deta.fecha_pago.split('-')
			# 			print aperioddate[1]+'/'+aperioddate[0],act.periodo.code
			# 			if aperioddate[1]+'/'+aperioddate[0]==act.periodo.code:
			# 				prestamos=prestamos+deta.monto

			adelantosheader=self.env['hr.adelanto'].search([('employee','=',i.id)])
			if len(adelantosheader)>0:
				for deta in adelantosheader:
					aperioddate=deta.fecha.split('-')
					if aperioddate[1]+'/'+aperioddate[0]==act.periodo.code:
						adelantos=adelantos+deta.monto


			#fivecat=self.env['hr.five.category'].search([('fiscalyear','=',act.periodo.fiscalyear_id.id)])

			# fivecat=self.env['hr.five.category'].search([('period_id','=',act.periodo.id)])
			# if len(fivecat)>0:
			# 	fivecatline=self.env['hr.five.category.lines'].search([('five_category_id','=',fivecat.id),('employee_id','=',i.id)])	
			# 	if len(fivecatline) >0:
			# 		if act.periodo.code[0:2]=='01':
			# 			monto_5category=fivecatline.janu_amount
			# 		if act.periodo.code[0:2]=='02':
			# 			monto_5category=fivecatline.febr_amount
			# 		if act.periodo.code[0:2]=='03':
			# 			monto_5category=fivecatline.marc_amount
			# 		if act.periodo.code[0:2]=='04':
			# 			monto_5category=fivecatline.apri_amount
			# 		if act.periodo.code[0:2]=='05':
			# 			monto_5category=fivecatline.mayo_amount
			# 		if act.periodo.code[0:2]=='06':
			# 			monto_5category=fivecatline.june_amount
			# 		if act.periodo.code[0:2]=='07':
			# 			monto_5category=fivecatline.july_amount
			# 		if act.periodo.code[0:2]=='08':
			# 			monto_5category=fivecatline.agos_amount
			# 		if act.periodo.code[0:2]=='09':
			# 			monto_5category=fivecatline.sept_amount
			# 		if act.periodo.code[0:2]=='10':
			# 			monto_5category=fivecatline.octo_amount
			# 		if act.periodo.code[0:2]=='11':
			# 			monto_5category=fivecatline.nove_amount
			# 		if act.periodo.code[0:2]=='12':
			# 			monto_5category=fivecatline.dece_amount

			vrl = self.env['vacation.role.line'].search([('parent.period_id','=',act.periodo.id),('employee_id','=',i.id)])
			ivac = False
			rvac = False
			if len(vrl):
				pvl = self.env['partial.vacation.line'].search([('parent','=',vrl.id)])
				ivac = pvl[0].init_date if len(pvl) else False
				rvac = pvl[0].end_date if len(pvl) else False

			ye = int(act.periodo.code.split("/")[1])
			mo = int(act.periodo.code.split("/")[0])

			vals = {
				'employee_id'      : i.id,
				'dni'              : i.identification_id,
				'codigo_trabajador': i.codigo_trabajador,
				'apellido_paterno' : i.last_name_father,
				'apellido_materno' : i.last_name_mother,
				'nombre'           : i.first_name_complete,
				'cargo'            : i.job_id.id,
				'afiliacion'       : i.afiliacion.id,
				'zona'             : i.zona_contab,
				'tipo_comision'    : i.c_mixta, 
				'basica_first'     : i.basica,
				'a_familiar_first' : a_f,
				'total_remunerable': i.basica + a_f,
				'dias_mes'         : monthrange(ye, mo)[1],
				'dias_trabajador'  : 30,
				'dias_vacaciones'  : vrl[0].days if len(vrl) > 0 else 0,
				
				'subsidiomaternidad' : 0,
				'subsidioincapacidad': 0,
				'h_25'               : 0,
				'h_35'               : 0,
				'h_100'              : 0,
				
				'total_ingreso': 0,
				'tardanzas'    : 0,
				'inasistencias': 0,  
				'dscto_domi'   : 0,
				'rmb'          : 0,
				'onp'          : 0,
				'afp_jub'      : 0,
				'afp_psi'      : 0,
				'afp_com'      : 0,
				
				'total_descuento': 0,
				'neto'           : 0,
				'neto_sueldo'    : 0,
				'neto_vacaciones': 0,

				'otros_dct'   : 0,
				'saldo_sueldo': 0,
				'essalud'     : 0,
				'senaty'      : 0,
				'rma_pi'      : 0,
				'dsc_afp'     : 0,
				'cts'         : 0,

				'vacaciones'                       : vacaciones,
				'vacaciones_trunca'                : vacaciones_trunca,
				'vacaciones_inicio'                : ivac,
				'vacaciones_retorno'               : rvac,
				'otros_ingreso'                    : vacaciones_indem,
				# 'quinta_cat'                       : monto_5category,
				'cts'                              : monto_cts,
				'gratificacion'                    : monto_grati ,
				'gratificacion_extraordinaria'     : monto_grati_trun,
				'boni_grati'                       : monto_boni_grati,
				'centro_costo'                     : i.dist_c.id,
				'adelantos'                        : adelantos,
				'prestamos'                        : prestamos,
				'gratificacion_extraordinaria_real': monto_boni_grati_liq,
				'centro_costo'                     : i.dist_c.id,
				'tareo_id'                         : self.env.context['active_id'],
				'horas_ordinarias_trabajadas'      : act.sunat_hours,
			}
			nhtl = self.env['hr.tareo.line'].create(vals)			
			nhtl.with_context({'active_id':nhtl.id}).onchange_all()
			nhtl.save_data()
		return True