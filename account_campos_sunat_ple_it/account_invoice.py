# -*- coding: utf-8 -*-

from openerp import models, fields, api

class res_partner(models.Model):
	_inherit = 'res.partner'

	pais_residencia_nd = fields.Char('País de la residencia del sujeto no domiciliado')
	domicilio_extranjero_nd =fields.Char('Domicilio  en el extranjero del sujeto no domiciliado')
	numero_identificacion_nd =fields.Char('Número de identificación del sujeto no domiciliado')

	vinculo_contribuyente_residente_extranjero = fields.Char('Vinculo entre el contribuyente y el residente en el extranjero')
	convenios_evitar_doble_imposicion = fields.Char('Convenios para evitar la doble imposición')


class account_invoice(models.Model):
	_inherit = 'account.invoice'


	tipo_sustento_credito_fiscasl = fields.Char('Tipo Documento')
	serie_sustento_credito_fiscasl = fields.Char('Serie')
	anio_sustento_credito_fiscasl = fields.Char('Año Emision Dua')
	nro_comp_sustento_credito_fiscasl = fields.Char('Nro Comprobante')




	# aqui van los de proveedor
	ultimo_numero_consolidado = fields.Char('Ultimo Número de Consolidado',size=100, copy=False)
	sujeto_a_retencion = fields.Boolean('Sujeto a Retención', copy=False)
	tipo_adquisicion = fields.Selection([('1','Mercaderia, materia prima, suministro, envases y embalajes'),('2','Activo Fijo'),('3','Otros activos no considerados en los numerales 1 y 2'),('4','Gastos de educación, recreación, salud, culturales, representación, capacitación, de viaje, mantenimiento de vehiculos, y de premios'),('5','Otros gastos no incluidos en el numeral 4')], 'Tipo Adquisición')
	contrato_o_proyecto = fields.Char('Contrato o Proyecto',size=200, copy=False)
	inconsistencia_tipo_cambio = fields.Boolean('Inconsistencia en Tipo de Cambio', copy=False)
	proveedor_no_habido = fields.Boolean('Proveedor No Habido', copy=False)
	renuncio_a_exoneracion_igv = fields.Boolean('Renuncio a Exoneracion IGV', copy=False)
	inconsistencia_dni_liquidacion_comp = fields.Boolean('Inconsistencia DNI en Liquidación Comp.', copy=False)
	cancelado_medio_pago = fields.Boolean('Cancelado con Medio de Pago', copy=False)
	estado_ple_compra = fields.Selection([('0', 'ANOTACION OPTATIVAS SIN EFECTO EN EL IGV'), ('1', 'FECHA DEL DOCUMENTO CORRESPONDE AL PERIODO EN QUE SE ANOTO'), ('6', 'FECHA DE EMISION ES ANTERIOR AL PERIODO DE ANOTACION, DENTRO DE LOS 12 MESES'), ('7','FECHA DE EMISION ES ANTERIOR AL PERIODO DE ANOTACION, LUEGO DE LOS 12 MESES'),('9','ES AJUSTE O RECTIFICACION')], 'PLE Compras' ,default="1",copy=False)
	periodo_ajuste_modificacion_ple = fields.Many2one('account.period','Periodo Ajuste PLE', copy=False)
	periodo_ajuste_modificacion_ple_compra = fields.Many2one('account.period','Periodo Ajuste PLE', copy=False)
	estado_ple = fields.Integer('Estado para PLE')


	#aqui van los de proveedor
	renta_bruta = fields.Float('Renta Bruta',digits=(12,2), copy=False)
	deduccion_costo_enajenacion = fields.Float('Deducción Costo Enajenacion',digits=(12,2), copy=False)
	renta_neta = fields.Float('Renta Neta',digits=(12,2), copy=False)
	tasa_de_retencion = fields.Float('Tasa de Retención',digits=(12,2), copy=False)
	impuesto_retenido = fields.Float('Impuesto Retenido',digits=(12,2), copy=False)
	exoneracion_aplicada = fields.Char('Exoneración Aplicada',size=200, copy=False)
	tipo_de_renta = fields.Char('Tipo de Renta',size=200, copy=False)
	modalidad_servicio_prestada = fields.Char('Modalidad Servicio Prestada',size=200, copy=False)
	aplica_art_del_impuesto = fields.Boolean('Aplicada Art 76 del Impuesto a la Renta', copy=False)
	beneficiario_de_pagos = fields.Many2one('res.partner','Beneficiario de los Pagos', copy=False)


	#aqui van los de cliente
	numero_final_consolidado_cliente = fields.Char('Ultimo Número de Consolidado',size=100, copy=False)
	numero_contrato_cliente = fields.Char('Número de contrato', size=200, copy=False)
	inconsistencia_tipo_cambio_cliente = fields.Boolean('Inconsistencia en Tipo de Cambio', copy=False)
	cancelado_medio_pago_cliente = fields.Boolean('Cancelado con Medio de Pago', copy=False)
	estado_ple_venta = fields.Selection([('0', 'ANOTACION OPTATIVA SIN EFECTO EN EL IGV'), ('1', 'FECHA DEL COMPROBANTE CORRESPONDE AL PERIODO'), ('2', 'DOCUMENTO ANULADO'), ('8', 'CORRESPONDE A UN PERIODO ANTERIOR'), ('9', 'SE ESTA CORRIGIENDO UNA ANOTACION DEL PERIODO ANTERIOR')], 'PLE Ventas' ,default='1',copy=False)
	periodo_ajuste_modificacion_ple_venta = fields.Many2one('account.period','Periodo Ajuste PLE', copy=False)


	@api.one
	def write(self,vals):
		t = super(account_invoice,self).write(vals)
		for inv in self:
			if inv.move_id.id:
				if inv.estado_ple_compra:
					self._cr.execute(""" UPDATE account_move SET ple_compra='%s' WHERE id=%s """%(inv.estado_ple_compra, inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET ple_compra=Null WHERE id=%s """%(inv.move_id.id))

				if inv.estado_ple_venta:
					self._cr.execute(""" UPDATE account_move SET ple_venta='%s' WHERE id=%s """%(inv.estado_ple_venta, inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET ple_venta=Null WHERE id=%s """%(inv.move_id.id))

				if inv.numero_final_consolidado_cliente:
					self._cr.execute(""" UPDATE account_move SET numero_final_consolidado_cliente='%s' WHERE id=%s """%(inv.numero_final_consolidado_cliente, inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET numero_final_consolidado_cliente=Null WHERE id=%s """%(inv.move_id.id))

				if inv.numero_contrato_cliente:
					self._cr.execute(""" UPDATE account_move SET numero_contrato_cliente='%s' WHERE id=%s """%(inv.numero_contrato_cliente, inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET numero_contrato_cliente=Null WHERE id=%s """%(inv.move_id.id))

				if inv.inconsistencia_tipo_cambio_cliente:
					self._cr.execute(""" UPDATE account_move SET inconsistencia_tipo_cambio_cliente=true WHERE id=%s """%(inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET inconsistencia_tipo_cambio_cliente=false WHERE id=%s """%(inv.move_id.id))

				if inv.cancelado_medio_pago_cliente:
					self._cr.execute(""" UPDATE account_move SET cancelado_medio_pago_cliente=true WHERE id=%s """%(inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET cancelado_medio_pago_cliente=false WHERE id=%s """%(inv.move_id.id))					

				if inv.ultimo_numero_consolidado:
					self._cr.execute(""" UPDATE account_move SET ultimo_numero_consolidado='%s' WHERE id=%s """%(inv.ultimo_numero_consolidado, inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET ultimo_numero_consolidado=Null WHERE id=%s """%(inv.move_id.id))
					
				if inv.sujeto_a_retencion:
					self._cr.execute(""" UPDATE account_move SET sujeto_a_retencion=true WHERE id=%s """%(inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET sujeto_a_retencion=false WHERE id=%s """%(inv.move_id.id))
					
				if inv.tipo_adquisicion:
					self._cr.execute(""" UPDATE account_move SET tipo_adquisicion='%s' WHERE id=%s """%(inv.tipo_adquisicion, inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET tipo_adquisicion=Null WHERE id=%s """%(inv.move_id.id))
					
				if inv.contrato_o_proyecto:
					self._cr.execute(""" UPDATE account_move SET contrato_o_proyecto='%s' WHERE id=%s """%(inv.contrato_o_proyecto, inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET contrato_o_proyecto=Null WHERE id=%s """%(inv.move_id.id))
					
				if inv.inconsistencia_tipo_cambio:
					self._cr.execute(""" UPDATE account_move SET inconsistencia_tipo_cambio=true WHERE id=%s """%(inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET inconsistencia_tipo_cambio=false WHERE id=%s """%(inv.move_id.id))
					
				if inv.proveedor_no_habido:
					self._cr.execute(""" UPDATE account_move SET proveedor_no_habido=true WHERE id=%s """%( inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET proveedor_no_habido=false WHERE id=%s """%(inv.move_id.id))
					
				if inv.renuncio_a_exoneracion_igv:
					self._cr.execute(""" UPDATE account_move SET renuncio_a_exoneracion_igv=true WHERE id=%s """%(inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET renuncio_a_exoneracion_igv=false WHERE id=%s """%(inv.move_id.id))
					
				if inv.inconsistencia_dni_liquidacion_comp:
					self._cr.execute(""" UPDATE account_move SET inconsistencia_dni_liquidacion_comp=true WHERE id=%s """%(inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET inconsistencia_dni_liquidacion_comp=false WHERE id=%s """%(inv.move_id.id))

				if inv.cancelado_medio_pago:
					self._cr.execute(""" UPDATE account_move SET cancelado_medio_pago=true WHERE id=%s """%(inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET cancelado_medio_pago=false WHERE id=%s """%(inv.move_id.id))

				if inv.periodo_ajuste_modificacion_ple_compra:
					self._cr.execute(""" UPDATE account_move SET periodo_ajuste_modificacion_ple_compra='%s' WHERE id=%s """%(inv.periodo_ajuste_modificacion_ple_compra.id, inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET periodo_ajuste_modificacion_ple_compra=Null WHERE id=%s """%(inv.move_id.id))

				if inv.periodo_ajuste_modificacion_ple_venta:
					self._cr.execute(""" UPDATE account_move SET periodo_ajuste_modificacion_ple_venta='%s' WHERE id=%s """%(inv.periodo_ajuste_modificacion_ple_venta.id, inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET periodo_ajuste_modificacion_ple_venta=Null WHERE id=%s """%(inv.move_id.id))






				self._cr.execute(""" UPDATE account_move SET renta_bruta=%s WHERE id=%s """%("%0.2f"%inv.renta_bruta, inv.move_id.id))
				self._cr.execute(""" UPDATE account_move SET deduccion_costo_enajenacion=%s WHERE id=%s """%("%0.2f"%inv.deduccion_costo_enajenacion, inv.move_id.id))
				self._cr.execute(""" UPDATE account_move SET renta_neta=%s WHERE id=%s """%("%0.2f"%inv.renta_neta, inv.move_id.id))
				self._cr.execute(""" UPDATE account_move SET tasa_de_retencion=%s WHERE id=%s """%("%0.2f"%inv.tasa_de_retencion, inv.move_id.id))
				self._cr.execute(""" UPDATE account_move SET impuesto_retenido=%s WHERE id=%s """%("%0.2f"%inv.impuesto_retenido, inv.move_id.id))


				if inv.exoneracion_aplicada:
					self._cr.execute(""" UPDATE account_move SET exoneracion_aplicada='%s' WHERE id=%s """%(inv.exoneracion_aplicada, inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET exoneracion_aplicada=Null WHERE id=%s """%(inv.move_id.id))

				if inv.tipo_de_renta:
					self._cr.execute(""" UPDATE account_move SET tipo_de_renta='%s' WHERE id=%s """%(inv.tipo_de_renta, inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET tipo_de_renta=Null WHERE id=%s """%(inv.move_id.id))

				if inv.modalidad_servicio_prestada:
					self._cr.execute(""" UPDATE account_move SET modalidad_servicio_prestada='%s' WHERE id=%s """%(inv.modalidad_servicio_prestada, inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET modalidad_servicio_prestada=Null WHERE id=%s """%(inv.move_id.id))

				if inv.aplica_art_del_impuesto:
					self._cr.execute(""" UPDATE account_move SET aplica_art_del_impuesto=true WHERE id=%s """%(inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET aplica_art_del_impuesto=false WHERE id=%s """%(inv.move_id.id))


				if inv.beneficiario_de_pagos:
					self._cr.execute(""" UPDATE account_move SET beneficiario_de_pagos='%s' WHERE id=%s """%(inv.beneficiario_de_pagos.id, inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET beneficiario_de_pagos=Null WHERE id=%s """%(inv.move_id.id))


				if inv.tipo_sustento_credito_fiscasl:
					self._cr.execute(""" UPDATE account_move SET tipo_sustento_credito_fiscasl='%s' WHERE id=%s """%(inv.tipo_sustento_credito_fiscasl, inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET tipo_sustento_credito_fiscasl=Null WHERE id=%s """%(inv.move_id.id))

				if inv.serie_sustento_credito_fiscasl:
					self._cr.execute(""" UPDATE account_move SET serie_sustento_credito_fiscasl='%s' WHERE id=%s """%(inv.serie_sustento_credito_fiscasl, inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET serie_sustento_credito_fiscasl=Null WHERE id=%s """%(inv.move_id.id))

				if inv.anio_sustento_credito_fiscasl:
					self._cr.execute(""" UPDATE account_move SET anio_sustento_credito_fiscasl='%s' WHERE id=%s """%(inv.anio_sustento_credito_fiscasl, inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET anio_sustento_credito_fiscasl=Null WHERE id=%s """%(inv.move_id.id))
				if inv.nro_comp_sustento_credito_fiscasl:
					self._cr.execute(""" UPDATE account_move SET nro_comp_sustento_credito_fiscasl='%s' WHERE id=%s """%(inv.nro_comp_sustento_credito_fiscasl, inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET nro_comp_sustento_credito_fiscasl=Null WHERE id=%s """%(inv.move_id.id))


		return t


	@api.one
	def action_number(self):
		t = super(account_invoice,self).action_number()
		self.write({})

		for inv in self:
			if inv.move_id.id:

				if inv.estado_ple_compra:
					self._cr.execute(""" UPDATE account_move SET ple_compra='%s' WHERE id=%s """%(inv.estado_ple_compra, inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET ple_compra=Null WHERE id=%s """%(inv.move_id.id))

				if inv.estado_ple_venta:
					self._cr.execute(""" UPDATE account_move SET ple_venta='%s' WHERE id=%s """%(inv.estado_ple_venta, inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET ple_venta=Null WHERE id=%s """%(inv.move_id.id))
				
				if inv.numero_final_consolidado_cliente:
					self._cr.execute(""" UPDATE account_move SET numero_final_consolidado_cliente='%s' WHERE id=%s """%(inv.numero_final_consolidado_cliente, inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET numero_final_consolidado_cliente=Null WHERE id=%s """%(inv.move_id.id))

				if inv.numero_contrato_cliente:
					self._cr.execute(""" UPDATE account_move SET numero_contrato_cliente='%s' WHERE id=%s """%(inv.numero_contrato_cliente, inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET numero_contrato_cliente=Null WHERE id=%s """%(inv.move_id.id))

				if inv.inconsistencia_tipo_cambio_cliente:
					self._cr.execute(""" UPDATE account_move SET inconsistencia_tipo_cambio_cliente=true WHERE id=%s """%(inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET inconsistencia_tipo_cambio_cliente=false WHERE id=%s """%(inv.move_id.id))

				if inv.cancelado_medio_pago_cliente:
					self._cr.execute(""" UPDATE account_move SET cancelado_medio_pago_cliente=true WHERE id=%s """%(inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET cancelado_medio_pago_cliente=false WHERE id=%s """%(inv.move_id.id))					

			
				if inv.ultimo_numero_consolidado:
					self._cr.execute(""" UPDATE account_move SET ultimo_numero_consolidado='%s' WHERE id=%s """%(inv.ultimo_numero_consolidado, inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET ultimo_numero_consolidado=Null WHERE id=%s """%(inv.move_id.id))
					
				if inv.sujeto_a_retencion:
					self._cr.execute(""" UPDATE account_move SET sujeto_a_retencion=true WHERE id=%s """%(inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET sujeto_a_retencion=false WHERE id=%s """%(inv.move_id.id))
					
				if inv.tipo_adquisicion:
					self._cr.execute(""" UPDATE account_move SET tipo_adquisicion='%s' WHERE id=%s """%(inv.tipo_adquisicion, inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET tipo_adquisicion=Null WHERE id=%s """%(inv.move_id.id))
					
				if inv.contrato_o_proyecto:
					self._cr.execute(""" UPDATE account_move SET contrato_o_proyecto='%s' WHERE id=%s """%(inv.contrato_o_proyecto, inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET contrato_o_proyecto=Null WHERE id=%s """%(inv.move_id.id))
					
				if inv.inconsistencia_tipo_cambio:
					self._cr.execute(""" UPDATE account_move SET inconsistencia_tipo_cambio=true WHERE id=%s """%(inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET inconsistencia_tipo_cambio=false WHERE id=%s """%(inv.move_id.id))
					
				if inv.proveedor_no_habido:
					self._cr.execute(""" UPDATE account_move SET proveedor_no_habido=true WHERE id=%s """%( inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET proveedor_no_habido=false WHERE id=%s """%(inv.move_id.id))
					
				if inv.renuncio_a_exoneracion_igv:
					self._cr.execute(""" UPDATE account_move SET renuncio_a_exoneracion_igv=true WHERE id=%s """%(inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET renuncio_a_exoneracion_igv=false WHERE id=%s """%(inv.move_id.id))
					
				if inv.inconsistencia_dni_liquidacion_comp:
					self._cr.execute(""" UPDATE account_move SET inconsistencia_dni_liquidacion_comp=true WHERE id=%s """%(inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET inconsistencia_dni_liquidacion_comp=false WHERE id=%s """%(inv.move_id.id))

				if inv.cancelado_medio_pago:
					self._cr.execute(""" UPDATE account_move SET cancelado_medio_pago=true WHERE id=%s """%(inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET cancelado_medio_pago=false WHERE id=%s """%(inv.move_id.id))

				
				if inv.periodo_ajuste_modificacion_ple_compra:
					self._cr.execute(""" UPDATE account_move SET periodo_ajuste_modificacion_ple_compra='%s' WHERE id=%s """%(inv.periodo_ajuste_modificacion_ple_compra.id, inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET periodo_ajuste_modificacion_ple_compra=Null WHERE id=%s """%(inv.move_id.id))

				if inv.periodo_ajuste_modificacion_ple_venta:
					self._cr.execute(""" UPDATE account_move SET periodo_ajuste_modificacion_ple_venta='%s' WHERE id=%s """%(inv.periodo_ajuste_modificacion_ple_venta.id, inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET periodo_ajuste_modificacion_ple_venta=Null WHERE id=%s """%(inv.move_id.id))







				self._cr.execute(""" UPDATE account_move SET renta_bruta=%s WHERE id=%s """%("%0.2f"%inv.renta_bruta, inv.move_id.id))
				self._cr.execute(""" UPDATE account_move SET deduccion_costo_enajenacion=%s WHERE id=%s """%("%0.2f"%inv.deduccion_costo_enajenacion, inv.move_id.id))
				self._cr.execute(""" UPDATE account_move SET renta_neta=%s WHERE id=%s """%("%0.2f"%inv.renta_neta, inv.move_id.id))
				self._cr.execute(""" UPDATE account_move SET tasa_de_retencion=%s WHERE id=%s """%("%0.2f"%inv.tasa_de_retencion, inv.move_id.id))
				self._cr.execute(""" UPDATE account_move SET impuesto_retenido=%s WHERE id=%s """%("%0.2f"%inv.impuesto_retenido, inv.move_id.id))


				if inv.exoneracion_aplicada:
					self._cr.execute(""" UPDATE account_move SET exoneracion_aplicada='%s' WHERE id=%s """%(inv.exoneracion_aplicada, inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET exoneracion_aplicada=Null WHERE id=%s """%(inv.move_id.id))

				if inv.tipo_de_renta:
					self._cr.execute(""" UPDATE account_move SET tipo_de_renta='%s' WHERE id=%s """%(inv.tipo_de_renta, inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET tipo_de_renta=Null WHERE id=%s """%(inv.move_id.id))

				if inv.modalidad_servicio_prestada:
					self._cr.execute(""" UPDATE account_move SET modalidad_servicio_prestada='%s' WHERE id=%s """%(inv.modalidad_servicio_prestada, inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET modalidad_servicio_prestada=Null WHERE id=%s """%(inv.move_id.id))

				if inv.aplica_art_del_impuesto:
					self._cr.execute(""" UPDATE account_move SET aplica_art_del_impuesto=true WHERE id=%s """%(inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET aplica_art_del_impuesto=false WHERE id=%s """%(inv.move_id.id))


				if inv.beneficiario_de_pagos:
					self._cr.execute(""" UPDATE account_move SET beneficiario_de_pagos='%s' WHERE id=%s """%(inv.beneficiario_de_pagos.id, inv.move_id.id))
				else:
					self._cr.execute(""" UPDATE account_move SET beneficiario_de_pagos=Null WHERE id=%s """%(inv.move_id.id))
		return t
