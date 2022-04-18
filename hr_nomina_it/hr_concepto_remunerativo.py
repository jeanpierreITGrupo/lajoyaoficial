# -*- encoding: utf-8 -*-
import base64
from openerp     import models, fields, api
from openerp.osv import osv

from lxml     import etree
from StringIO import StringIO

class hr_lista_conceptos(models.Model):
	_name = 'hr.lista.conceptos'
	_rec_name = 'name'
	_order = 'position'

	name             = fields.Char('Nombre', required=True)
	code             = fields.Char(u'Código', required=True)
	sunat_code       = fields.Char(u'Código SUNAT')
	payroll_group    = fields.Selection([('1','Ingreso'),
										 ('2','Descuentos de la Base'),
										 ('3','Aportes Trabajador'),
										 ('4','Aportes Empleador'),
										 ('5','Descuentos del Neto'),
										 ('6','Neto'),
										 ('7','Detalle del Neto'),], 'Grupo Planilla')
	account_debe_id  = fields.Many2one('account.account', 'Cuenta Debe')
	account_haber_id = fields.Many2one('account.account', 'Cuenta Haber')
	position         = fields.Integer(u'Posición en la Planilla')
	mostrar_tabla    = fields.Boolean('No mostrar en tabla de checks')
	check_boleta     = fields.Boolean('Boleta empleado')
	check_liquida    = fields.Boolean(u'Liquidación')
	cuentas_line	 = fields.One2many('hr.lista.conceptos.line','lista_id','hijos')

	@api.model
	def create(self, vals):
		t = super(hr_lista_conceptos, self).create(vals)
		if 'code' in vals:
			hlc = self.env['hr.lista.conceptos'].search([('code','=',t.code),('id','!=',t.id)])
			if len(hlc) > 0:
				raise osv.except_osv("Alerta!", u"Ya existe un concepto con el código "+t.code)

			# SECCION PARA LA VISTA DINAMICA DE LA PLANILLA

			im  = self.env['ir.model'].search([('model','=','hr.planilla1')])[0]
			imf = self.env['ir.model.fields'].search([('model_id','=',im.id),('name','=','x_'+t.code)])

			if len(imf) == 0:
				pmodel_vals = {
					'model_id'         : im.id,
					'name'             : 'x_'+t.code,
					'field_description': t.name,
					'ttype'            : 'float',
					'state'			   : 'manual',
				}
				self.env['ir.model.fields'].create(pmodel_vals)

			planilla_tree_view = self.env['ir.model.data'].xmlid_to_object('hr_nomina_it.view_hr_planilla1_tree_concepts')

			arch_in = etree.XML(bytes(bytearray(planilla_tree_view.arch, encoding='utf-8')))
			start_concepts = arch_in.xpath("//field[@name='tipo_comision']")[0]

			for ch in start_concepts:
				ch.getparent().remove(ch)

			all_con = self.env['hr.lista.conceptos'].search([]).sorted(key=lambda r: r.position)
			for item in all_con:
				fi = etree.SubElement(start_concepts,"field",name='x_'+item.code, sum='x_'+item.code)

			imf = self.env['ir.model.fields'].search([('model_id','=',im.id),('name','=','x_'+all_con[0].code)])

			planilla_tree_view.write({'arch':etree.tostring(arch_in, xml_declaration=True, encoding="utf-8")})
			planilla_tree_view.refresh()
						
		return t

	@api.one
	def write(self, vals):
		prev_code = self.code
		t = super(hr_lista_conceptos, self).write(vals)
		self.refresh()
		if 'code' in vals:
			con_rep = {}
			hlc = self.env['hr.lista.conceptos'].search([])
			for lista in hlc:
				if lista.code not in con_rep:
					con_rep[lista.code] = 1
				else:
					con_rep[lista.code] += 1

			msg = ""
			for k,v in con_rep.items():
				if v > 1:
					msg += k + " -> " + str(v) + "\n"

			if len(msg) > 0:
				raise osv.except_osv("Alerta!", u"Existen códigos repetidos.\nCódigo -> Repeticiones\n"+msg)

			# SECCION PARA LA VISTA DINAMICA DE LA PLANILLA

			planilla_tree_view = self.env['ir.model.data'].xmlid_to_object('hr_nomina_it.view_hr_planilla1_tree_concepts')

			arch_in = etree.XML(bytes(bytearray(planilla_tree_view.arch, encoding='utf-8')))
			start_concepts = arch_in.xpath("//field[@name='tipo_comision']")[0]

			for ch in start_concepts:
				ch.getparent().remove(ch)

			im  = self.env['ir.model'].search([('model','=','hr.planilla1')])[0]
			imf = self.env['ir.model.fields'].search([('model_id','=',im.id),('name','=','x_'+prev_code)])
			if len(imf) > 0:
				imf = imf[0]
				imf.write({ 'name'  : 'x_'+self.code,                                    
							'field_description': self.name})

			all_con = self.env['hr.lista.conceptos'].search([]).sorted(key=lambda r: r.position)
			for item in all_con:
				fi = etree.SubElement(start_concepts,"field",name='x_'+item.code, sum='x_'+item.code)

			planilla_tree_view.write({'arch':etree.tostring(arch_in, xml_declaration=True, encoding="utf-8")})
			planilla_tree_view.refresh()


		if 'name' in vals:
			# SECCION PARA LA VISTA DINAMICA DE LA PLANILLA

			im  = self.env['ir.model'].search([('model','=','hr.planilla1')])[0]
			imf = self.env['ir.model.fields'].search([('model_id','=',im.id),('name','=','x_'+self.code)])
			if len(imf) > 0:
				imf = imf[0]
				imf.write({'field_description':self.name})

		if 'position' in vals:
			# SECCION PARA LA VISTA DINAMICA DE LA PLANILLA

			planilla_tree_view = self.env['ir.model.data'].xmlid_to_object('hr_nomina_it.view_hr_planilla1_tree_concepts')

			arch_in = etree.XML(bytes(bytearray(planilla_tree_view.arch, encoding='utf-8')))
			start_concepts = arch_in.xpath("//field[@name='tipo_comision']")[0]

			for ch in start_concepts:
				ch.getparent().remove(ch)

			all_con = self.env['hr.lista.conceptos'].search([]).sorted(key=lambda r: r.position)
			for item in all_con:
				fi = etree.SubElement(start_concepts,"field",name='x_'+item.code, sum='x_'+item.code)

			planilla_tree_view.write({'arch':etree.tostring(arch_in, xml_declaration=True, encoding="utf-8")})
			planilla_tree_view.refresh()


		return t

	@api.one
	def unlink(self):
		hcrl = self.env['hr.concepto.remunerativo.line'].search([('concepto.code','=',self.code)])
		if len(hcrl) > 0:
			raise osv.except_osv("Alerta!", u"El concepto "+self.name+"("+self.code+") no se puede eliminar porque se usa en un concepto remunerativo.")
		
		hcl = self.env['hr.concepto.line'].search([('concepto_id','=',self.id)])
		if len(hcl) > 0:
			raise osv.except_osv("Alerta!", u"El concepto "+self.name+"("+self.code+") no se puede eliminar porque se usa en un tareo.")
		
		# SECCION PARA LA VISTA DINAMICA DE LA PLANILLA

		planilla_tree_view = self.env['ir.model.data'].xmlid_to_object('hr_nomina_it.view_hr_planilla1_tree_concepts')

		arch_in = etree.XML(bytes(bytearray(planilla_tree_view.arch, encoding='utf-8')))
		start_concepts = arch_in.xpath("//field[@name='tipo_comision']")[0]

		for ch in start_concepts:
			ch.getparent().remove(ch)

		all_con = self.env['hr.lista.conceptos'].search([('code','!=',self.code)]).sorted(key=lambda r: r.position)
		for item in all_con:
			fi = etree.SubElement(start_concepts,"field",name='x_'+item.code, sum='x_'+item.code)

		planilla_tree_view.write({'arch':etree.tostring(arch_in, xml_declaration=True, encoding="utf-8")})
		planilla_tree_view.refresh()

		im  = self.env['ir.model'].search([('model','=','hr.planilla1')])[0]
		imf = self.env['ir.model.fields'].search([('model_id','=',im.id),('name','=','x_'+self.code)])
		for item in imf:
			item.unlink()
			item.write({})


		t = super(hr_lista_conceptos, self).unlink()
		return t

