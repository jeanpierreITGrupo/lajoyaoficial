# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import api, fields, models, tools, _
from openerp.exceptions import Warning

import openerp.addons.decimal_precision as dp

import re
import base64



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

import decimal

class BudgetLine(models.Model):
    _inherit = 'crossovered.budget.lines'

    @api.multi
    def _get_sql_query(self, journal_clause, analytic_account_id, date_from, date_to, acc_ids):
        sql_string = "SELECT SUM(al.amount) "\
                     "FROM account_analytic_line al "\
                     "LEFT JOIN account_analytic_journal aj ON al.journal_id = aj.id "\
                     "WHERE al.account_id=%s "\
                     "AND (al.date between to_date(%s,'yyyy-mm-dd') AND to_date(%s,'yyyy-mm-dd')) "\
                     "AND al.general_account_id=ANY(%s)" + journal_clause
        sql_args = (analytic_account_id, date_from, date_to, acc_ids)
        return sql_string, sql_args

    @api.multi
    def _prac_amt(self, commitment=False):
        res = {}
        result = 0.0
        context = self._context or {}
        journal_clause = " AND aj.type %s 'general'" % (commitment and '=' or '<>')
        for line in self:
            acc_ids = [x.id for x in line.general_budget_id.account_ids]
            if not acc_ids:
                raise Warning(_("The Budget '%s' has no accounts!") % tools.ustr(line.general_budget_id.name))
            date_to = line.date_to
            date_from = line.date_from
            if 'wizard_date_from' in context:
                date_from = context['wizard_date_from']
            if 'wizard_date_to' in context:
                date_to = context['wizard_date_to']
            if line.analytic_account_id.id:
                sql_string, sql_args = self._get_sql_query(journal_clause, line.analytic_account_id.id,
                                                           date_from, date_to, acc_ids)
                self._cr.execute(sql_string, sql_args)
                result = self._cr.fetchone()[0]
            if result is None:
                result = 0.0
            res[line.id] = result
        return res

    @api.one
    def _commitment_amt(self):
        self.commitment_amount = self._prac_amt(commitment=True)[self.id]
        self.available_amount = self.planned_amount - self.commitment_amount

    analytic_line_ids = fields.One2many('account.analytic.line', 'budget_line_id', 'Analytic Lines')
    commitment_amount = fields.Float('Commitment Amount', digits=dp.get_precision('Account'), compute="_commitment_amt")
    available_amount = fields.Float('Available Amount', digits=dp.get_precision('Account'), compute="_commitment_amt")

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False, lazy=True):
        fields_to_compute = []
        for field in ('commitment_amount', 'available_amount', 'practical_amount', 'theoritical_amount'):
            if field in fields:
                fields.remove(field)
                fields_to_compute.append(field)
        res = super(BudgetLine, self).read_group(cr, uid, domain, fields, groupby, offset, limit, context, orderby, lazy)
        if fields_to_compute:
            for group in res:
                if group.get('__domain'):
                    line_infos = self.search_read(cr, uid, group['__domain'], fields_to_compute, context=context)
                    for field in fields_to_compute:
                        group[field] = sum([l[field] for l in line_infos])
        return res

    @api.multi
    def action_open_analytic_lines(self):
        self.ensure_one()
        return {
            'name': _('Analytic Lines'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.analytic.line',
            'target': 'new',
            'domain': [('id', 'in', self[0].analytic_line_ids._ids)],
            'context': self._context,
        }


class BudgetPositionCommitmentLimit(models.Model):
    _name = 'account.budget.post.commitment_limit'
    _description = 'Budgetary Position Commitment Limit'
    _rec_name = 'budget_post_id'

    budget_post_id = fields.Many2one('account.budget.post', 'Budgetary Position', required=True, index=True)
    user_id = fields.Many2one('res.users', 'User', required=True, index=True)
    amount_limit = fields.Float('Commitment Amount Limit', digits=dp.get_precision('Account'), required=True)


class BudgetPosition(models.Model):
    _inherit = 'account.budget.post'

    commitment_limit_ids = fields.One2many('account.budget.post.commitment_limit', 'budget_post_id', 'Commitment Limits')



class report_budges_line_wizard(models.Model):
    _name='report.budget.line.wizard'

    fiscalyear_id = fields.Many2one('account.fiscalyear','Año Fiscal',required="1")
    type_show = fields.Selection([('pdf','PDF'),('excel','Excel')],'Mostrar',required=True)


    @api.multi
    def do_rebuild(self):


        if self.type_show == 'pdf':

            self.reporteador()
            
            import sys
            reload(sys)
            sys.setdefaultencoding('iso-8859-1')
            mod_obj = self.env['ir.model.data']
            act_obj = self.env['ir.actions.act_window']
            import os

            direccion = self.env['main.parameter'].search([])[0].dir_create_file
            vals = {
                'output_name': 'Presupuesto.pdf',
                'output_file': open(direccion + "pressup.pdf", "rb").read().encode("base64"),   
            }
            sfs_id = self.env['export.file.save'].create(vals)
            result = {}
            view_ref = mod_obj.get_object_reference('account_contable_book_it', 'export_file_save_action')
            view_id = view_ref and view_ref[1] or False
            result = act_obj.read( [view_id] )
            print sfs_id
            return {
                "type": "ir.actions.act_window",
                "res_model": "export.file.save",
                "views": [[False, "form"]],
                "res_id": sfs_id.id,
                "target": "new",
            }
        else:

            import io
            from xlsxwriter.workbook import Workbook
            output = io.BytesIO()
            ########### PRIMERA HOJA DE LA DATA EN TABLA
            #workbook = Workbook(output, {'in_memory': True})

            direccion = self.env['main.parameter'].search([])[0].dir_create_file

            workbook = Workbook(direccion +'tempo_presupuestos.xlsx')
            worksheet = workbook.add_worksheet("Presupuesto")
            worksheet_a = workbook.add_worksheet("Importe Real")
            worksheet_b = workbook.add_worksheet("Desviaciones")
            worksheet_c = workbook.add_worksheet("Porcentaje Desviaciones")
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
            numberdos = workbook.add_format({'num_format':'0.00'})
            
            numberdosbold = workbook.add_format({'num_format':'0.00','bold': True})
            bord = workbook.add_format()
            bord.set_border(style=1)
            numberdos.set_border(style=1)
            numbertres.set_border(style=1)          
            x= 4
            tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
            tam_letra = 1.2
            import sys
            reload(sys)
            sys.setdefaultencoding('iso-8859-1')

            worksheet.write(0,0, "Presupuestos por Meses:", bold)
            worksheet.write(0,1, self.fiscalyear_id.name, normal)
            
            worksheet.write(3,0, "C. COSTO",boldbord)
            worksheet.write(3,1, "CONCEPTO",boldbord)
            worksheet.write(3,2, "ENE.",boldbord)
            worksheet.write(3,3, "FEB.",boldbord)
            worksheet.write(3,4, u"MAR.",boldbord)
            worksheet.write(3,5, "ABR.",boldbord)
            worksheet.write(3,6, "MAY.",boldbord)
            worksheet.write(3,7, "JUN.",boldbord)
            worksheet.write(3,8, "JUL.",boldbord)
            worksheet.write(3,9, "AGO.",boldbord)
            worksheet.write(3,10, "SET.",boldbord)
            worksheet.write(3,11, u"OCT.",boldbord)
            worksheet.write(3,12, u"NOV.",boldbord)
            worksheet.write(3,13, u"DIC.",boldbord)
            worksheet.write(3,14, "TOTAL",boldbord)
            

            objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id)])

            cuenta_analiticas_list = []
            posicion_presupuestaria_list = []

            for elem in objetosrecorrer:
                try:
                    xxxx = cuenta_analiticas_list.index(elem.analytic_account_id.name)
                except:
                    cuenta_analiticas_list.append(elem.analytic_account_id.name)

                try:
                    yyyy = posicion_presupuestaria_list.index(elem.general_budget_id.name)
                except:
                    posicion_presupuestaria_list.append(elem.general_budget_id.name)
        
            
            for c_a_l in cuenta_analiticas_list:

                totales = [0,0,0,0,0,0,0,0,0,0,0,0,0]
                for p_p_l in posicion_presupuestaria_list:
                    contador_acum = 0
                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id)])
                    if objetosrecorrer and len(objetosrecorrer)>0:

                        worksheet.write(x,0, c_a_l ,bord)
                        worksheet.write(x,1, p_p_l ,bord)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','01/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet.write(x,2, objetosrecorrer[0].planned_amount ,numberdos)
                            contador_acum += objetosrecorrer[0].planned_amount
                            totales[0] = objetosrecorrer[0].planned_amount
                        else:
                            worksheet.write(x,2, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','02/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet.write(x,3, objetosrecorrer[0].planned_amount ,numberdos)
                            contador_acum += objetosrecorrer[0].planned_amount
                            totales[1] = objetosrecorrer[0].planned_amount
                        else:
                            worksheet.write(x,3, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','03/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet.write(x,4, objetosrecorrer[0].planned_amount ,numberdos)
                            contador_acum += objetosrecorrer[0].planned_amount
                            totales[2] = objetosrecorrer[0].planned_amount
                        else:
                            worksheet.write(x,4, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','04/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet.write(x,5, objetosrecorrer[0].planned_amount ,numberdos)
                            contador_acum += objetosrecorrer[0].planned_amount
                            totales[3] = objetosrecorrer[0].planned_amount
                        else:
                            worksheet.write(x,5, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','05/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet.write(x,6, objetosrecorrer[0].planned_amount ,numberdos)
                            contador_acum += objetosrecorrer[0].planned_amount
                            totales[4] = objetosrecorrer[0].planned_amount
                        else:
                            worksheet.write(x,6, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','06/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet.write(x,7, objetosrecorrer[0].planned_amount ,numberdos)
                            contador_acum += objetosrecorrer[0].planned_amount
                            totales[5] = objetosrecorrer[0].planned_amount
                        else:
                            worksheet.write(x,7, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','07/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet.write(x,8, objetosrecorrer[0].planned_amount ,numberdos)
                            contador_acum += objetosrecorrer[0].planned_amount
                            totales[6] = objetosrecorrer[0].planned_amount
                        else:
                            worksheet.write(x,8, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','08/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet.write(x,9, objetosrecorrer[0].planned_amount ,numberdos)
                            contador_acum += objetosrecorrer[0].planned_amount
                            totales[7] = objetosrecorrer[0].planned_amount
                        else:
                            worksheet.write(x,9, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','09/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet.write(x,10, objetosrecorrer[0].planned_amount ,numberdos)
                            contador_acum += objetosrecorrer[0].planned_amount
                            totales[8] = objetosrecorrer[0].planned_amount
                        else:
                            worksheet.write(x,10, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','10/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet.write(x,11, objetosrecorrer[0].planned_amount ,numberdos)
                            contador_acum += objetosrecorrer[0].planned_amount
                            totales[9] = objetosrecorrer[0].planned_amount
                        else:
                            worksheet.write(x,11, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','11/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet.write(x,12, objetosrecorrer[0].planned_amount ,numberdos)
                            contador_acum += objetosrecorrer[0].planned_amount
                            totales[10] = objetosrecorrer[0].planned_amount
                        else:
                            worksheet.write(x,12, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','12/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet.write(x,13, objetosrecorrer[0].planned_amount ,numberdos)
                            contador_acum += objetosrecorrer[0].planned_amount
                            totales[11] = objetosrecorrer[0].planned_amount
                        else:
                            worksheet.write(x,13, None ,numberdos)

                        worksheet.write(x,14, contador_acum ,numberdos)
                        totales[12] = contador_acum
                        x = x+1


                worksheet.write(x,0, "Total:" ,bold)
                worksheet.write(x,2, totales[0] ,numberdosbold)
                worksheet.write(x,3, totales[1] ,numberdosbold)
                worksheet.write(x,4, totales[2] ,numberdosbold)
                worksheet.write(x,5, totales[3] ,numberdosbold)
                worksheet.write(x,6, totales[4] ,numberdosbold)
                worksheet.write(x,7, totales[5] ,numberdosbold)
                worksheet.write(x,8, totales[6] ,numberdosbold)
                worksheet.write(x,9, totales[7] ,numberdosbold)
                worksheet.write(x,10, totales[8] ,numberdosbold)
                worksheet.write(x,11, totales[9] ,numberdosbold)
                worksheet.write(x,12, totales[10] ,numberdosbold)
                worksheet.write(x,13, totales[11] ,numberdosbold)
                worksheet.write(x,14, totales[12] ,numberdosbold)
                x = x+3


            tam_col = [25,25,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14]


            worksheet.set_column('A:A', tam_col[0])
            worksheet.set_column('B:B', tam_col[1])
            worksheet.set_column('C:C', tam_col[2])
            worksheet.set_column('D:D', tam_col[3])
            worksheet.set_column('E:E', tam_col[4])
            worksheet.set_column('F:F', tam_col[5])
            worksheet.set_column('G:G', tam_col[6])
            worksheet.set_column('H:H', tam_col[7])
            worksheet.set_column('I:I', tam_col[8])
            worksheet.set_column('J:J', tam_col[9])
            worksheet.set_column('K:K', tam_col[10])
            worksheet.set_column('L:L', tam_col[11])
            worksheet.set_column('M:M', tam_col[12])
            worksheet.set_column('N:N', tam_col[13])
            worksheet.set_column('O:O', tam_col[14])
            worksheet.set_column('P:P', tam_col[15])
            worksheet.set_column('Q:Q', tam_col[16])
            worksheet.set_column('R:R', tam_col[17])
            worksheet.set_column('S:S', tam_col[18])
            worksheet.set_column('T:T', tam_col[19])

            ################################################


            x= 4
            worksheet_a.write(0,0, "Importe Real por Meses:", bold)
            worksheet_a.write(0,1, self.fiscalyear_id.name, normal)
            
            worksheet_a.write(3,0, "C. COSTO",boldbord)
            worksheet_a.write(3,1, "CONCEPTO",boldbord)
            worksheet_a.write(3,2, "ENE.",boldbord)
            worksheet_a.write(3,3, "FEB.",boldbord)
            worksheet_a.write(3,4, u"MAR.",boldbord)
            worksheet_a.write(3,5, "ABR.",boldbord)
            worksheet_a.write(3,6, "MAY.",boldbord)
            worksheet_a.write(3,7, "JUN.",boldbord)
            worksheet_a.write(3,8, "JUL.",boldbord)
            worksheet_a.write(3,9, "AGO.",boldbord)
            worksheet_a.write(3,10, "SET.",boldbord)
            worksheet_a.write(3,11, u"OCT.",boldbord)
            worksheet_a.write(3,12, u"NOV.",boldbord)
            worksheet_a.write(3,13, u"DIC.",boldbord)
            worksheet_a.write(3,14, "TOTAL",boldbord)
            

            objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id)])

            cuenta_analiticas_list = []
            posicion_presupuestaria_list = []

            for elem in objetosrecorrer:
                try:
                    xxxxxx = cuenta_analiticas_list.index(elem.analytic_account_id.name)
                except:
                    cuenta_analiticas_list.append(elem.analytic_account_id.name)

                try:
                    yyyyyyy = posicion_presupuestaria_list.index(elem.general_budget_id.name)
                except:
                    posicion_presupuestaria_list.append(elem.general_budget_id.name)
        
            
            for c_a_l in cuenta_analiticas_list:

                totales = [0,0,0,0,0,0,0,0,0,0,0,0,0]
                for p_p_l in posicion_presupuestaria_list:
                    contador_acum = 0
                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id)])
                    if objetosrecorrer and len(objetosrecorrer)>0:

                        worksheet_a.write(x,0, c_a_l ,bord)
                        worksheet_a.write(x,1, p_p_l ,bord)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','01/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet_a.write(x,2, objetosrecorrer[0].importe_real ,numberdos)
                            contador_acum += objetosrecorrer[0].importe_real
                            totales[0] = objetosrecorrer[0].importe_real
                        else:
                            worksheet_a.write(x,2, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','02/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet_a.write(x,3, objetosrecorrer[0].importe_real ,numberdos)
                            contador_acum += objetosrecorrer[0].importe_real
                            totales[1] = objetosrecorrer[0].importe_real
                        else:
                            worksheet_a.write(x,3, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','03/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet_a.write(x,4, objetosrecorrer[0].importe_real ,numberdos)
                            contador_acum += objetosrecorrer[0].importe_real
                            totales[2] = objetosrecorrer[0].importe_real
                        else:
                            worksheet_a.write(x,4, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','04/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet_a.write(x,5, objetosrecorrer[0].importe_real ,numberdos)
                            contador_acum += objetosrecorrer[0].importe_real
                            totales[3] = objetosrecorrer[0].importe_real
                        else:
                            worksheet_a.write(x,5, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','05/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet_a.write(x,6, objetosrecorrer[0].importe_real ,numberdos)
                            contador_acum += objetosrecorrer[0].importe_real
                            totales[4] = objetosrecorrer[0].importe_real
                        else:
                            worksheet_a.write(x,6, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','06/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet_a.write(x,7, objetosrecorrer[0].importe_real ,numberdos)
                            contador_acum += objetosrecorrer[0].importe_real
                            totales[5] = objetosrecorrer[0].importe_real
                        else:
                            worksheet_a.write(x,7, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','07/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet_a.write(x,8, objetosrecorrer[0].importe_real ,numberdos)
                            contador_acum += objetosrecorrer[0].importe_real
                            totales[6] = objetosrecorrer[0].importe_real
                        else:
                            worksheet_a.write(x,8, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','08/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet_a.write(x,9, objetosrecorrer[0].importe_real ,numberdos)
                            contador_acum += objetosrecorrer[0].importe_real
                            totales[7] = objetosrecorrer[0].importe_real
                        else:
                            worksheet_a.write(x,9, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','09/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet_a.write(x,10, objetosrecorrer[0].importe_real ,numberdos)
                            contador_acum += objetosrecorrer[0].importe_real
                            totales[8] = objetosrecorrer[0].importe_real
                        else:
                            worksheet_a.write(x,10, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','10/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet_a.write(x,11, objetosrecorrer[0].importe_real ,numberdos)
                            contador_acum += objetosrecorrer[0].importe_real
                            totales[9] = objetosrecorrer[0].importe_real
                        else:
                            worksheet_a.write(x,11, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','11/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet_a.write(x,12, objetosrecorrer[0].importe_real ,numberdos)
                            contador_acum += objetosrecorrer[0].importe_real
                            totales[10] = objetosrecorrer[0].importe_real
                        else:
                            worksheet_a.write(x,12, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','12/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet_a.write(x,13, objetosrecorrer[0].importe_real ,numberdos)
                            contador_acum += objetosrecorrer[0].importe_real
                            totales[11] = objetosrecorrer[0].importe_real
                        else:
                            worksheet_a.write(x,13, None ,numberdos)

                        worksheet_a.write(x,14, contador_acum ,numberdos)
                        totales[12] = contador_acum
                        x = x+1


                worksheet_a.write(x,0, "Total:" ,bold)
                worksheet_a.write(x,2, totales[0] ,numberdosbold)
                worksheet_a.write(x,3, totales[1] ,numberdosbold)
                worksheet_a.write(x,4, totales[2] ,numberdosbold)
                worksheet_a.write(x,5, totales[3] ,numberdosbold)
                worksheet_a.write(x,6, totales[4] ,numberdosbold)
                worksheet_a.write(x,7, totales[5] ,numberdosbold)
                worksheet_a.write(x,8, totales[6] ,numberdosbold)
                worksheet_a.write(x,9, totales[7] ,numberdosbold)
                worksheet_a.write(x,10, totales[8] ,numberdosbold)
                worksheet_a.write(x,11, totales[9] ,numberdosbold)
                worksheet_a.write(x,12, totales[10] ,numberdosbold)
                worksheet_a.write(x,13, totales[11] ,numberdosbold)
                worksheet_a.write(x,14, totales[12] ,numberdosbold)
                x = x+3


            tam_col = [25,25,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14]


            worksheet_a.set_column('A:A', tam_col[0])
            worksheet_a.set_column('B:B', tam_col[1])
            worksheet_a.set_column('C:C', tam_col[2])
            worksheet_a.set_column('D:D', tam_col[3])
            worksheet_a.set_column('E:E', tam_col[4])
            worksheet_a.set_column('F:F', tam_col[5])
            worksheet_a.set_column('G:G', tam_col[6])
            worksheet_a.set_column('H:H', tam_col[7])
            worksheet_a.set_column('I:I', tam_col[8])
            worksheet_a.set_column('J:J', tam_col[9])
            worksheet_a.set_column('K:K', tam_col[10])
            worksheet_a.set_column('L:L', tam_col[11])
            worksheet_a.set_column('M:M', tam_col[12])
            worksheet_a.set_column('N:N', tam_col[13])
            worksheet_a.set_column('O:O', tam_col[14])
            worksheet_a.set_column('P:P', tam_col[15])
            worksheet_a.set_column('Q:Q', tam_col[16])
            worksheet_a.set_column('R:R', tam_col[17])
            worksheet_a.set_column('S:S', tam_col[18])
            worksheet_a.set_column('T:T', tam_col[19])

            ###################################################


            x= 4
            worksheet_b.write(0,0, "Desviaciones por Meses:", bold)
            worksheet_b.write(0,1, self.fiscalyear_id.name, normal)
            
            worksheet_b.write(3,0, "C. COSTO",boldbord)
            worksheet_b.write(3,1, "CONCEPTO",boldbord)
            worksheet_b.write(3,2, "ENE.",boldbord)
            worksheet_b.write(3,3, "FEB.",boldbord)
            worksheet_b.write(3,4, u"MAR.",boldbord)
            worksheet_b.write(3,5, "ABR.",boldbord)
            worksheet_b.write(3,6, "MAY.",boldbord)
            worksheet_b.write(3,7, "JUN.",boldbord)
            worksheet_b.write(3,8, "JUL.",boldbord)
            worksheet_b.write(3,9, "AGO.",boldbord)
            worksheet_b.write(3,10, "SET.",boldbord)
            worksheet_b.write(3,11, u"OCT.",boldbord)
            worksheet_b.write(3,12, u"NOV.",boldbord)
            worksheet_b.write(3,13, u"DIC.",boldbord)
            worksheet_b.write(3,14, "TOTAL",boldbord)
            

            objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id)])

            cuenta_analiticas_list = []
            posicion_presupuestaria_list = []

            for elem in objetosrecorrer:
                try:
                    xxxxx = cuenta_analiticas_list.index(elem.analytic_account_id.name)
                except:
                    cuenta_analiticas_list.append(elem.analytic_account_id.name)

                try:
                    yyyyyy = posicion_presupuestaria_list.index(elem.general_budget_id.name)
                except:
                    posicion_presupuestaria_list.append(elem.general_budget_id.name)
        
            
            for c_a_l in cuenta_analiticas_list:

                totales = [0,0,0,0,0,0,0,0,0,0,0,0,0]
                for p_p_l in posicion_presupuestaria_list:
                    contador_acum = 0
                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id)])
                    if objetosrecorrer and len(objetosrecorrer)>0:

                        worksheet_b.write(x,0, c_a_l ,bord)
                        worksheet_b.write(x,1, p_p_l ,bord)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','01/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet_b.write(x,2, objetosrecorrer[0].desviacion ,numberdos)
                            contador_acum += objetosrecorrer[0].desviacion
                            totales[0] = objetosrecorrer[0].desviacion
                        else:
                            worksheet_b.write(x,2, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','02/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet_b.write(x,3, objetosrecorrer[0].desviacion ,numberdos)
                            contador_acum += objetosrecorrer[0].desviacion
                            totales[1] = objetosrecorrer[0].desviacion
                        else:
                            worksheet_b.write(x,3, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','03/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet_b.write(x,4, objetosrecorrer[0].desviacion ,numberdos)
                            contador_acum += objetosrecorrer[0].desviacion
                            totales[2] = objetosrecorrer[0].desviacion
                        else:
                            worksheet_b.write(x,4, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','04/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet_b.write(x,5, objetosrecorrer[0].desviacion ,numberdos)
                            contador_acum += objetosrecorrer[0].desviacion
                            totales[3] = objetosrecorrer[0].desviacion
                        else:
                            worksheet_b.write(x,5, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','05/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet_b.write(x,6, objetosrecorrer[0].desviacion ,numberdos)
                            contador_acum += objetosrecorrer[0].desviacion
                            totales[4] = objetosrecorrer[0].desviacion
                        else:
                            worksheet_b.write(x,6, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','06/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet_b.write(x,7, objetosrecorrer[0].desviacion ,numberdos)
                            contador_acum += objetosrecorrer[0].desviacion
                            totales[5] = objetosrecorrer[0].desviacion
                        else:
                            worksheet_b.write(x,7, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','07/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet_b.write(x,8, objetosrecorrer[0].desviacion ,numberdos)
                            contador_acum += objetosrecorrer[0].desviacion
                            totales[6] = objetosrecorrer[0].desviacion
                        else:
                            worksheet_b.write(x,8, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','08/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet_b.write(x,9, objetosrecorrer[0].desviacion ,numberdos)
                            contador_acum += objetosrecorrer[0].desviacion
                            totales[7] = objetosrecorrer[0].desviacion
                        else:
                            worksheet_b.write(x,9, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','09/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet_b.write(x,10, objetosrecorrer[0].desviacion ,numberdos)
                            contador_acum += objetosrecorrer[0].desviacion
                            totales[8] = objetosrecorrer[0].desviacion
                        else:
                            worksheet_b.write(x,10, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','10/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet_b.write(x,11, objetosrecorrer[0].desviacion ,numberdos)
                            contador_acum += objetosrecorrer[0].desviacion
                            totales[9] = objetosrecorrer[0].desviacion
                        else:
                            worksheet_b.write(x,11, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','11/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet_b.write(x,12, objetosrecorrer[0].desviacion ,numberdos)
                            contador_acum += objetosrecorrer[0].desviacion
                            totales[10] = objetosrecorrer[0].desviacion
                        else:
                            worksheet_b.write(x,12, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','12/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet_b.write(x,13, objetosrecorrer[0].desviacion ,numberdos)
                            contador_acum += objetosrecorrer[0].desviacion
                            totales[11] = objetosrecorrer[0].desviacion
                        else:
                            worksheet_b.write(x,13, None ,numberdos)

                        worksheet_b.write(x,14, contador_acum ,numberdos)
                        totales[12] = contador_acum
                        x = x+1


                worksheet_b.write(x,0, "Total:" ,bold)
                worksheet_b.write(x,2, totales[0] ,numberdosbold)
                worksheet_b.write(x,3, totales[1] ,numberdosbold)
                worksheet_b.write(x,4, totales[2] ,numberdosbold)
                worksheet_b.write(x,5, totales[3] ,numberdosbold)
                worksheet_b.write(x,6, totales[4] ,numberdosbold)
                worksheet_b.write(x,7, totales[5] ,numberdosbold)
                worksheet_b.write(x,8, totales[6] ,numberdosbold)
                worksheet_b.write(x,9, totales[7] ,numberdosbold)
                worksheet_b.write(x,10, totales[8] ,numberdosbold)
                worksheet_b.write(x,11, totales[9] ,numberdosbold)
                worksheet_b.write(x,12, totales[10] ,numberdosbold)
                worksheet_b.write(x,13, totales[11] ,numberdosbold)
                worksheet_b.write(x,14, totales[12] ,numberdosbold)
                x = x+3


            tam_col = [25,25,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14]


            worksheet_b.set_column('A:A', tam_col[0])
            worksheet_b.set_column('B:B', tam_col[1])
            worksheet_b.set_column('C:C', tam_col[2])
            worksheet_b.set_column('D:D', tam_col[3])
            worksheet_b.set_column('E:E', tam_col[4])
            worksheet_b.set_column('F:F', tam_col[5])
            worksheet_b.set_column('G:G', tam_col[6])
            worksheet_b.set_column('H:H', tam_col[7])
            worksheet_b.set_column('I:I', tam_col[8])
            worksheet_b.set_column('J:J', tam_col[9])
            worksheet_b.set_column('K:K', tam_col[10])
            worksheet_b.set_column('L:L', tam_col[11])
            worksheet_b.set_column('M:M', tam_col[12])
            worksheet_b.set_column('N:N', tam_col[13])
            worksheet_b.set_column('O:O', tam_col[14])
            worksheet_b.set_column('P:P', tam_col[15])
            worksheet_b.set_column('Q:Q', tam_col[16])
            worksheet_b.set_column('R:R', tam_col[17])
            worksheet_b.set_column('S:S', tam_col[18])
            worksheet_b.set_column('T:T', tam_col[19])



            ###################################################


            x= 4
            worksheet_c.write(0,0, "Porcentaje Desviaciones por Meses:", bold)
            worksheet_c.write(0,1, self.fiscalyear_id.name, normal)
            
            worksheet_c.write(3,0, "C. COSTO",boldbord)
            worksheet_c.write(3,1, "CONCEPTO",boldbord)
            worksheet_c.write(3,2, "ENE.",boldbord)
            worksheet_c.write(3,3, "FEB.",boldbord)
            worksheet_c.write(3,4, u"MAR.",boldbord)
            worksheet_c.write(3,5, "ABR.",boldbord)
            worksheet_c.write(3,6, "MAY.",boldbord)
            worksheet_c.write(3,7, "JUN.",boldbord)
            worksheet_c.write(3,8, "JUL.",boldbord)
            worksheet_c.write(3,9, "AGO.",boldbord)
            worksheet_c.write(3,10, "SET.",boldbord)
            worksheet_c.write(3,11, u"OCT.",boldbord)
            worksheet_c.write(3,12, u"NOV.",boldbord)
            worksheet_c.write(3,13, u"DIC.",boldbord)
            worksheet_c.write(3,14, "TOTAL",boldbord)
            

            objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id)])

            cuenta_analiticas_list = []
            posicion_presupuestaria_list = []

            for elem in objetosrecorrer:
                try:
                    xxxxx = cuenta_analiticas_list.index(elem.analytic_account_id.name)
                except:
                    cuenta_analiticas_list.append(elem.analytic_account_id.name)

                try:
                    yyyyyy = posicion_presupuestaria_list.index(elem.general_budget_id.name)
                except:
                    posicion_presupuestaria_list.append(elem.general_budget_id.name)
        
            
            for c_a_l in cuenta_analiticas_list:

                totales = [0,0,0,0,0,0,0,0,0,0,0,0,0]
                for p_p_l in posicion_presupuestaria_list:
                    contador_acum = 0
                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id)])
                    if objetosrecorrer and len(objetosrecorrer)>0:

                        worksheet_c.write(x,0, c_a_l ,bord)
                        worksheet_c.write(x,1, p_p_l ,bord)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','01/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet_c.write(x,2, ("%0.2f"% objetosrecorrer[0].porcentaje_real_decimal) + " %" ,bord)
                            contador_acum += objetosrecorrer[0].porcentaje_real_decimal
                            totales[0] = objetosrecorrer[0].porcentaje_real_decimal
                        else:
                            worksheet_c.write(x,2, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','02/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet_c.write(x,3, ("%0.2f"% objetosrecorrer[0].porcentaje_real_decimal) + " %" ,bord)
                            contador_acum += objetosrecorrer[0].porcentaje_real_decimal
                            totales[1] = objetosrecorrer[0].porcentaje_real_decimal
                        else:
                            worksheet_c.write(x,3, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','03/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet_c.write(x,4, ("%0.2f"% objetosrecorrer[0].porcentaje_real_decimal) + " %" ,bord)
                            contador_acum += objetosrecorrer[0].porcentaje_real_decimal
                            totales[2] = objetosrecorrer[0].porcentaje_real_decimal
                        else:
                            worksheet_c.write(x,4, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','04/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet_c.write(x,5, ("%0.2f"% objetosrecorrer[0].porcentaje_real_decimal) + " %" ,bord)
                            contador_acum += objetosrecorrer[0].porcentaje_real_decimal
                            totales[3] = objetosrecorrer[0].porcentaje_real_decimal
                        else:
                            worksheet_c.write(x,5, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','05/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet_c.write(x,6, ("%0.2f"% objetosrecorrer[0].porcentaje_real_decimal) + " %" ,bord)
                            contador_acum += objetosrecorrer[0].porcentaje_real_decimal
                            totales[4] = objetosrecorrer[0].porcentaje_real_decimal
                        else:
                            worksheet_c.write(x,6, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','06/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet_c.write(x,7, ("%0.2f"% objetosrecorrer[0].porcentaje_real_decimal) + " %" ,bord)
                            contador_acum += objetosrecorrer[0].porcentaje_real_decimal
                            totales[5] = objetosrecorrer[0].porcentaje_real_decimal
                        else:
                            worksheet_c.write(x,7, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','07/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet_c.write(x,8, ("%0.2f"% objetosrecorrer[0].porcentaje_real_decimal) + " %" ,bord)
                            contador_acum += objetosrecorrer[0].porcentaje_real_decimal
                            totales[6] = objetosrecorrer[0].porcentaje_real_decimal
                        else:
                            worksheet_c.write(x,8, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','08/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet_c.write(x,9, ("%0.2f"% objetosrecorrer[0].porcentaje_real_decimal) + " %" ,bord)
                            contador_acum += objetosrecorrer[0].porcentaje_real_decimal
                            totales[7] = objetosrecorrer[0].porcentaje_real_decimal
                        else:
                            worksheet_c.write(x,9, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','09/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet_c.write(x,10, ("%0.2f"% objetosrecorrer[0].porcentaje_real_decimal) + " %" ,bord)
                            contador_acum += objetosrecorrer[0].porcentaje_real_decimal
                            totales[8] = objetosrecorrer[0].porcentaje_real_decimal
                        else:
                            worksheet_c.write(x,10, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','10/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet_c.write(x,11, ("%0.2f"% objetosrecorrer[0].porcentaje_real_decimal) + " %" ,bord)
                            contador_acum += objetosrecorrer[0].porcentaje_real_decimal
                            totales[9] = objetosrecorrer[0].porcentaje_real_decimal
                        else:
                            worksheet_c.write(x,11, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','11/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet_c.write(x,12, ("%0.2f"% objetosrecorrer[0].porcentaje_real_decimal) + " %" ,bord)
                            contador_acum += objetosrecorrer[0].porcentaje_real_decimal
                            totales[10] = objetosrecorrer[0].porcentaje_real_decimal
                        else:
                            worksheet_c.write(x,12, None ,numberdos)

                        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','12/'+ self.fiscalyear_id.name)])
                        if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                            worksheet_c.write(x,13, ("%0.2f"% objetosrecorrer[0].porcentaje_real_decimal) + " %" ,bord)
                            contador_acum += objetosrecorrer[0].porcentaje_real_decimal
                            totales[11] = objetosrecorrer[0].porcentaje_real_decimal
                        else:
                            worksheet_c.write(x,13, None ,numberdos)

                        worksheet_c.write(x,14, ("%0.2f"% contador_acum) + " %" ,numberdos)
                        totales[12] = contador_acum
                        x = x+1


                worksheet_c.write(x,0, "Total:" ,bold)
                worksheet_c.write(x,2, ("%0.2f"% totales[0]) + " %" ,bold)
                worksheet_c.write(x,3, ("%0.2f"% totales[1]) + " %"  ,bold)
                worksheet_c.write(x,4, ("%0.2f"% totales[2]) + " %"  ,bold)
                worksheet_c.write(x,5, ("%0.2f"% totales[3]) + " %"  ,bold)
                worksheet_c.write(x,6, ("%0.2f"% totales[4]) + " %"  ,bold)
                worksheet_c.write(x,7, ("%0.2f"% totales[5]) + " %"  ,bold)
                worksheet_c.write(x,8, ("%0.2f"% totales[6]) + " %"  ,bold)
                worksheet_c.write(x,9, ("%0.2f"% totales[7]) + " %"  ,bold)
                worksheet_c.write(x,10, ("%0.2f"% totales[8]) + " %"  ,bold)
                worksheet_c.write(x,11, ("%0.2f"% totales[9]) + " %"  ,bold)
                worksheet_c.write(x,12, ("%0.2f"% totales[10]) + " %"  ,bold)
                worksheet_c.write(x,13, ("%0.2f"% totales[11]) + " %"  ,bold)
                worksheet_c.write(x,14, ("%0.2f"% totales[12]) + " %"  ,bold)
                x = x+3


            tam_col = [25,25,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14,14]


            worksheet_c.set_column('A:A', tam_col[0])
            worksheet_c.set_column('B:B', tam_col[1])
            worksheet_c.set_column('C:C', tam_col[2])
            worksheet_c.set_column('D:D', tam_col[3])
            worksheet_c.set_column('E:E', tam_col[4])
            worksheet_c.set_column('F:F', tam_col[5])
            worksheet_c.set_column('G:G', tam_col[6])
            worksheet_c.set_column('H:H', tam_col[7])
            worksheet_c.set_column('I:I', tam_col[8])
            worksheet_c.set_column('J:J', tam_col[9])
            worksheet_c.set_column('K:K', tam_col[10])
            worksheet_c.set_column('L:L', tam_col[11])
            worksheet_c.set_column('M:M', tam_col[12])
            worksheet_c.set_column('N:N', tam_col[13])
            worksheet_c.set_column('O:O', tam_col[14])
            worksheet_c.set_column('P:P', tam_col[15])
            worksheet_c.set_column('Q:Q', tam_col[16])
            worksheet_c.set_column('R:R', tam_col[17])
            worksheet_c.set_column('S:S', tam_col[18])
            worksheet_c.set_column('T:T', tam_col[19])

            workbook.close()
            
            f = open(direccion + 'tempo_presupuestos.xlsx', 'rb')
            
            
            sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
            vals = {
                'output_name': 'Presupuestos.xlsx',
                'output_file': base64.encodestring(''.join(f.readlines())),     
            }

            mod_obj = self.env['ir.model.data']
            act_obj = self.env['ir.actions.act_window']
            sfs_id = self.env['export.file.save'].create(vals)
            result = {}
            view_ref = mod_obj.get_object_reference('account_contable_book_it', 'export_file_save_action')
            view_id = view_ref and view_ref[1] or False
            result = act_obj.read( [view_id] )
            print sfs_id

            #import os
            #os.system('c:\\eSpeak2\\command_line\\espeak.exe -ves-f1 -s 170 -p 100 "Se Realizo La exportación exitosamente Y A EDWARD NO LE GUSTA XDXDXDXDDDDDDDDDDDD" ')

            return {
                "type": "ir.actions.act_window",
                "res_model": "export.file.save",
                "views": [[False, "form"]],
                "res_id": sfs_id.id,
                "target": "new",
            }




    @api.multi
    def cabezera(self,c,wReal,hReal):
        c.setFont("Calibri-Bold", 18)
        c.setFillColor(black)
        c.drawCentredString((wReal/2)+20,hReal, u"PRESUPUESTO ANUAL "+ self.env["res.company"].search([])[0].name.upper() + u" AÑO "+ self.fiscalyear_id.name )
        c.line((wReal/2)+20-170,hReal-3,(wReal/2)+20+170,hReal-3)


    @api.multi
    def x_aument(self,a):
        a[0] = a[0]+1

    @api.multi
    def reporteador(self):


        import sys
        reload(sys)
        sys.setdefaultencoding('iso-8859-1')


        pdfmetrics.registerFont(TTFont('Calibri', 'Calibri.ttf'))
        pdfmetrics.registerFont(TTFont('Calibri-Bold', 'CalibriBold.ttf'))

        width ,height  = A4  # 595 , 842
        wReal = height- 30
        hReal = width - 40

        direccion = self.env['main.parameter'].search([])[0].dir_create_file
        c = canvas.Canvas( direccion + "pressup.pdf", pagesize= (height,width) )
        inicio = 0
        pos_inicial = hReal-28
        libro = None
        voucher = None
        total = 0
        debeTotal = 0
        haberTotal = 0
        pagina = 1
        textPos = 0
        
        self.cabezera(c,wReal,hReal)

        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id)])

        cuenta_analiticas_list = []
        posicion_presupuestaria_list = []

        for elem in objetosrecorrer:
            try:
                x = cuenta_analiticas_list.index(elem.analytic_account_id.name)
            except:
                cuenta_analiticas_list.append(elem.analytic_account_id.name)

            try:
                y = posicion_presupuestaria_list.index(elem.general_budget_id.name)
            except:
                posicion_presupuestaria_list.append(elem.general_budget_id.name)

        tamanios = [60,90,51,51,51,51,51,51,51,51,51,51,51,51,51]
        titulos_cab = ['C. COSTO','CONCEPTO','ENE','FEB','MAR','ABR','MAY','JUN','JUL','AGO','SEP','OCT','NOV','DIC','TOTAL']
        
        
        c.setFont("Calibri-Bold", 7)
        c.drawString( 10 ,pos_inicial, u'PRESUPUESTADO' )

        pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,15,pagina)

        fondo = HexColor('#d3eaf1')
        c.setFillColor(fondo)
        c.rect(10,pos_inicial-3,813,10, fill=True,stroke=False)
        c.setFillColor(colors.black)
 
        recorredor_t = 0
        acum_titulo = 10
        for i_titulo in titulos_cab:
            c.drawString( acum_titulo , pos_inicial, i_titulo )

            acum_titulo+= tamanios[recorredor_t]
            recorredor_t +=1


        pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,10,pagina)
        
        for c_a_l in cuenta_analiticas_list:

            totales = [0,0,0,0,0,0,0,0,0,0,0,0,0]
            for p_p_l in posicion_presupuestaria_list:
                contador_acum = 0
                objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id)])
                if objetosrecorrer and len(objetosrecorrer)>0:

                    c.setFont("Calibri", 7)
                    c.drawString( 10 ,pos_inicial, c_a_l )
                    c.drawString( 70 , pos_inicial, p_p_l )

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','01/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 209 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% objetosrecorrer[0].planned_amount )))
                        contador_acum += objetosrecorrer[0].planned_amount
                        totales[0] = objetosrecorrer[0].planned_amount

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','02/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 260 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% objetosrecorrer[0].planned_amount )))
                        contador_acum += objetosrecorrer[0].planned_amount
                        totales[1] = objetosrecorrer[0].planned_amount

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','03/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 311 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% objetosrecorrer[0].planned_amount )))
                        contador_acum += objetosrecorrer[0].planned_amount
                        totales[2] = objetosrecorrer[0].planned_amount

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','04/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 362 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% objetosrecorrer[0].planned_amount )))
                        contador_acum += objetosrecorrer[0].planned_amount
                        totales[3] = objetosrecorrer[0].planned_amount

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','05/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 413 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% objetosrecorrer[0].planned_amount )))
                        contador_acum += objetosrecorrer[0].planned_amount
                        totales[4] = objetosrecorrer[0].planned_amount

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','06/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 464 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% objetosrecorrer[0].planned_amount )))
                        contador_acum += objetosrecorrer[0].planned_amount
                        totales[5] = objetosrecorrer[0].planned_amount

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','07/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 515 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% objetosrecorrer[0].planned_amount )))
                        contador_acum += objetosrecorrer[0].planned_amount
                        totales[6] = objetosrecorrer[0].planned_amount

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','08/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 566 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% objetosrecorrer[0].planned_amount )))
                        contador_acum += objetosrecorrer[0].planned_amount
                        totales[7] = objetosrecorrer[0].planned_amount

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','09/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 617 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% objetosrecorrer[0].planned_amount )))
                        contador_acum += objetosrecorrer[0].planned_amount
                        totales[8] = objetosrecorrer[0].planned_amount

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','10/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 668 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% objetosrecorrer[0].planned_amount )))
                        contador_acum += objetosrecorrer[0].planned_amount
                        totales[9] = objetosrecorrer[0].planned_amount

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','11/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 719 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% objetosrecorrer[0].planned_amount )))
                        contador_acum += objetosrecorrer[0].planned_amount
                        totales[10] = objetosrecorrer[0].planned_amount

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','12/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 770 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% objetosrecorrer[0].planned_amount )))
                        contador_acum += objetosrecorrer[0].planned_amount
                        totales[11] = objetosrecorrer[0].planned_amount
                    
                    c.drawRightString( 821 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% contador_acum )))
                    totales[12] = contador_acum


                    pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,10,pagina)


            c.setFont("Calibri-Bold", 7)
            c.line(158,pos_inicial+7, 823,pos_inicial+7)
            c.line(158,pos_inicial-2, 823,pos_inicial-2)
            c.line(158,pos_inicial-4, 823,pos_inicial-4)
            c.drawRightString( 209 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[0] )))
            c.drawRightString( 260 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[1] )))
            c.drawRightString( 311 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[2] )))
            c.drawRightString( 362 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[3] )))
            c.drawRightString( 413 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[4] )))
            c.drawRightString( 464 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[5] )))
            c.drawRightString( 515 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[6] )))
            c.drawRightString( 566 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[7] )))
            c.drawRightString( 617 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[8] )))
            c.drawRightString( 668 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[9] )))
            c.drawRightString( 719 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[10] )))
            c.drawRightString( 770 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[11] )))
            c.drawRightString( 821 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[12] )))

            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
        c.showPage()
            #############################


        inicio = 0
        pos_inicial = hReal-28
        libro = None
        voucher = None
        total = 0
        debeTotal = 0
        haberTotal = 0
        pagina = 1
        textPos = 0
        
        self.cabezera(c,wReal,hReal)

        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id)])

        cuenta_analiticas_list = []
        posicion_presupuestaria_list = []

        for elem in objetosrecorrer:
            try:
                x = cuenta_analiticas_list.index(elem.analytic_account_id.name)
            except:
                cuenta_analiticas_list.append(elem.analytic_account_id.name)

            try:
                y = posicion_presupuestaria_list.index(elem.general_budget_id.name)
            except:
                posicion_presupuestaria_list.append(elem.general_budget_id.name)

        tamanios = [60,90,51,51,51,51,51,51,51,51,51,51,51,51,51]
        titulos_cab = ['C. COSTO','CONCEPTO','ENE','FEB','MAR','ABR','MAY','JUN','JUL','AGO','SEP','OCT','NOV','DIC','TOTAL']
        
        
        c.setFont("Calibri-Bold", 7)
        c.drawString( 10 ,pos_inicial, u'IMPORTE REAL' )

        pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,15,pagina)

        fondo = HexColor('#d3eaf1')
        c.setFillColor(fondo)
        c.rect(10,pos_inicial-3,813,10, fill=True,stroke=False)
        c.setFillColor(colors.black)
 
        recorredor_t = 0
        acum_titulo = 10
        for i_titulo in titulos_cab:
            c.drawString( acum_titulo , pos_inicial, i_titulo )

            acum_titulo+= tamanios[recorredor_t]
            recorredor_t +=1


        pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,10,pagina)
        
        for c_a_l in cuenta_analiticas_list:

            totales = [0,0,0,0,0,0,0,0,0,0,0,0,0]
            for p_p_l in posicion_presupuestaria_list:
                contador_acum = 0
                objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id)])
                if objetosrecorrer and len(objetosrecorrer)>0:

                    c.setFont("Calibri", 7)
                    c.drawString( 10 ,pos_inicial, c_a_l )
                    c.drawString( 70 , pos_inicial, p_p_l )

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','01/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 209 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% objetosrecorrer[0].importe_real )))
                        contador_acum += objetosrecorrer[0].importe_real
                        totales[0] = objetosrecorrer[0].importe_real

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','02/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 260 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% objetosrecorrer[0].importe_real )))
                        contador_acum += objetosrecorrer[0].importe_real
                        totales[1] = objetosrecorrer[0].importe_real

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','03/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 311 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% objetosrecorrer[0].importe_real )))
                        contador_acum += objetosrecorrer[0].importe_real
                        totales[2] = objetosrecorrer[0].importe_real

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','04/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 362 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% objetosrecorrer[0].importe_real )))
                        contador_acum += objetosrecorrer[0].importe_real
                        totales[3] = objetosrecorrer[0].importe_real

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','05/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 413 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% objetosrecorrer[0].importe_real )))
                        contador_acum += objetosrecorrer[0].importe_real
                        totales[4] = objetosrecorrer[0].importe_real

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','06/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 464 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% objetosrecorrer[0].importe_real )))
                        contador_acum += objetosrecorrer[0].importe_real
                        totales[5] = objetosrecorrer[0].importe_real

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','07/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 515 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% objetosrecorrer[0].importe_real )))
                        contador_acum += objetosrecorrer[0].importe_real
                        totales[6] = objetosrecorrer[0].importe_real

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','08/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 566 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% objetosrecorrer[0].importe_real )))
                        contador_acum += objetosrecorrer[0].importe_real
                        totales[7] = objetosrecorrer[0].importe_real

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','09/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 617 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% objetosrecorrer[0].importe_real )))
                        contador_acum += objetosrecorrer[0].importe_real
                        totales[8] = objetosrecorrer[0].importe_real

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','10/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 668 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% objetosrecorrer[0].importe_real )))
                        contador_acum += objetosrecorrer[0].importe_real
                        totales[9] = objetosrecorrer[0].importe_real

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','11/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 719 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% objetosrecorrer[0].importe_real )))
                        contador_acum += objetosrecorrer[0].importe_real
                        totales[10] = objetosrecorrer[0].importe_real

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','12/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 770 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% objetosrecorrer[0].importe_real )))
                        contador_acum += objetosrecorrer[0].importe_real
                        totales[11] = objetosrecorrer[0].importe_real

                    c.drawRightString( 821 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% contador_acum )))
                    totales[12] = contador_acum


                    pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,10,pagina)


            c.setFont("Calibri-Bold", 7)
            c.line(158,pos_inicial+7, 823,pos_inicial+7)
            c.line(158,pos_inicial-2, 823,pos_inicial-2)
            c.line(158,pos_inicial-4, 823,pos_inicial-4)
            c.drawRightString( 209 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[0] )))
            c.drawRightString( 260 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[1] )))
            c.drawRightString( 311 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[2] )))
            c.drawRightString( 362 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[3] )))
            c.drawRightString( 413 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[4] )))
            c.drawRightString( 464 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[5] )))
            c.drawRightString( 515 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[6] )))
            c.drawRightString( 566 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[7] )))
            c.drawRightString( 617 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[8] )))
            c.drawRightString( 668 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[9] )))
            c.drawRightString( 719 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[10] )))
            c.drawRightString( 770 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[11] )))
            c.drawRightString( 821 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[12] )))


            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
        c.showPage()

            ############################


        inicio = 0
        pos_inicial = hReal-28
        libro = None
        voucher = None
        total = 0
        debeTotal = 0
        haberTotal = 0
        pagina = 1
        textPos = 0
        
        self.cabezera(c,wReal,hReal)

        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id)])

        cuenta_analiticas_list = []
        posicion_presupuestaria_list = []

        for elem in objetosrecorrer:
            try:
                x = cuenta_analiticas_list.index(elem.analytic_account_id.name)
            except:
                cuenta_analiticas_list.append(elem.analytic_account_id.name)

            try:
                y = posicion_presupuestaria_list.index(elem.general_budget_id.name)
            except:
                posicion_presupuestaria_list.append(elem.general_budget_id.name)

        tamanios = [60,90,51,51,51,51,51,51,51,51,51,51,51,51,51]
        titulos_cab = ['C. COSTO','CONCEPTO','ENE','FEB','MAR','ABR','MAY','JUN','JUL','AGO','SEP','OCT','NOV','DIC','TOTAL']
        
        
        c.setFont("Calibri-Bold", 7)
        c.drawString( 10 ,pos_inicial, u'DESVIACIONES' )

        pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,15,pagina)

        fondo = HexColor('#d3eaf1')
        c.setFillColor(fondo)
        c.rect(10,pos_inicial-3,813,10, fill=True,stroke=False)
        c.setFillColor(colors.black)
 
        recorredor_t = 0
        acum_titulo = 10
        for i_titulo in titulos_cab:
            c.drawString( acum_titulo , pos_inicial, i_titulo )

            acum_titulo+= tamanios[recorredor_t]
            recorredor_t +=1


        pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,10,pagina)


        for c_a_l in cuenta_analiticas_list:

            totales = [0,0,0,0,0,0,0,0,0,0,0,0,0]
            for p_p_l in posicion_presupuestaria_list:
                contador_acum = 0
                objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id)])
                if objetosrecorrer and len(objetosrecorrer)>0:

                    c.setFont("Calibri", 7)
                    c.drawString( 10 ,pos_inicial, c_a_l )
                    c.drawString( 70 , pos_inicial, p_p_l )

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','01/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 209 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% objetosrecorrer[0].desviacion )))
                        contador_acum += objetosrecorrer[0].desviacion
                        totales[0] = objetosrecorrer[0].desviacion

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','02/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 260 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% objetosrecorrer[0].desviacion )))
                        contador_acum += objetosrecorrer[0].desviacion
                        totales[1] = objetosrecorrer[0].desviacion

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','03/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 311 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% objetosrecorrer[0].desviacion )))
                        contador_acum += objetosrecorrer[0].desviacion
                        totales[2] = objetosrecorrer[0].desviacion

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','04/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 362 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% objetosrecorrer[0].desviacion )))
                        contador_acum += objetosrecorrer[0].desviacion
                        totales[3] = objetosrecorrer[0].desviacion

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','05/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 413 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% objetosrecorrer[0].desviacion )))
                        contador_acum += objetosrecorrer[0].desviacion
                        totales[4] = objetosrecorrer[0].desviacion

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','06/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 464 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% objetosrecorrer[0].desviacion )))
                        contador_acum += objetosrecorrer[0].desviacion
                        totales[5] = objetosrecorrer[0].desviacion

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','07/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 515 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% objetosrecorrer[0].desviacion )))
                        contador_acum += objetosrecorrer[0].desviacion
                        totales[6] = objetosrecorrer[0].desviacion

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','08/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 566 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% objetosrecorrer[0].desviacion )))
                        contador_acum += objetosrecorrer[0].desviacion
                        totales[7] = objetosrecorrer[0].desviacion

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','09/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 617 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% objetosrecorrer[0].desviacion )))
                        contador_acum += objetosrecorrer[0].desviacion
                        totales[8] = objetosrecorrer[0].desviacion

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','10/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 668 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% objetosrecorrer[0].desviacion )))
                        contador_acum += objetosrecorrer[0].desviacion
                        totales[9] = objetosrecorrer[0].desviacion

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','11/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 719 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% objetosrecorrer[0].desviacion )))
                        contador_acum += objetosrecorrer[0].desviacion
                        totales[10] = objetosrecorrer[0].desviacion

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','12/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 770 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% objetosrecorrer[0].desviacion )))
                        contador_acum += objetosrecorrer[0].desviacion
                        totales[11] = objetosrecorrer[0].desviacion

                    c.drawRightString( 821 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% contador_acum )))
                    totales[12] = contador_acum


                    pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,10,pagina)


            c.setFont("Calibri-Bold", 7)
            c.line(158,pos_inicial+7, 823,pos_inicial+7)
            c.line(158,pos_inicial-2, 823,pos_inicial-2)
            c.line(158,pos_inicial-4, 823,pos_inicial-4)
            c.drawRightString( 209 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[0] )))
            c.drawRightString( 260 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[1] )))
            c.drawRightString( 311 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[2] )))
            c.drawRightString( 362 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[3] )))
            c.drawRightString( 413 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[4] )))
            c.drawRightString( 464 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[5] )))
            c.drawRightString( 515 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[6] )))
            c.drawRightString( 566 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[7] )))
            c.drawRightString( 617 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[8] )))
            c.drawRightString( 668 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[9] )))
            c.drawRightString( 719 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[10] )))
            c.drawRightString( 770 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[11] )))
            c.drawRightString( 821 , pos_inicial, '{:,.2f}'.format(decimal.Decimal ("%0.2f"% totales[12] )))

            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)

        c.showPage()


            ############################


        inicio = 0
        pos_inicial = hReal-28
        libro = None
        voucher = None
        total = 0
        debeTotal = 0
        haberTotal = 0
        pagina = 1
        textPos = 0
        
        self.cabezera(c,wReal,hReal)

        objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id)])

        cuenta_analiticas_list = []
        posicion_presupuestaria_list = []

        for elem in objetosrecorrer:
            try:
                x = cuenta_analiticas_list.index(elem.analytic_account_id.name)
            except:
                cuenta_analiticas_list.append(elem.analytic_account_id.name)

            try:
                y = posicion_presupuestaria_list.index(elem.general_budget_id.name)
            except:
                posicion_presupuestaria_list.append(elem.general_budget_id.name)

        tamanios = [60,90,51,51,51,51,51,51,51,51,51,51,51,51,51]
        titulos_cab = ['C. COSTO','CONCEPTO','ENE','FEB','MAR','ABR','MAY','JUN','JUL','AGO','SEP','OCT','NOV','DIC','TOTAL']
        
        
        c.setFont("Calibri-Bold", 7)
        c.drawString( 10 ,pos_inicial, u'Porcentaje Desviaciones' )

        pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,15,pagina)

        fondo = HexColor('#d3eaf1')
        c.setFillColor(fondo)
        c.rect(10,pos_inicial-3,813,10, fill=True,stroke=False)
        c.setFillColor(colors.black)
 
        recorredor_t = 0
        acum_titulo = 10
        for i_titulo in titulos_cab:
            c.drawString( acum_titulo , pos_inicial, i_titulo )

            acum_titulo+= tamanios[recorredor_t]
            recorredor_t +=1


        pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,10,pagina)


        for c_a_l in cuenta_analiticas_list:

            totales = [0,0,0,0,0,0,0,0,0,0,0,0,0]
            for p_p_l in posicion_presupuestaria_list:
                contador_acum = 0
                objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id)])
                if objetosrecorrer and len(objetosrecorrer)>0:

                    c.setFont("Calibri", 7)
                    c.drawString( 10 ,pos_inicial, c_a_l )
                    c.drawString( 70 , pos_inicial, p_p_l )

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','01/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 209 , pos_inicial, ("%0.2f"% objetosrecorrer[0].porcentaje_real_decimal) + " %" )
                        contador_acum += objetosrecorrer[0].porcentaje_real_decimal
                        totales[0] = objetosrecorrer[0].porcentaje_real_decimal

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','02/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 260 , pos_inicial, ("%0.2f"% objetosrecorrer[0].porcentaje_real_decimal) + " %" )
                        contador_acum += objetosrecorrer[0].porcentaje_real_decimal
                        totales[1] = objetosrecorrer[0].porcentaje_real_decimal

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','03/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 311 , pos_inicial, ("%0.2f"% objetosrecorrer[0].porcentaje_real_decimal) + " %" )
                        contador_acum += objetosrecorrer[0].porcentaje_real_decimal
                        totales[2] = objetosrecorrer[0].porcentaje_real_decimal

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','04/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 362 , pos_inicial, ("%0.2f"% objetosrecorrer[0].porcentaje_real_decimal) + " %" )
                        contador_acum += objetosrecorrer[0].porcentaje_real_decimal
                        totales[3] = objetosrecorrer[0].porcentaje_real_decimal

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','05/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 413 , pos_inicial, ("%0.2f"% objetosrecorrer[0].porcentaje_real_decimal) + " %" )
                        contador_acum += objetosrecorrer[0].porcentaje_real_decimal
                        totales[4] = objetosrecorrer[0].porcentaje_real_decimal

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','06/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 464 , pos_inicial, ("%0.2f"% objetosrecorrer[0].porcentaje_real_decimal) + " %" )
                        contador_acum += objetosrecorrer[0].porcentaje_real_decimal
                        totales[5] = objetosrecorrer[0].porcentaje_real_decimal

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','07/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 515 , pos_inicial, ("%0.2f"% objetosrecorrer[0].porcentaje_real_decimal) + " %" )
                        contador_acum += objetosrecorrer[0].porcentaje_real_decimal
                        totales[6] = objetosrecorrer[0].porcentaje_real_decimal

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','08/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 566 , pos_inicial, ("%0.2f"% objetosrecorrer[0].porcentaje_real_decimal) + " %" )
                        contador_acum += objetosrecorrer[0].porcentaje_real_decimal
                        totales[7] = objetosrecorrer[0].porcentaje_real_decimal

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','09/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 617 , pos_inicial, ("%0.2f"% objetosrecorrer[0].porcentaje_real_decimal) + " %" )
                        contador_acum += objetosrecorrer[0].porcentaje_real_decimal
                        totales[8] = objetosrecorrer[0].porcentaje_real_decimal

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','10/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 668 , pos_inicial, ("%0.2f"% objetosrecorrer[0].porcentaje_real_decimal) + " %" )
                        contador_acum += objetosrecorrer[0].porcentaje_real_decimal
                        totales[9] = objetosrecorrer[0].porcentaje_real_decimal

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','11/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 719 , pos_inicial, ("%0.2f"% objetosrecorrer[0].porcentaje_real_decimal) + " %" )
                        contador_acum += objetosrecorrer[0].porcentaje_real_decimal
                        totales[10] = objetosrecorrer[0].porcentaje_real_decimal

                    objetosrecorrer = self.env['crossovered.budget.lines'].search([('crossovered_budget_id.period_id.fiscalyear_id','=',self.fiscalyear_id.id),('analytic_account_id.name','=',c_a_l),('general_budget_id.name','=',p_p_l),('crossovered_budget_id.period_id.code','=','12/'+ self.fiscalyear_id.name)])
                    if objetosrecorrer and len(objetosrecorrer)>0 and objetosrecorrer[0].id:
                        c.drawRightString( 770 , pos_inicial, ("%0.2f"% objetosrecorrer[0].porcentaje_real_decimal) + " %" )
                        contador_acum += objetosrecorrer[0].porcentaje_real_decimal
                        totales[11] = objetosrecorrer[0].porcentaje_real_decimal

                    c.drawRightString( 821 , pos_inicial, ("%0.2f"% contador_acum) + " %" )
                    totales[12] = contador_acum


                    pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,10,pagina)


            c.setFont("Calibri-Bold", 7)
            c.line(158,pos_inicial+7, 823,pos_inicial+7)
            c.line(158,pos_inicial-2, 823,pos_inicial-2)
            c.line(158,pos_inicial-4, 823,pos_inicial-4)
            c.drawRightString( 209 , pos_inicial, ("%0.2f"% totales[0]) + " %")
            c.drawRightString( 260 , pos_inicial, ("%0.2f"% totales[1]) + " %")
            c.drawRightString( 311 , pos_inicial, ("%0.2f"% totales[2]) + " %")
            c.drawRightString( 362 , pos_inicial, ("%0.2f"% totales[3]) + " %")
            c.drawRightString( 413 , pos_inicial, ("%0.2f"% totales[4]) + " %")
            c.drawRightString( 464 , pos_inicial, ("%0.2f"% totales[5]) + " %")
            c.drawRightString( 515 , pos_inicial, ("%0.2f"% totales[6]) + " %")
            c.drawRightString( 566 , pos_inicial, ("%0.2f"% totales[7]) + " %")
            c.drawRightString( 617 , pos_inicial, ("%0.2f"% totales[8]) + " %")
            c.drawRightString( 668 , pos_inicial, ("%0.2f"% totales[9]) + " %")
            c.drawRightString( 719 , pos_inicial, ("%0.2f"% totales[10]) + " %")
            c.drawRightString( 770 , pos_inicial, ("%0.2f"% totales[11]) + " %")
            c.drawRightString( 821 , pos_inicial, ("%0.2f"% totales[12]) + " %")

            pagina, pos_inicial = self.verify_linea(c,wReal,hReal,pos_inicial,24,pagina)
        c.save()


    @api.multi
    def particionar_text(self,c,tam):
        tet = ""
        for i in range(len(c)):
            tet += c[i]
            lines = simpleSplit(tet,'Calibri',7,tam)
            if len(lines)>1:
                return tet[:-1]
        return tet

    @api.multi
    def verify_linea(self,c,wReal,hReal,posactual,valor,pagina):
        if posactual <40:
            c.showPage()
            self.cabezera(c,wReal,hReal)

            c.setFont("Calibri-Bold", 7)
            #c.drawCentredString(300,25,'Pág. ' + str(pagina+1))
            return pagina+1,hReal-40
        else:
            return pagina,posactual-valor








