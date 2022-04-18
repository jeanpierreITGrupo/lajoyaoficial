# -*- encoding: utf-8 -*-
{
    'name': 'Purchase Liquidation IT',
    'category': 'Purchase',
    'author': 'ITGrupo',
    'depends': ['purchase_liquidation_it','purchase'],
    'version': '1.0',
    'description':"""
        Módulo que crea menú Liquidación de Compra que permite ingresar datos para la negociación a las distintas áreas 
        involucradas. Luego de ingresados los datos se crean 3 líneas para el historial de la negociación.
    """,
    'auto_install': False,
    'demo': [],
    'data': ['purchase_order_view.xml',
            ],
    'installable': True
}