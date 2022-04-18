# -*- coding: utf-8 -*-
from openerp.osv import osv
from openerp import models, fields, api
from datetime import datetime

class reward_employee_wizard(models.TransientModel):
	_name = 'reward.employee.wizard'

	employee_id = fields.Many2one('hr.employee', "Empleado")

	@api.multi
	def add_replace_employee(self):
		reward = self.env['hr.reward'].search([('id','=',self.env.context['active_id'])])
		replace = False #Variable que controla si se agrega o modifica el empleado.
		for line in reward.reward_lines:
			if self.employee_id == line.employee_id:
				print "Reemplazando datos de empleado"
				replace = True
				employees = self.employee_id
				tareos = self.env['hr.tareo'].search([])
				if reward.period == '07':
					final_date = datetime.strptime(reward.year.code+'-07-01', '%Y-%m-%d')
					for employee in employees:
						in_date = datetime.strptime(str(employee.fecha_ingreso), '%Y-%m-%d')
						#Verifica que el empleado no haya sido despedido antes de la fecha de gratificación
						if  (not employee.fecha_cese) or (datetime.strptime(str(employee.fecha_cese), '%Y-%m-%d').year == int(reward.year.code) and datetime.strptime(str(employee.fecha_cese), '%Y-%m-%d').month > 6):
							total_days = (final_date - in_date).days
							days = 0
							if total_days > 180:
								months = 6
							else:
								months = total_days / 30
							if months >= 1:
								hr_param = self.env['hr.parameters'].search([])	
								a_familiar = 0
								if employee.children_number > 0:
									a_familiar = self.env['hr.parameters'].search([('num_tipo','=','10001')])[0].monto
								he_night = []
								ex_plus = 0 
								absences = 0
								for tareo in tareos:
									periodo = tareo.periodo.code.split("/")
									if periodo[1] == reward.year.code and periodo[0] in ['01', '02', '03', '04', '05', '06']:
										#Cálculo de faltas
										absences += self.env['hr.tareo.line'].search([('tareo_id','=',tareo.id),('dni','=',employee.identification_id)]).dias_suspension_perfecta
										#Cálculo bonificación
										concepto = self.env['hr.concepto.remunerativo.line'].search([('concepto.code','=','008')])
										tareo_concepto = self.env['hr.tareo.concepto'].search([('tareo_id','=',tareo.id),('employee_id','=',employee.id),('concepto_id','=',concepto.id)])
										if tareo_concepto.amount > 0.00:
											ex_plus += tareo_concepto.amount
										#Cálculo de sobre tasa nocturna
										concepto = self.env['hr.concepto.remunerativo.line'].search([('concepto.code','=','106')])
										tareo_concepto = self.env['hr.tareo.concepto'].search([('tareo_id','=',tareo.id),('employee_id','=',employee.id),('concepto_id','=',concepto.id)])
										if tareo_concepto.amount > 0.00:
											he_night.append(tareo_concepto.amount)
								st_nocturna = 0
								if len(he_night) >= 3:
									st_nocturna = sum(he_night)/6
								complete_amount = employee.basica + a_familiar + st_nocturna + ex_plus
								vals = {
									'reward'				: reward.id,
									'employee_id'			: employee.id,
									'identification_number'	: employee.identification_id,
									'code'					: employee.codigo_trabajador,
									'last_name_father'		: employee.last_name_father,
									'last_name_mother'		: employee.last_name_mother,
									'names'					: employee.first_name_complete,
									'in_date'				: employee.fecha_ingreso,
									'months'				: months,
									'days'					: days,
									'absences'				: absences,
									'basic'					: employee.basica,
									'ex_plus'				: ex_plus,
									'a_familiar'			: a_familiar,
									'he_night'				: st_nocturna,
									'complete_amount'		: complete_amount,
									'monthly_amount'		: complete_amount/6,
									'dayly_amount'			: complete_amount/180,
									'months_reward'			: months*round(complete_amount/6,2),
									'days_reward'			: days*round(complete_amount/180,2),
									'absences_amount'		: absences*round(complete_amount/180,2),
								}	
								vals['total_reward'] = vals['months_reward'] + vals['days_reward'] - vals['absences_amount']
								plus_9 = 0
								if reward.plus_9:
									vals['plus_9'] = vals['total_reward']*0.09
								vals['total'] = vals['total_reward'] + vals['plus_9']
								line.write(vals)
				else:
					final_date = datetime.strptime(str(int(reward.year.code)+1)+'-01-01', '%Y-%m-%d')
					for employee in employees:
						in_date = datetime.strptime(str(employee.fecha_ingreso), '%Y-%m-%d')
						#Verifica que el empleado no haya sido despedido antes de la fecha de gratificación
						if  (not employee.fecha_cese) or datetime.strptime(str(employee.fecha_cese), '%Y-%m-%d').year > int(reward.year.code):
							total_days = (final_date - in_date).days
							days = 0
							if total_days > 180:
								months = 6
							else:
								months = total_days / 30
							if months >= 1:
								hr_param = self.env['hr.parameters'].search([])	
								a_familiar = 0
								if employee.children_number > 0:
									a_familiar = self.env['hr.parameters'].search([('num_tipo','=','10001')])[0].monto
								he_night = []
								ex_plus = 0 
								absences = 0
								for tareo in tareos:
									periodo = self.env['account.period'].search([('id','=',tareo.periodo.id)]).code.split("/")
									if periodo[1] == reward.year.code and periodo[0] in ['07', '08', '09', '10', '11', '12']:
										#Cálculo de faltas
										absences += self.env['hr.tareo.line'].search([('tareo_id','=',tareo.id),('dni','=',employee.identification_id)]).dias_suspension_perfecta
										#Cálculo bonificación
										concepto = self.env['hr.concepto.remunerativo.line'].search([('concepto.code','=','008')])
										tareo_concepto = self.env['hr.tareo.concepto'].search([('tareo_id','=',tareo.id),('employee_id','=',employee.id),('concepto_id','=',concepto.id)])
										if tareo_concepto.amount > 0.00:
											ex_plus += tareo_concepto.amount
										#Cálculo de sobre tasa nocturna
										concepto = self.env['hr.concepto.remunerativo.line'].search([('concepto.code','=','40')])
										tareo_concepto = self.env['hr.tareo.concepto'].search([('tareo_id','=',tareo.id),('employee_id','=',employee.id),('concepto_id','=',concepto.id)])
										if tareo_concepto.amount > 0.00:
											he_night.append(tareo_concepto.amount)
								st_nocturna = 0
								if len(he_night) >= 3:
									st_nocturna = sum(he_night)/6
								complete_amount = employee.basica + a_familiar + st_nocturna + ex_plus
								vals = {
									'reward'				: reward.id,
									'employee_id'			: employee.id,
									'identification_number'	: employee.identification_id,
									'code'					: employee.codigo_trabajador,
									'last_name_father'		: employee.last_name_father,
									'last_name_mother'		: employee.last_name_mother,
									'names'					: employee.first_name_complete,
									'in_date'				: employee.fecha_ingreso,
									'months'				: months,
									'days'					: days,
									'absences'				: absences,
									'basic'					: employee.basica,
									'ex_plus'				: ex_plus,
									'a_familiar'			: a_familiar,
									'he_night'				: st_nocturna,
									'complete_amount'		: complete_amount,
									'monthly_amount'		: complete_amount/6,
									'dayly_amount'			: complete_amount/180,
									'months_reward'			: months*round(complete_amount/6,2),
									'days_reward'			: days*round(complete_amount/180,2),
									'absences_amount'		: absences*round(complete_amount/180,2),
								}		
								vals['total_reward'] = vals['months_reward'] + vals['days_reward'] - vals['absences_amount']
								plus_9 = 0
								if reward.plus_9:
									vals['plus_9'] = vals['total_reward']*0.09
								vals['total'] = vals['total_reward'] + vals['plus_9']
								line.write(vals)
				break
		if not replace:
			print "Agregando datos de empleado"
			employees = self.employee_id
			reward_line = self.env['hr.reward.line']
			tareos = self.env['hr.tareo'].search([])
			if reward.period == '07':
				final_date = datetime.strptime(reward.year.code+'-07-01', '%Y-%m-%d')
				for employee in employees:
					in_date = datetime.strptime(str(employee.fecha_ingreso), '%Y-%m-%d')
					#Verifica que el empleado no haya sido despedido antes de la fecha de gratificación
					if  (not employee.fecha_cese) or (datetime.strptime(str(employee.fecha_cese), '%Y-%m-%d').year == int(reward.year.code) and datetime.strptime(str(employee.fecha_cese), '%Y-%m-%d').month > 6):
						total_days = (final_date - in_date).days
						days = 0
						if total_days > 180:
							months = 6
						else:
							months = total_days / 30
						if months >= 1:
							hr_param = self.env['hr.parameters'].search([])	
							a_familiar = 0
							if employee.children_number > 0:
								a_familiar = self.env['hr.parameters'].search([('num_tipo','=','10001')])[0].monto
							he_night = []
							ex_plus = 0 
							absences = 0
							for tareo in tareos:
								periodo = tareo.periodo.code.split("/")
								if periodo[1] == reward.year.code and periodo[0] in ['01', '02', '03', '04', '05', '06']:
									#Cálculo de faltas
									absences += self.env['hr.tareo.line'].search([('tareo_id','=',tareo.id),('dni','=',employee.identification_id)]).dias_suspension_perfecta
									#Cálculo bonificación
									concepto = self.env['hr.concepto.remunerativo.line'].search([('concepto.code','=','008')])
									tareo_concepto = self.env['hr.tareo.concepto'].search([('tareo_id','=',tareo.id),('employee_id','=',employee.id),('concepto_id','=',concepto.id)])
									if tareo_concepto.amount > 0.00:
										ex_plus += tareo_concepto.amount
									#Cálculo de sobre tasa nocturna
									concepto = self.env['hr.concepto.remunerativo.line'].search([('concepto.code','=','106')])
									tareo_concepto = self.env['hr.tareo.concepto'].search([('tareo_id','=',tareo.id),('employee_id','=',employee.id),('concepto_id','=',concepto.id)])
									if tareo_concepto.amount > 0.00:
										he_night.append(tareo_concepto.amount)
							st_nocturna = 0
							if len(he_night) >= 3:
								st_nocturna = sum(he_night)/6
							complete_amount = employee.basica + a_familiar + st_nocturna + ex_plus
							vals = {
								'reward'				: reward.id,
								'employee_id'			: employee.id,
								'identification_number'	: employee.identification_id,
								'code'					: employee.codigo_trabajador,
								'last_name_father'		: employee.last_name_father,
								'last_name_mother'		: employee.last_name_mother,
								'names'					: employee.first_name_complete,
								'in_date'				: employee.fecha_ingreso,
								'months'				: months,
								'days'					: days,
								'absences'				: absences,
								'basic'					: employee.basica,
								'ex_plus'				: ex_plus,
								'a_familiar'			: a_familiar,
								'he_night'				: st_nocturna,
								'complete_amount'		: complete_amount,
								'monthly_amount'		: complete_amount/6,
								'dayly_amount'			: complete_amount/180,
								'months_reward'			: months*round(complete_amount/6,2),
								'days_reward'			: days*round(complete_amount/180,2),
								'absences_amount'		: absences*round(complete_amount/180,2),
							}	
							vals['total_reward'] = vals['months_reward'] + vals['days_reward'] - vals['absences_amount']
							plus_9 = 0
							if reward.plus_9:
								vals['plus_9'] = vals['total_reward']*0.09
							vals['total'] = vals['total_reward'] + vals['plus_9']
							reward_line.create(vals)
			else:
				final_date = datetime.strptime(str(int(reward.year.code)+1)+'-01-01', '%Y-%m-%d')
				for employee in employees:
					in_date = datetime.strptime(str(employee.fecha_ingreso), '%Y-%m-%d')
					#Verifica que el empleado no haya sido despedido antes de la fecha de gratificación
					if  (not employee.fecha_cese) or datetime.strptime(str(employee.fecha_cese), '%Y-%m-%d').year > int(reward.year.code):
						total_days = (final_date - in_date).days
						days = 0
						if total_days > 180:
							months = 6
						else:
							months = total_days / 30
						if months >= 1:
							hr_param = self.env['hr.parameters'].search([])	
							a_familiar = 0
							if employee.children_number > 0:
								a_familiar = self.env['hr.parameters'].search([('num_tipo','=','10001')])[0].monto
							he_night = []
							ex_plus = 0 
							absences = 0
							for tareo in tareos:
								periodo = self.env['account.period'].search([('id','=',tareo.periodo.id)]).code.split("/")
								if periodo[1] == reward.year.code and periodo[0] in ['07', '08', '09', '10', '11', '12']:
									#Cálculo de faltas
									absences += self.env['hr.tareo.line'].search([('tareo_id','=',tareo.id),('dni','=',employee.identification_id)]).dias_suspension_perfecta
									#Cálculo bonificación
									concepto = self.env['hr.concepto.remunerativo.line'].search([('concepto.code','=','008')])
									tareo_concepto = self.env['hr.tareo.concepto'].search([('tareo_id','=',tareo.id),('employee_id','=',employee.id),('concepto_id','=',concepto.id)])
									if tareo_concepto.amount > 0.00:
										ex_plus += tareo_concepto.amount
									#Cálculo de sobre tasa nocturna
									concepto = self.env['hr.concepto.remunerativo.line'].search([('concepto.code','=','40')])
									tareo_concepto = self.env['hr.tareo.concepto'].search([('tareo_id','=',tareo.id),('employee_id','=',employee.id),('concepto_id','=',concepto.id)])
									if tareo_concepto.amount > 0.00:
										he_night.append(tareo_concepto.amount)
							st_nocturna = 0
							if len(he_night) >= 3:
								st_nocturna = sum(he_night)/6
							complete_amount = employee.basica + a_familiar + st_nocturna + ex_plus
							vals = {
								'reward'				: reward.id,
								'employee_id'			: employee.id,
								'identification_number'	: employee.identification_id,
								'code'					: employee.codigo_trabajador,
								'last_name_father'		: employee.last_name_father,
								'last_name_mother'		: employee.last_name_mother,
								'names'					: employee.first_name_complete,
								'in_date'				: employee.fecha_ingreso,
								'months'				: months,
								'days'					: days,
								'absences'				: absences,
								'basic'					: employee.basica,
								'ex_plus'				: ex_plus,
								'a_familiar'			: a_familiar,
								'he_night'				: st_nocturna,
								'complete_amount'		: complete_amount,
								'monthly_amount'		: complete_amount/6,
								'dayly_amount'			: complete_amount/180,
								'months_reward'			: months*round(complete_amount/6,2),
								'days_reward'			: days*round(complete_amount/180,2),
								'absences_amount'		: absences*round(complete_amount/180,2),
							}		
							vals['total_reward'] = vals['months_reward'] + vals['days_reward'] - vals['absences_amount']
							plus_9 = 0
							if reward.plus_9:
								vals['plus_9'] = vals['total_reward']*0.09
							vals['total'] = vals['total_reward'] + vals['plus_9']
							reward_line.create(vals)