import time
from openerp.osv import fields, osv


class account_budget_crossvered_summary_report_it(osv.osv_memory):
    """
    This wizard provides the crossovered budget summary report'
    """
    _name = 'account.budget.crossvered.summary.report.it'
    _description = 'Account Budget  crossvered summary report'
    _columns = {
        'date_from': fields.date('Inicio de periodo', required=True),
        'date_to': fields.date('Fin de periodo', required=True),
    }
    _defaults = {
        'date_from': lambda *a: time.strftime('%Y-01-01'),
        'date_to': lambda *a: time.strftime('%Y-%m-%d'),
    }

    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = self.read(cr, uid, ids, context=context)[0]
        datas = {
            'ids': context.get('active_ids',[]),
            'model': 'crossovered.budget',
            'form': data
        }
        datas['form']['ids'] = datas['ids']
        datas['form']['report'] = 'analytic-one'
        return self.pool['report'].get_action(cr, uid, [], 'smile_account_budget_commitment.report_crossoveredbudget_it', data=datas, context=context)




class account_budget_crossvered_report_it(osv.osv_memory):

    _name = "account.budget.crossvered.report.it"
    _description = "Account Budget crossvered report"
    _columns = {
        'date_from': fields.date('Inicio de periodo', required=True),
        'date_to': fields.date('Fin de periodo', required=True),
    }
    _defaults = {
        'date_from': lambda *a: time.strftime('%Y-01-01'),
        'date_to': lambda *a: time.strftime('%Y-%m-%d'),
    }

    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = self.read(cr, uid, ids, context=context)[0]
        datas = {
            'ids': context.get('active_ids', []),
            'model': 'crossovered.budget',
            'form': data
        }
        datas['form']['ids'] = datas['ids']
        datas['form']['report'] = 'analytic-full'
        return self.pool['report'].get_action(cr, uid, [], 'smile_account_budget_commitment.report_crossoveredbudget_it', data=datas, context=context)