class hr_lista_conceptos_line(models.Model):
	_name = 'hr.lista.conceptos.line'

	lista_id    = fields.Many2one('hr.lista.conceptos','Padre')
	
	account_id  = fields.Many2one('account.account','Cuenta',required=True)
	analytic_id = fields.Many2one('account.analytic.account',u'Cuenta Analítica')

class hr_concepto_remunerativo_line(models.Model):
	_name = 'hr.concepto.remunerativo.line'
	_rec_name = 'concepto'
	
	codigo      = fields.Char('Código')
	name        = fields.Char('Nombre')
	concepto_id = fields.Many2one('hr.concepto.remunerativo', 'Padre')
	
	concepto       = fields.Many2one('hr.lista.conceptos','Concepto', required=True)
	onp            = fields.Boolean('ONP')
	afp_fon_pen    = fields.Boolean('AFP FONDO PENSIONES')
	afp_pri_se     = fields.Boolean('AFP PRIMA DE SEGUROS')
	afp_co_va      = fields.Boolean('AFP COM VARIABLE')
	afp_co_mix     = fields.Boolean('AFP COM MIXTA')
	quinta_categ   = fields.Boolean('5ta Cat.')
	essalud_vida   = fields.Boolean('Essalud Vida')
	jubilacion     = fields.Boolean('Fondo de Jubilación')
	essalud        = fields.Boolean('ESSALUD')
	eps_sctr_salud = fields.Boolean('EPS/SCTR SALUD')
	scrt           = fields.Boolean('SCRT')
	senati         = fields.Boolean('SENATI')
	afp_2p         = fields.Boolean('AFP 2%')
	rmb	           = fields.Boolean('RMB')
	neto_vac       = fields.Boolean('NETO VACACIONES')

	@api.model
	def create(self,vals):
		t = super(hr_concepto_remunerativo_line,self).create(vals)
		t.codigo = t.concepto.code
		return t

	@api.one
	def write(self,vals):
		t = super(hr_concepto_remunerativo_line,self).write(vals)

		self.refresh()
		if 'concepto' in vals:
			hlc = self.env['hr.lista.conceptos'].search([('id','=',vals['concepto'])])[0]
			self.write({'codigo':hlc.code})

		con_rep = {}
		for line in self.concepto_id.line_id:
			if line.concepto.id not in con_rep:
				con_rep[line.concepto.id] = 1
			else:
				con_rep[line.concepto.id] += 1

		msg = ""
		for k,v in con_rep.items():
			if v > 1:
				hlc = self.env['hr.lista.conceptos'].search([('id','=',k)])[0]
				msg += hlc.name + "(" + hlc.code + ")" + " -> " + str(v) + "\n"

		if len(msg) > 0:
			raise osv.except_osv("Alerta!", "Existen conceptos remunerativos repetidos.\nConcepto -> Repeticiones\n"+msg)
		
		return t

