# -*- coding: utf-8 -*-
{
    'name': "Recursos Humanos",

    'description': """
        Módulo que gestiona Recursos Humanos
    """,

    'author': "ITGrupo",
    'category': 'managment',
    'version': '0.1',
    'depends': ['hr_employee', 'account_contable_book_it','account','account_invoice_distrib_gastos_it'],
    'data': ['hr_parameters_view.xml',
             'hr_tareo_parameters_view.xml',
             'hr_horas_extra_view.xml',
             'hr_table_membership_view.xml',
             'hr_cuentas_analiticas_view.xml',
             'hr_membership_view.xml',
             'hr_nomina_view.xml',
             'wizard/hr_nomina_wizard.xml',
             'wizard/add_worker_tareo_view.xml',
             'hr_tareo_view.xml',
             'hr_planilla_view.xml',
             'hr_concepto_remunerativo_view.xml',
             'hr_table_adelanto_view.xml',
             'hr_adelanto_view.xml',
             'human_resources.xml',
             'hr_distribucion_gasto_view.xml',
             'hr_certificado_medico_view.xml',
             'wizard/hr_export_employee_view.xml',
             'wizard/boleta_empleado_wizard_view.xml',
             'res_company_view.xml'],
}