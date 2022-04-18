# -*- encoding: utf-8 -*-
{
	'name': 'Stock Picking Motive',
	'category': 'sale',
	'author': 'ITGrupo',
	'depends': [
		'sale_stock',
     ],
	'version': '1.0',
	'description':"""A. Formulario Pedido/Presupuesto de venta:

    En la parte inferior luego de Método de envío:

        Añadir sección: "Datos impresión"
            Añadir campos a la izquierda:
                "Serie Guía remision", combo para seleccionar diario de stock. Campo mandatorio.
                "Guía núm. siguiente", texto solo lectura que muestra el numero siguiente de la secuencia de dicho diario (prefijo y rellenado). Fuente negrita y grande.
                "Transportista", combo para seleccionar el carrier a asignar para la creacion de la guia de remision. Mandatorio.
                "Motivo de traslado", combo para seleccionar motivo de traslado. Mandatorio.
            Añadir campo a la derecha:
                "Factura núm. siguiente" texto solo lectura que muestra el numero siguiente del diario de comprobante utilizado (prefijo y rellenado). Fuente negrita y grande.
    En la barra superior añadir boton "Imprimir Guia". Debe aparecer luego de confirmar pedido.

B. Al confirmar venta la guia de remision:

    Debe forzar disponibilidad.
    Debe enviar los productos automaticamente.""",
	'auto_install': False,
	'demo': [],
	'data':['stock_picking_view.xml'],
	#'data':[],
	'css': ['static/src/css/style.css'],
	'installable': True
}
