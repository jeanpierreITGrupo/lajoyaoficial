# -*- coding: utf-8 -*-
{
    'name'    : "Envío de correo en licitaciones mensuales",
    'author'  : "ITGrupo",
    'category': 'purchase',
    'version' : '0.1',

    'description': """
        Módulo que agrega el enviar un correo a una dirección al momento de crear una licitación mensual.
    """,

    'auto_install': False,
    'installable' : True,
    'depends'     : ['licitacion_advance_it'],
    'data'        : ['reporte_flujo_cajacuenta_view.xml'],
}