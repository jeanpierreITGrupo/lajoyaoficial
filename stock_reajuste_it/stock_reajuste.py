# -*- encoding: utf-8 -*-
from openerp.osv import osv
from tempfile    import TemporaryFile
from openerp     import models, fields, api
import csv
import base64
import codecs
import datetime
import openerp.addons.decimal_precision as dp

class stock_reajuste(models.Model):
	_name     = 'stock.reajuste'
	_rec_name = 'file_text'

	file        	= fields.Binary(u'Archivo', required=True)
	file_text       = fields.Char(u'texto archivo')
	delimitador 	= fields.Char(u'Delimitador', required=True, default=",", size=1)
	state       	= fields.Selection([('draft','Borrador'),
										('not_imported','No Importado'),
										('imported',"Importado")], 'Estado', default="draft")
	picking_type_id = fields.Many2one('stock.picking.type', u'Tipo de Operación')
	nro_lineas		= fields.Integer(u'Líneas por albarán', default=10)
	errores         = fields.Text(u'Errores')

	reajuste_lines  = fields.One2many('stock.reajuste.lines', 'reajuste_id', u'Lineas', domain=[('diferencia','<',0)])
	reajuste_lines2 = fields.One2many('stock.reajuste.lines', 'reajuste_id', u'Lineas', domain=[('diferencia','>=',0)])

	def string2float(self, s):
		try:
			float(s)
			return True
		except:
			return False

	@api.one
	def procesar(self):
		for i in self.reajuste_lines:
			i.unlink()
		for i in self.reajuste_lines2:
			i.unlink()

		self.env.cr.execute("set client_encoding ='UTF8';")
		data    = self.read()[0]
		fileobj = TemporaryFile('w+')
		fileobj.write(base64.decodestring(data['file']))
		fileobj.seek(0)		
		fic = csv.reader(fileobj,delimiter=str(self.delimitador),quotechar='"')

		err         = ""
		skip_titles = True
		nro_row     = 2
		for row in fic:
			if skip_titles:
				skip_titles = False
				continue
			detalle = ""

			#VALIDACIONES
			if not len(row[0]) and not len(self.env['product.product'].search([('default_code','=',row[0])])):
				detalle += "LINEA " + str(nro_row) + u"- código producto incorrecto\n"
			if not self.string2float(row[3]):
				detalle += "LINEA " + str(nro_row) + u"- disponibilidad incorrecta\n"
			if not self.string2float(row[4]):
				detalle += "LINEA " + str(nro_row) + u"- inventario incorrecto\n"

			nro_row += 1
			if not detalle:
				vals = {}
				vals['reajuste_id'] = self.id
				vals['codigo']      = row[0]
				vals['producto']    = row[1].decode('unicode-escape')
				vals['almacen']     = row[2]
				vals['saldo']       = float(row[3])
				vals['inventario']  = float(row[4])
				vals['diferencia']  = vals['inventario'] - vals['saldo']

				self.env['stock.reajuste.lines'].create(vals)
			else:
				err += detalle

		self.errores = err
		if not self.errores:
			self.state = 'not_imported'

	@api.one
	def importar(self):
		nro_reg = len(self.reajuste_lines)
		nro_alb = nro_reg / self.nro_lineas		
		
		#ALBARANES
		new_picking = False
		cont_l = 0
		for i in self.reajuste_lines:
			if cont_l == 0:
				seq_name = self.pool.get('ir.sequence').next_by_id(self.env.cr, self.env.uid, self.picking_type_id.sequence_id.id, self.env.context)
				pq = """
					INSERT INTO
					stock_picking
					(
					name,
					origin,
					priority,
					picking_type_id,
					move_type,
					company_id,
					state,
					recompute_pack_op,
					invoice_state,
					reception_to_invoice,
					motivo_guia,
					use_date,
					is_req,
					es_control,
					is_employee,
					check_forced,
					date
					)
					VALUES"""+\
					"""(""" +\
					"""'""" + seq_name + """'""" + """,""" +\
					"""'Reajuste'""" + """,""" +\
					"""'1'""" + """,""" +\
					str(self.picking_type_id.id) + """,""" +\
					"""'direct'""" + """,""" +\
					"""1""" + """,""" +\
					"""'done'""" + """,""" +\
					"""true""" + """,""" +\
					"""'none'""" + """,""" +\
					"""false""" + """,""" +\
					"""'11'""" + """,""" +\
					"""false""" + """,""" +\
					"""false""" + """,""" +\
					"""false""" + """,""" +\
					"""false""" + """,""" +\
					"""true""" + """,""" +\
					"""'""" + """2017-07-31 00:00:00""" + """'::timestamp""" +\
					""") RETURNING id;"""	
				self.env.cr.execute(pq)
				new_picking = self.env.cr.fetchall()[0][0]
			
			pp = self.env['product.product'].search([('default_code','=',i.codigo)])[0]

			p_name = """'"""+pp.product_tmpl_id.description_purchase+"""'""" if pp.product_tmpl_id.description_purchase else ("'["+pp.default_code+"] "+pp.name_template.replace("'","''")+"'")
			mq = """
				INSERT INTO stock_move
				(
				picking_id,
				origin,
				product_uos_qty,
				product_uom_qty,
				product_qty,
				company_id,
				picking_type_id,
				location_id,
				location_dest_id,
				priority,
				state,
				date,
				date_expected,
				name,
				partially_available,
				propagate,
				procure_method,
				product_id,
				product_uom,
				invoice_state,
				ponderation,
				precio_unitario_manual,
				price_unit
				)
				VALUES""" +\
				"""(""" +\
				str(new_picking) + """,""" +\
				"""'Reajuste'""" + """,""" +\
				str(abs(i.diferencia)) + """,""" +\
				str(abs(i.diferencia)) + """,""" +\
				str(abs(i.diferencia)) + """,""" +\
				"""1""" + """,""" +\
				str(self.picking_type_id.id) + """,""" +\
				str(self.picking_type_id.default_location_src_id.id) + """,""" +\
				str(self.picking_type_id.default_location_dest_id.id) + """,""" +\
				"""'1'""" + """,""" +\
				"""'done'""" + """,""" +\
				"""'""" + """2017-07-31 00:00:00""" + """'::timestamp""" + """,""" +\
				"""'""" + """2017-07-31 00:00:00""" + """'::timestamp""" + """,""" +\
				p_name + """,""" +\
				"""false""" + """,""" +\
				"""true""" + """,""" +\
				"""'make_to_stock'""" + """,""" +\
				str(pp.id) + """,""" +\
				str(pp.product_tmpl_id.uom_id.id) + """,""" +\
				"""'none'""" + """,""" +\
				"""0.00""" + """,""" +\
				"""0""" + """,""" +\
				"""0.00""" +\
				""")"""
			self.env.cr.execute(mq)
			cont_l += 1
			if cont_l == self.nro_lineas:
				cont_l = 0

		self.state = 'imported'

class stock_reajuste_lines(models.Model):
	_name = 'stock.reajuste.lines'

	reajuste_id = fields.Many2one('stock.reajuste', 'Padre')

	codigo     = fields.Char(u'Código')
	producto   = fields.Char(u'Producto')
	almacen    = fields.Char(u'Almacén')
	saldo      = fields.Float(u'Saldo')
	inventario = fields.Float(u'Inventario')
	diferencia = fields.Float(u'Diferencia')
	observ	   = fields.Text(u'Observaciones')