# -*- coding: utf-8 -*-

from openerp import models, fields, api , exceptions , _

class account_move(models.Model):
	_inherit = 'account.move'


	tipo_sustento_credito_fiscasl = fields.Char('Tipo Documento')
	serie_sustento_credito_fiscasl = fields.Char('Serie')
	anio_sustento_credito_fiscasl = fields.Char('Año Emision Dua')
	nro_comp_sustento_credito_fiscasl = fields.Char('Nro Comprobante')


	type_journal_tmp = fields.Selection(string='Type Journal Tmp',related='journal_id.type')
	
	# aqui van los de cliente
	ultimo_numero_consolidado = fields.Char('Ultimo Número de Consolidado',size=100, copy=False)
	sujeto_a_retencion = fields.Boolean('Sujeto a Retención', copy=False)
	tipo_adquisicion = fields.Selection([('1','Mercaderia, materia prima, suministro, envases y embalajes'),('2','Activo Fijo'),('3','Otros activos no considerados en los numerales 1 y 2'),('4','Gastos de educación, recreación, salud, culturales, representación, capacitación, de viaje, mantenimiento de vehiculos, y de premios'),('5','Otros gastos no incluidos en el numeral 4')], 'Tipo Adquisición')
	contrato_o_proyecto = fields.Char('Contrato o Proyecto',size=200, copy=False)
	inconsistencia_tipo_cambio = fields.Boolean('Inconsistencia en Tipo de Cambio', copy=False)
	proveedor_no_habido = fields.Boolean('Proveedor No Habido', copy=False)
	renuncio_a_exoneracion_igv = fields.Boolean('Renuncio a Exoneracion IGV', copy=False)
	inconsistencia_dni_liquidacion_comp = fields.Boolean('Inconsistencia DNI en Liquidación Comp.', copy=False)
	cancelado_medio_pago = fields.Boolean('Cancelado con Medio de Pago', copy=False)
	
	periodo_ajuste_modificacion_ple = fields.Many2one('account.period','Periodo Ajuste o Modifacaión PLE', copy=False)
	periodo_ajuste_modificacion_ple_compra = fields.Many2one('account.period','Periodo Ajuste PLE', copy=False)

	estado_ple = fields.Integer('Estado PLE')

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
	periodo_ajuste_modificacion_ple_venta = fields.Many2one('account.period','Periodo Ajuste PLE', copy=False)


class account_move_line(models.Model):
	_inherit = 'account.move.line'

	codigos_ple_diario = fields.Char('Establecimiento')
