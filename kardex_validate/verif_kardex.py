# -*- encoding: utf-8 -*-
import pprint

from openerp import fields, models, api, _
from openerp.osv import osv

class vst_verif_kardex(models.Model):
	_name='vst.verif.kardex'
	_auto=False

	ubicacion = fields.Char('Ubicacion',size=150)
	origen = fields.Char('Origen',size=150)
	producto = fields.Char('Producto',size=150)
	albaran = fields.Char('Albaran',size=50)
	referencia = fields.Char('Referencia',size=20)
	fecha = fields.Datetime('Fecha')
	tipo_comp =fields.Char('Tipo de comprobante',size=20)
	comprobante= fields.Char('Comprobante',size=20)
	periodo =fields.Char('Periodo',size=20)
	valor = fields.Char('Valor',size=200)
	
	def init(self,cr):
		cr.execute("""
		DROP VIEW IF EXISTS vst_verif_kardex;
			create or replace view vst_verif_kardex as (
		 SELECT row_number() OVER () AS id,
    t.ubicacion,
    t.origen,
    t.producto,
    t.albaran,
    t.referencia,
    t.fecha,
    t.tipo_comp,
    t.comprobante,
    t.periodo,
    t.valor
    FROM ( SELECT sl.complete_name AS ubicacion,
            og.complete_name AS origen,
            pp.name_template AS producto,
            sp.name AS albaran,
            sp.origin AS referencia,
                CASE
                    WHEN ai.id IS NULL THEN 
			case when ai2.id is null then
				ai2.date_invoice::timestamp without time zone
			else
				sp.date::timestamp without time zone
			end
		  ELSE ai.date_invoice::timestamp without time zone
                END AS fecha,
                CASE
                    WHEN ai.id IS NULL THEN 
                    case when ai2.id is null then
			' '::text::character varying
		    else
			itd2.description
		    end
                    ELSE itd.description
                END AS tipo_comp,
                CASE
                    WHEN ai.id IS NULL THEN
			    case when ai2.id is null then
			    ' '::text::character varying
			    else
				ai2.number
			    end

                    ELSE ai.number
                END AS comprobante,
                CASE
                    WHEN am.id IS NULL THEN 
                    case when ai2.id is null then
			' '::text::character varying
                    else
			ap2.name
                    end
                    ELSE ap.name
                END AS periodo,
                CASE
                    WHEN ai.id IS NULL and sm.invoice_id is null THEN 'Sin comprobante relacionado'::text
                    ELSE
                    CASE
                        WHEN ail.id IS NULL and ail2.id is null THEN 'Comprobante sin producto relacionado'::text
                        ELSE
                        CASE
                            WHEN am.id is null and am2.id IS NULL THEN 'Comprobante sin asiento contable'::text
                            ELSE
                            CASE
                                WHEN aml.id IS NULL and aml2.id is null THEN 'Verificar producto en asiento contable'::text
                                ELSE 'ok'::text
                            END
                        END
                    END
                END AS valor
           FROM stock_move sm
             JOIN stock_picking sp ON sm.picking_id = sp.id
             LEFT JOIN product_product pp ON sm.product_id = pp.id
             LEFT JOIN account_invoice ai ON sp.invoice_id = ai.id
             LEFT JOIN account_invoice ai2 ON sm.invoice_id = ai2.id
             LEFT JOIN account_invoice_line ail ON ai.id = ail.invoice_id AND sm.product_id = ail.product_id
             LEFT JOIN account_invoice_line ail2 ON ai2.id = ail2.invoice_id AND sm.product_id = ail2.product_id
             LEFT JOIN account_move am ON ai.move_id = am.id
             LEFT JOIN account_move am2 ON ai2.move_id = am2.id
             LEFT JOIN account_move_line aml ON aml.move_id = am.id AND sm.product_id = aml.product_id
             LEFT JOIN account_move_line aml2 ON aml2.move_id = am2.id AND sm.product_id = aml2.product_id
             LEFT JOIN stock_location sl ON sm.location_dest_id = sl.id
             LEFT JOIN stock_location og ON sm.location_id = og.id
             LEFT JOIN res_partner rp ON ai.partner_id = rp.id
             LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
             LEFT JOIN it_type_document itd ON ai.type_document_id = itd.id
             LEFT JOIN it_type_document itd2 ON ai2.type_document_id = itd2.id
             LEFT JOIN account_period ap ON am.period_id = ap.id
             LEFT JOIN account_period ap2 ON am.period_id = ap2.id
          WHERE sl.usage::text = 'internal'::text 
          AND pt.type::text = 'product'::text 
          AND sm.state::text = 'done'::text 
          AND sp.state::text = 'done'::text 
          AND (og.usage::text <> ALL (ARRAY['production'::character varying::text, 'internal'::character varying::text, 'inventory'::character varying::text])) 
          AND (ai.id IS NULL OR am.id IS NULL OR aml.id IS NULL or ai2.id is null) 
          ORDER BY sp.origin, sp.name, pp.name_template) t
          where t.valor !='ok');
		""")
		
		# Consulta anterior
		"""
			DROP VIEW IF EXISTS vst_verif_kardex;
			create or replace view vst_verif_kardex as (
			SELECT row_number() OVER () AS id,* from (
			 SELECT sl.complete_name AS ubicacion, og.complete_name AS origen, 
				pp.name_template AS producto, sp.name AS albaran, sp.origin AS referencia, 
					CASE
						WHEN ai.id IS NULL THEN sp.date
						ELSE ai.date_invoice::timestamp without time zone
					END AS fecha, 
					CASE
						WHEN ai.id IS NULL THEN ' '::text::character varying
						ELSE itd.description
					END AS tipo_comp, 
					CASE
						WHEN ai.id IS NULL THEN ' '::text::character varying
						ELSE ai.number
					END AS comprobante, 
					CASE
						WHEN am.id IS NULL THEN ' '::text::character varying
						ELSE ap.name
					END AS periodo, 
					CASE
						WHEN ai.id IS NULL THEN 'Sin comprobante relacionado'::text
						ELSE 
						CASE
							WHEN ail.id IS NULL THEN 'Comprobante sin producto relacionado'::text
							ELSE 
							CASE
								WHEN am.id IS NULL THEN 'Comprobante sin asiento contable'::text
								ELSE 
								CASE
									WHEN aml.id IS NULL THEN 'Verificar producto en asiento contable'::text
									ELSE 'ok'::text
								END
							END
						END
					END AS valor
			   FROM stock_move sm
			   JOIN stock_picking sp ON sm.picking_id = sp.id
			   LEFT JOIN product_product pp ON sm.product_id = pp.id
			   LEFT JOIN account_invoice ai ON sp.invoice_id = ai.id
			   LEFT JOIN account_invoice_line ail ON ai.id = ail.invoice_id AND sm.product_id = ail.product_id
			   LEFT JOIN account_move am ON ai.move_id = am.id
			   LEFT JOIN account_move_line aml ON aml.move_id = am.id AND sm.product_id = aml.product_id
			   LEFT JOIN stock_location sl ON sm.location_dest_id = sl.id
			   LEFT JOIN stock_location og ON sm.location_id = og.id
			   LEFT JOIN res_partner rp ON ai.partner_id = rp.id
			   LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
			   LEFT JOIN it_type_document itd ON ai.type_document_id = itd.id
			   LEFT JOIN account_period ap ON am.period_id = ap.id
			  WHERE sl.usage::text = 'internal'::text AND pt.type::text = 'product'::text AND sm.state::text = 'done'::text AND sp.state::text = 'done'::text AND (og.usage::text <> ALL (ARRAY['production'::character varying, 'internal'::character varying, 'inventory'::character varying]::text[])) AND (ai.id IS NULL OR am.id IS NULL OR aml.id IS NULL)
			  ORDER BY sp.origin, sp.name, pp.name_template) T

			)
			"""