class hr_concepto_remunerativo(models.Model):
	_name = 'hr.concepto.remunerativo'

	name    = fields.Char('Nombre')
	line_id = fields.One2many('hr.concepto.remunerativo.line','concepto_id','Detalle')

	def init(self, cr):
		cr.execute('select id from hr_concepto_remunerativo')
		ids = cr.fetchall()

		if len(ids) == 0:
			cr.execute("""INSERT INTO hr_concepto_remunerativo (name) VALUES ('Concepto Remunerativo')""")

	@api.one
	def write(self, vals):
		t = super(hr_concepto_remunerativo, self).write(vals)

		crc = self.env['conceptos.remunerativos.configuracion']
		for item in crc.search([]):
			item.unlink()

		crc_vals = ({
			'concepto_id' : 0,
			'parameter_id': 0,
		})

		for line in self.line_id:
			if line.essalud_vida:
				hr = self.env['hr.parameters'].search([('num_tipo','=',2)])
				if len(hr) == 0:
					raise osv.except_osv('Alerta!','No se encontró parametro de tipo 2')
				crc_vals['concepto_id']  = line.concepto.id
				crc_vals['parameter_id'] = hr[0].num_tipo
				crc.create(crc_vals)

			if line.jubilacion:
				hr = self.env['hr.parameters'].search([('num_tipo','=',3)])
				if len(hr) == 0:
					raise osv.except_osv('Alerta!','No se encontró parametro de tipo 3')
				crc_vals['concepto_id']  = line.concepto.id
				crc_vals['parameter_id'] = hr[0].num_tipo
				crc.create(crc_vals)

			if line.essalud:
				hr = self.env['hr.parameters'].search([('num_tipo','=',4)])
				if len(hr) == 0:
					raise osv.except_osv('Alerta!','No se encontró parametro de tipo 4')
				crc_vals['concepto_id']  = line.concepto.id
				crc_vals['parameter_id'] = hr[0].num_tipo
				crc.create(crc_vals)

			if line.eps_sctr_salud:
				hr = self.env['hr.parameters'].search([('num_tipo','=',5)])
				if len(hr) == 0:
					raise osv.except_osv('Alerta!','No se encontró parametro de tipo 5')
				crc_vals['concepto_id']  = line.concepto.id
				crc_vals['parameter_id'] = hr[0].num_tipo
				crc.create(crc_vals)

			if line.scrt:
				hr = self.env['hr.parameters'].search([('num_tipo','=',6)])
				if len(hr) == 0:
					raise osv.except_osv('Alerta!','No se encontró parametro de tipo 6')
				crc_vals['concepto_id']  = line.concepto.id
				crc_vals['parameter_id'] = hr[0].num_tipo
				crc.create(crc_vals)

			if line.senati:
				hr = self.env['hr.parameters'].search([('num_tipo','=',7)])
				if len(hr) == 0:
					raise osv.except_osv('Alerta!','No se encontró parametro de tipo 7')
				crc_vals['concepto_id']  = line.concepto.id
				crc_vals['parameter_id'] = hr[0].num_tipo
				crc.create(crc_vals)

			if line.afp_2p:
				hr = self.env['hr.parameters'].search([('num_tipo','=',8)])
				if len(hr) == 0:
					raise osv.except_osv('Alerta!','No se encontró parametro de tipo 8')
				crc_vals['concepto_id']  = line.concepto.id
				crc_vals['parameter_id'] = hr[0].num_tipo
				crc.create(crc_vals)

		return t


class conceptos_remunerativos_configuracion(models.Model):
	_name = 'conceptos.remunerativos.configuracion'

	concepto_id  = fields.Many2one('hr.lista.conceptos','concepto_id')
	parameter_id = fields.Integer('parameter_id')