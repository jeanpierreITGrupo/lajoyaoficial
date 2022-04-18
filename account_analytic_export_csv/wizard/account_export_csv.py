# -*- coding: utf-8 -*-
##############################################################################
#
#    Author Joel Grand-Guillaume and Vincent Renaville Copyright 2013
#    Camptocamp SA
#    CSV data formating inspired from
# http://docs.python.org/2.7/library/csv.html?highlight=csv#examples
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import itertools
import tempfile
from cStringIO import StringIO
import base64

import csv
import codecs

from openerp.osv import orm, fields
from openerp.tools.translate import _


class AccountUnicodeWriter(object):

    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = StringIO()
        # created a writer with Excel formating settings
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        # we ensure that we do not try to encode none or bool
        row = (x or u'' for x in row)

        encoded_row = [
            c.encode("utf-8") if isinstance(c, unicode) else c for c in row]

        self.writer.writerow(encoded_row)
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


class AccountCSVExport(orm.TransientModel):
    _name = 'account.csv.export.analytic'
    _description = 'Export Accounting'

    _columns = {
        'data': fields.binary('CSV', readonly=True),
        'company_id': fields.many2one('res.company', 'Company',
                                      invisible=True),
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscalyear',
                                         required=True),
        'periods': fields.many2many(
            'account.period', 'rel_wizard_periodas',
            'wizard_id', 'period_id', 'Periods',
            help='All periods in the fiscal year if empty'),
        'journal_ids': fields.many2many(
            'account.journal',
            'rel_wizard_journalas',
            'wizard_id',
            'journal_id',
            'Journals',
            help='If empty, use all journals, only used for journal entries'),
        'export_filename': fields.char('Export CSV Filename', size=128),
    }

    def _get_company_default(self, cr, uid, context=None):
        comp_obj = self.pool['res.company']
        return comp_obj._company_default_get(cr, uid, 'account.fiscalyear',
                                             context=context)

    def _get_fiscalyear_default(self, cr, uid, context=None):
        fiscalyear_obj = self.pool['account.fiscalyear']
        context = dict(context,
                       company_id=self._get_company_default(cr, uid, context))
        return fiscalyear_obj.find(cr, uid, dt=None, exception=True,
                                   context=context)

    _defaults = {'company_id': _get_company_default,
                 'fiscalyear_id': _get_fiscalyear_default,
                 'export_filename': 'account_analytic_export.csv'}

    def action_manual_export_account(self, cr, uid, ids, context=None):
        this = self.browse(cr, uid, ids)[0]
        rows = self.get_data(cr, uid, ids, "account", context)
        file_data = StringIO()
        try:
            writer = AccountUnicodeWriter(file_data)
            writer.writerows(rows)
            file_value = file_data.getvalue()
            self.write(cr, uid, ids,
                       {'data': base64.encodestring(file_value)},
                       context=context)
        finally:
            file_data.close()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.csv.export.analytic',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': this.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

    def _get_header_account(self, cr, uid, ids, context=None):
        return [_(u'PERIODO'),
                _(u'CUENTA ANALITICA'),
                _(u'MONTO'),
                ]

    def _get_rows_account(self, cr, uid, ids,
                          fiscalyear_id,
                          period_range_ids,
                          journal_ids,
                          context=None):
        """
        Return list to generate rows of the CSV file
        """
        cr.execute("""

          select 
periodo.code as periodo,
cta_an.name as cta_an,
 sum(-amount) as monto 
 from account_analytic_line a1
 left join account_move_line apuntes on apuntes.id=a1.move_id
 left join account_move asientos on asientos.id=apuntes.move_id
 left join account_period periodo on periodo.id=asientos.period_id
 left join account_journal libros on libros.id=asientos.journal_id
 left join account_analytic_account cta_an on cta_an.id=a1.account_id
 left join account_account cta on cta.id=a1.general_account_id
 left join account_analytic_account p_cta_an on p_cta_an.id=cta_an.parent_id
 left join account_analytic_account p_p_cta_an on p_p_cta_an.id=p_cta_an.parent_id
 left join product_product pro on pro.id=a1.product_id
 left join product_uom unidad on unidad.id=a1.product_uom_id
 left join res_partner part on part.id=apuntes.partner_id

where periodo.id in %(period_ids)s
and libros.id in %(journal_ids)s
group by periodo.code,cta_an.name
order by periodo.code,cta_an.name
                   """,
                   {'fiscalyear_id': fiscalyear_id,
                       'period_ids': tuple(period_range_ids), 'journal_ids': tuple(journal_ids)}
                   )
        res = cr.fetchall()

        rows = []
        for line in res:
            rows.append(list(line))
        return rows
    def action_manual_export_analytic(self, cr, uid, ids, context=None):
        this = self.browse(cr, uid, ids)[0]
        rows = self.get_data(cr, uid, ids, "analytic", context)
        file_data = StringIO()
        try:
            writer = AccountUnicodeWriter(file_data)
            writer.writerows(rows)
            file_value = file_data.getvalue()
            self.write(cr, uid, ids,
                       {'data': base64.encodestring(file_value)},
                       context=context)
        finally:
            file_data.close()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.csv.export.analytic',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': this.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

    def _get_header_analytic(self, cr, uid, ids, context=None):
        return [_(u'ANALYTIC CODE'),
                _(u'ANALYTIC NAME'),
                _(u'CODE'),
                _(u'ACCOUNT NAME'),
                _(u'DEBIT'),
                _(u'CREDIT'),
                _(u'BALANCE'),
                ]

    def _get_rows_analytic(self, cr, uid, ids,
                           fiscalyear_id,
                           period_range_ids,
                           journal_ids,
                           context=None):
        """
        Return list to generate rows of the CSV file
        """
        cr.execute("""  select aac.code as analytic_code,
                        aac.name as analytic_name,
                        ac.code,ac.name,
                        sum(debit) as sum_debit,
                        sum(credit) as sum_credit,
                        sum(debit) - sum(credit) as balance
                        from account_move_line
                        left outer join account_analytic_account as aac
                        on (account_move_line.analytic_account_id = aac.id)
                        inner join account_account as ac
                        on account_move_line.account_id = ac.id
                        and account_move_line.period_id in %(period_ids)s
						and aac.code is not null
                        group by aac.id,aac.code,aac.name,ac.id,ac.code,ac.name
                        order by aac.code
                   """,
                   {'fiscalyear_id': fiscalyear_id,
                       'period_ids': tuple(period_range_ids)}
                   )
        res = cr.fetchall()

        rows = []
        for line in res:
            rows.append(list(line))
        return rows
	
		
		


    def action_manual_export_journal_entries(self, cr, uid, ids, context=None):
        """
        Here we use TemporaryFile to avoid full filling the OpenERP worker
        Memory
        We also write the data to the wizard with SQL query as write seems
        to use too much memory as well.

        Those improvements permitted to improve the export from a 100k line to
        200k lines
        with default `limit_memory_hard = 805306368` (768MB) with more lines,
        you might encounter a MemoryError when trying to download the file even
        if it has been generated.

        To be able to export bigger volume of data, it is advised to set
        limit_memory_hard to 2097152000 (2 GB) to generate the file and let
        OpenERP load it in the wizard when trying to download it.

        Tested with up to a generation of 700k entry lines
        """
        this = self.browse(cr, uid, ids)[0]
        rows = self.get_data(cr, uid, ids, "journal_entries", context)
        with tempfile.TemporaryFile() as file_data:
            writer = AccountUnicodeWriter(file_data)
            writer.writerows(rows)
            with tempfile.TemporaryFile() as base64_data:
                file_data.seek(0)
                base64.encode(file_data, base64_data)
                base64_data.seek(0)
                cr.execute("""
                UPDATE account_csv_export_analytic
                SET data = %s
                WHERE id = %s""", (base64_data.read(), ids[0]))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.csv.export.analytic',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': this.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

    def _get_header_journal_entries(self, cr, uid, ids, context=None):
        return [
                     
			_(u'PERIODO'),
			_(u'LIBRO'),
			_(u'FECHA'),
			_(u'VOUCHER'),
			_(u'NRO. COMPROBANTE'),
			_(u'RUC'),
			_(u'EMPRESA O PERSONA'),
			_(u'CTA. ANALITICA PADRE'),
			_(u'CTA. ANALITICA PADRE 2'),
			_(u'CTA. ANALITICA'),
			_(u'CTA. AMARRE'),
			_(u'CTA. CONTABLE'),
			_(u'PRODUCTO'),
			_(u'UNIDAD'),
			_(u'CANTIDAD'),
			_(u'GLOSA'),
            _(u'MONTO'),
            _(u'MONEDA'),
            _(u'TIPO CAMBIO'),
            _(u'DOLARES'),
            _(u'USUARIO'),
            _(u'FECHA CREACION/MODIFICACION'),
			_(u'Zona'),
        ]

    def _get_rows_journal_entries(self, cr, uid, ids,
                                  fiscalyear_id,
                                  period_range_ids,
                                  journal_ids,
                                  context=None):
        """
        Create a generator of rows of the CSV file
        """
        cr.execute("""

          select 
periodo.code as periodo,
libros.name as libro,
asientos.date as fecha,
asientos.name as voucher,
apuntes.nro_comprobante,
part.type_number as ruc,
part.name as empresa_persona, 
p_p_cta_an.name as an_padre1,
p_cta_an.name as an_padre2,
cta_an.name as cta_an,
cta_am.code as cta_amarre,
cta.code||'-'||cta.name as cta_fin,  
pro.name_template as producto,
unidad.name as unidad,
a1.unit_amount as cantidad,
a1.name as glosa,
 -amount as monto,
coalesce(rc.name,'PEN') as moneda,
apuntes.currency_rate_it as tipocambio,
apuntes.amount_currency as dolares,
rpu.name as usuario,
zon.name as zona,
a1.write_date::date as fecha
 from account_analytic_line a1
 left join account_move_line apuntes on apuntes.id=a1.move_id
 left join res_currency rc on rc.id = apuntes.currency_id
 left join res_users ru on ru.id = a1.create_uid
 left join res_partner rpu on rpu.id = ru.partner_id
 left join account_move asientos on asientos.id=apuntes.move_id
 left join account_period periodo on periodo.id=asientos.period_id
 left join account_journal libros on libros.id=asientos.journal_id
 left join account_analytic_account cta_an on cta_an.id=a1.account_id
 left join account_account cta_am on cta_am.id=cta_an.account_account_moorage_id
 left join account_account cta on cta.id=a1.general_account_id
 left join account_analytic_account p_cta_an on p_cta_an.id=cta_an.parent_id
 left join account_analytic_account p_p_cta_an on p_p_cta_an.id=p_cta_an.parent_id
 left join product_product pro on pro.id=a1.product_id
 left join product_uom unidad on unidad.id=a1.product_uom_id
 left join res_partner part on part.id=apuntes.partner_id
 left join zona_resumen zon on zon.id=cta_an.zona_id

where periodo.id in  %(period_ids)s 
and libros.id in %(journal_ids)s 
order by periodo.code,libros.code,asientos.name 
			
        """,
                   {'period_ids': tuple(
                       period_range_ids), 'journal_ids': tuple(journal_ids)}
                   )
        while 1:
            # http://initd.org/psycopg/docs/cursor.html#cursor.fetchmany
            # Set cursor.arraysize to minimize network round trips
            cr.arraysize = 100
            rows = cr.fetchmany()
            if not rows:
                break
            for row in rows:
                yield row


    def get_data(self, cr, uid, ids, result_type, context=None):
		get_header_func = getattr(
			self, ("_get_header_%s" % (result_type)), None)
		get_rows_func = getattr(self, ("_get_rows_%s" % (result_type)), None)
		form = self.browse(cr, uid, ids[0], context=context)
		fiscalyear_id = form.fiscalyear_id.id
		if form.periods:
			period_range_ids = [x.id for x in form.periods]
		else:
			# If not period selected , we take all periods
			p_obj = self.pool.get("account.period")
			period_range_ids = p_obj.search(
				cr, uid, [('fiscalyear_id', '=', fiscalyear_id)],
				context=context)
		journal_ids = None
		if form.journal_ids:
			journal_ids = [x.id for x in form.journal_ids]
		else:
			j_obj = self.pool.get("account.journal")
			journal_ids = j_obj.search(cr, uid, [], context=context)
		rows = itertools.chain((get_header_func(cr, uid, ids,
												context=context),),
							   get_rows_func(cr, uid, ids,
											 fiscalyear_id,
											 period_range_ids,
											 journal_ids,
											 context=context)
							   )
		return rows