import time
from openerp.osv import osv
from openerp.report import report_sxw


class budget_report_it(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(budget_report_it, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'funct': self.funct,
            'funct_total': self.funct_total,
            'time': time,
        })
        self.context = context

    def funct(self, object, form, ids=None, done=None, level=1):
        if ids is None:
            ids = {}
        if not ids:
            ids = self.ids
        if not done:
            done = {}
        global tot
        tot = {
            'theo':0.00,
            'pln':0.00,
            'prac':0.00,
            'perc':0.00
        }
        result = []

        budgets = self.pool.get('crossovered.budget').browse(self.cr, self.uid, [object.id], self.context.copy())
        c_b_lines_obj = self.pool.get('crossovered.budget.lines')
        acc_analytic_obj = self.pool.get('account.analytic.account')
        for budget_id in budgets:
            res = {}
            budget_lines = []
            budget_ids = []
            d_from = form['date_from']
            d_to = form['date_to']

            for line in budget_id.crossovered_budget_line:
                budget_ids.append(line.id)

            if not budget_ids:
                return []

            self.cr.execute('SELECT DISTINCT(analytic_account_id) FROM crossovered_budget_lines WHERE id = ANY(%s)',(budget_ids,))
            an_ids = self.cr.fetchall()

            context = {'wizard_date_from': d_from, 'wizard_date_to': d_to}
            for i in range(0, len(an_ids)):
                if not an_ids[i][0]:
                    continue
                analytic_name = acc_analytic_obj.browse(self.cr, self.uid, [an_ids[i][0]])
                res={
                    'b_id': '-1',
                    'a_id': '-1',
                    'name': analytic_name[0].name,
                    'status': 1,
                    'theo': 0.00,
                    'pln': 0.00,
                    'prac': 0.00,
                    'perc': 0.00
                }
                result.append(res)

                line_ids = c_b_lines_obj.search(self.cr, self.uid, [('id', 'in', budget_ids), ('analytic_account_id','=',an_ids[i][0]), ('date_to', '>=', d_from), ('date_from', '<=', d_to)])
                line_id = c_b_lines_obj.browse(self.cr, self.uid, line_ids)
                tot_theo = tot_pln = tot_prac = tot_perc = 0.00

                done_budget = []
                for line in line_id:
                    if line.id in budget_ids:
                        theo = pract = 0.00
                        theo = c_b_lines_obj._theo_amt(self.cr, self.uid, [line.id], context)[line.id]
                        pract = c_b_lines_obj._prac_amt(self.cr, self.uid, [line.id], context)[line.id]
                        if line.general_budget_id.id in done_budget:
                            for record in result:
                                if record['b_id'] == line.general_budget_id.id  and record['a_id'] == line.analytic_account_id.id:
                                    record['theo'] += line.planned_amount
                                    record['pln'] += line.importe_real
                                    record['prac'] += line.desviacion

                                    if record['theo'] == 0:
                                        record['perc'] = 0
                                    else:
                                        record['perc'] = ((record['pln'] / record['theo'])*100)
                                    tot_theo += line.planned_amount
                                    tot_pln += line.importe_real
                                    tot_prac += line.desviacion
                                    tot_perc += record['perc']
                                    print "record",record
                        else:
                            res1 = {
                                    'a_id': line.analytic_account_id.id,
                                    'b_id': line.general_budget_id.id,
                                    'name': line.general_budget_id.name,
                                    'status': 2,
                                    'theo': line.planned_amount,
                                    'pln': line.importe_real,
                                    'prac': line.desviacion,
                                    'perc': line.porcentaje_real_decimal,
                            }

                            tot_theo += line.planned_amount
                            tot_pln += line.importe_real
                            tot_prac += line.desviacion
                            tot_perc += line.porcentaje_real_decimal
                            if form['report'] == 'analytic-full':

                                result.append(res1)
                                done_budget.append(line.general_budget_id.id)
                    else:

                        if line.general_budget_id.id in done_budget:
                            continue
                        else:
                            res1={
                                    'a_id': line.analytic_account_id.id,
                                    'b_id': line.general_budget_id.id,
                                    'name': line.general_budget_id.name,
                                    'status': 2,
                                    'theo': 0.00,
                                    'pln': 0.00,
                                    'prac': 0.00,
                                    'perc': 0.00
                            }
                            

                            if form['report'] == 'analytic-full':
                                result.append(res1)
                                done_budget.append(line.general_budget_id.id)


                if tot_theo == 0.00:
                    tot_perc = 0.00
                else:
                    tot_perc = float(tot_pln / tot_theo) * 100
                if form['report'] == 'analytic-full':
                    result[-(len(done_budget) +1)]['theo'] = tot_theo
                    tot['theo'] += tot_theo
                    result[-(len(done_budget) +1)]['pln'] = tot_pln
                    tot['pln'] += tot_pln
                    result[-(len(done_budget) +1)]['prac'] = tot_prac
                    tot['prac'] += tot_prac
                    result[-(len(done_budget) +1)]['perc'] = tot_perc
                else:
                    result[-1]['theo'] = tot_theo
                    tot['theo'] += tot_theo
                    result[-1]['pln'] = tot_pln
                    tot['pln'] += tot_pln
                    result[-1]['prac'] = tot_prac
                    tot['prac'] += tot_prac
                    result[-1]['perc'] = tot_perc
                print result
            if tot['theo'] == 0.00:
                tot['perc'] = 0.00
            else:
                tot['perc'] = float(tot['pln'] / tot['theo']) * 100

        return result

    def funct_total(self, form):
        result = []
        res = {}
        res = {
             'tot_theo': tot['theo'],
             'tot_pln': tot['pln'],
             'tot_prac': tot['prac'],
             'tot_perc': tot['perc']
        }
        result.append(res)
        return result


class report_crossoveredbudget_it(osv.AbstractModel):
    _name = 'report.smile_account_budget_commitment.report_crossoveredbudget_it'
    _inherit = 'report.abstract_report'
    _template = 'smile_account_budget_commitment.report_crossoveredbudget_it'
    _wrapped_report_class = budget_report_it
