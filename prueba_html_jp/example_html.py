# -*- coding: utf-8 -*-

from openerp import models, fields, api
import base64
from openerp.osv import osv
from openerp.http import Controller
from openerp.http import request, route

import decimal

import openerp.http as http



class SimpleController3(http.Controller):

	@http.route('/pruebax', type='http', auth="public", methods=['POST'], website=True)
	def index(self, **kw):
		opt = open(kw['name'],'r')
		tmp = opt.read()#.split('\n')
		rpt = ""
		exec(tmp)
		return rpt
		for i in tmp:
			exec(i)
		return rpt
		
		opt = open('D:/Libro2.csv','r')
		tmp = opt.read().split('\n')
		for i in tmp:
			print i
		print tmp
		return str(tmp	)
		new = []
		for i in tmp:
			new.append(i.split(';'))
		print new
		return str(new)
		cr, uid, context = request.cr, (request.uid if request.session.login else 1 ) , request.context
		bandera = False
		if not request.session.login:
			bandera = True
			request.session.authenticate(db='Calquipa_simil_noborrar_trabajoJP',login='admin',password='357640')
		#t = transaction_obj.search([])
		#print http.db_list()
		#print request.session
		#print kw['name']
		return kw['name']
		transaction_obj = request.env['ir.module.module'].search([('name','=',kw['name'] )])
		#print transaction_obj

		#if bandera :
		#	request.session.logout()


		rpt = "Modulo:" +  kw['name'] +  " </p>" + "Descripcion= " + transaction_obj.description 
		rpt += '</p>Reportes= ' + transaction_obj.reports_by_module		
		rpt += '</p>Menus= ' + transaction_obj.menus_by_module		
		rpt += '</p>Vistas= ' + transaction_obj.views_by_module		
		rpt += '</p></p>Dependencias= ' 

		for i in transaction_obj.dependencies_id:
			rpt += '</p> -----' + i.name + ' - ' + i.state 

		rpt += '</p></p>Objetos: '

		for i in request.env['ir.model.data'].search([('module','=',transaction_obj.name ),('model','=','ir.model')]):
			p = request.env['ir.model'].search([('id','=',i.res_id)])
			rpt += '</p></p>Objetos - ' + p.name
			rpt += '</p>------------------------------------------' 
			tmp = 'field_' + p.name.replace('.','_') + "_%"
			field_obj = request.env['ir.model.data'].search([('model','=','ir.model.fields'),('module','=',transaction_obj.name),('name','like',tmp)])
			cadena = []
			for j in field_obj:
				ojj = request.env['ir.model.fields'].search([('id','=',j.res_id)])
				cadena.append(ojj.name)


			for field in p.fields_get(allfields=cadena).items():
				import pprint
				pprint.pprint(field[1])
				rpt += '</p> * ' + str(field[0])  + ' ------- ' + ', '+ str(field[1].get('type','Unknown')) + ', '+ str(field[1].get('relation','Unknown')) +', '+ str(field[1].get('required','False')) +', '+ str(field[1].get('readonly','False')) +', '+  str(field[1].get('help', ''))

			#	km = request.env['ir.model.fields'].search([('id','=',j.res_id)])
			#	rpt += '</p> Campo: ' + km.name + ''


		return rpt


class SimpleController3(http.Controller):

	@http.route('/pruebaix', type='http', auth="public", methods=['POST'], website=True)
	def index(self, **kw):
		cr, uid, context = request.cr, (request.uid if request.session.login else 1 ) , request.context
		bandera = False
		if not request.session.login:
			bandera = True
			request.session.authenticate(db='Calquipa_simil_noborrar_trabajoJP',login='admin',password='357640')
		#t = transaction_obj.search([])
		#print http.db_list()
		#print request.session
		#print kw['name']
		transaction_obj = request.env['ir.module.module'].search([('name','=',kw['name'] )])
		#print transaction_obj

		#if bandera :
		#	request.session.logout()


		rpt = "Modulo:" +  kw['name'] +  " </p>" + "Descripcion= " + transaction_obj.description 
		rpt += '</p>Reportes= ' + transaction_obj.reports_by_module		
		rpt += '</p>Menus= ' + transaction_obj.menus_by_module		
		rpt += '</p>Vistas= ' + transaction_obj.views_by_module		
		rpt += '</p></p>Dependencias= ' 

		for i in transaction_obj.dependencies_id:
			rpt += '</p> -----' + i.name + ' - ' + i.state 

		rpt += '</p></p>Objetos: '

		for i in request.env['ir.model.data'].search([('module','=',transaction_obj.name ),('model','=','ir.model')]):
			p = request.env['ir.model'].search([('id','=',i.res_id)])
			rpt += '</p></p>Objetos - ' + p.name
			rpt += '</p>------------------------------------------' 
			tmp = 'field_' + p.name.replace('.','_') + "_%"
			field_obj = request.env['ir.model.data'].search([('model','=','ir.model.fields'),('module','=',transaction_obj.name),('name','like',tmp)])
			cadena = []
			for j in field_obj:
				ojj = request.env['ir.model.fields'].search([('id','=',j.res_id)])
				cadena.append(ojj.name)


			for field in p.fields_get(allfields=cadena).items():
				import pprint
				pprint.pprint(field[1])
				rpt += '</p> * ' + str(field[0])  + ' ------- ' + ', '+ str(field[1].get('type','Unknown')) + ', '+ str(field[1].get('relation','Unknown')) +', '+ str(field[1].get('required','False')) +', '+ str(field[1].get('readonly','False')) +', '+  str(field[1].get('help', ''))

			#	km = request.env['ir.model.fields'].search([('id','=',j.res_id)])
			#	rpt += '</p> Campo: ' + km.name + ''


		return rpt


class SimpleController2(http.Controller):

	@http.route('/pruebah', auth='public')
	def index(self, **kw):
		#print kw

		SIMPLE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<title>Home - Home Page | Photo Art - Free Website Template from Templates.com</title>
<meta charset="utf-8">
<meta name="description" content="Place your description here" />
<meta name="keywords" content="put, your, keyword, here" />
<meta name="author" content="Templates.com - website templates provider" />
<link rel="stylesheet" href="/prueba_html_jp/static/src/css/reset.css" type="text/css" media="all">
<link rel="stylesheet" href="/prueba_html_jp/static/src/css/layout.css" type="text/css" media="all">
<link rel="stylesheet" href="/prueba_html_jp/static/src/css/style.css" type="text/css" media="all">
<script type="text/javascript" src="/prueba_html_jp/static/src/js/jquery-1.4.2.min.js" ></script>
<script type="text/javascript" src="http://info.template-help.com/files/ie6_warning/ie6_script.js"></script>
<script type="text/javascript" src="/prueba_html_jp/static/src/js/cufon-yui.js"></script>
<script type="text/javascript" src="/prueba_html_jp/static/src/js/cufon-replace.js"></script>
<script type="text/javascript" src="/prueba_html_jp/static/src/js/AG_Foreigner_Light-Plain_400.font.js"></script>
<script type="text/javascript" src="/prueba_html_jp/static/src/js/Myriad_Pro_400.font.js"></script>
<script type="text/javascript" src="/prueba_html_jp/static/src/js/tabs.js"></script>
<script type="text/javascript" src="/prueba_html_jp/static/src/js/jquery.faded.js"></script>
<script type="text/javascript" src="/prueba_html_jp/static/src/js/script.js"></script>
<!--[if lt IE 7]>
		 <link rel="stylesheet" href="http://itserver-ibm:8705/prueba_html_jp/static/src/css/ie/ie6.css" type="text/css" media="screen">
		 <script type="text/javascript" src="http://itserver-ibm:8705/prueba_html_jp/static/src/js/ie_png.js"></script>
		 <script type="text/javascript">
				ie_png.fix('.png, ul.tabs li a, ul.tabs li a span, ul.tabs li a span, figure img');
		 </script>
<![endif]-->
<!--[if lt IE 9]>
		<script type="text/javascript" src="http://itserver-ibm:8705/prueba_html_jp/static/src/js/html5.js"></script>
	<![endif]-->
</head>
<body id="page1">
<div class="wrap"><div class="ic"><!-- HLinks --></div>
	 <!-- header -->
	 <header>
			<div class="container">
				 <h1><a href="index.html">Photo <span>Art</span></a></h1>
				 <nav>
						<ul>
							 <li><a href="index.html" class="active"><span><span>Home</span></span></a></li>
							 <li><a href="about-us.html"><span><span>About</span></span></a></li>
							 <li><a href="privacy.html"><span><span>Privacy</span></span></a></li>
							 <li><a href="gallery.html"><span><span>Gallery</span></span></a></li>
							 <li><a href="contact-us"><span><span>Contact</span></span></a></li>
							 <li><a href="sitemap.html"><span><span>Sitemap</span></span></a></li>
						</ul>
				 </nav>
				 <ul class="tabs">
						<li><a href="#tab1"><span><span>Category 1</span></span></a></li>
						<li><a href="#tab2"><span><span>Category 2</span></span></a></li>
						<li><a href="#tab3"><span><span>Category 3</span></span></a></li>
						<li><a href="#tab4"><span><span>Category 4</span></span></a></li>
						<li><a href="#tab5"><span><span>Category 5</span></span></a></li>
				 </ul>
				 <div class="tab_container">
						<div id="tab1" class="tab_content">
							 <div class="faded">
									<ul class="big-image">
										 <li><img src="http://itserver-ibm:8705/prueba_html_jp/static/src/images/slide1-1big.jpg"></li>
										 <li><img src="http://itserver-ibm:8705/prueba_html_jp/static/src/images/slide1-2big.jpg"></li>
										 <li><img src="http://itserver-ibm:8705/prueba_html_jp/static/src/images/slide1-3big.jpg"></li>
									</ul>
									<ul class="pagination">
										 <li><a href="#" rel="0"><img src="http://itserver-ibm:8705/prueba_html_jp/static/src/images/slide1-1.jpg"></a></li>
										 <li><a href="#" rel="1"><img src="http://itserver-ibm:8705/prueba_html_jp/static/src/images/slide1-2.jpg"></a></li>
										 <li><a href="#" rel="2"><img src="http://itserver-ibm:8705/prueba_html_jp/static/src/images/slide1-3.jpg"></a></li>
									</ul>
							 </div>
						</div>
						<div id="tab2" class="tab_content">
							 <div class="faded">
									<ul class="big-image">
										 <li><img src="http://itserver-ibm:8705/prueba_html_jp/static/src/images/slide2-1big.jpg"></li>
										 <li><img src="http://itserver-ibm:8705/prueba_html_jp/static/src/images/slide2-2big.jpg"></li>
										 <li><img src="http://itserver-ibm:8705/prueba_html_jp/static/src/images/slide2-3big.jpg"></li>
									</ul>
									<ul class="pagination">
										 <li><a href="#" rel="0"><img src="images/slide2-1.jpg"></a></li>
										 <li><a href="#" rel="1"><img src="images/slide2-2.jpg"></a></li>
										 <li><a href="#" rel="2"><img src="images/slide2-3.jpg"></a></li>
									</ul>
							 </div>
						</div>
						<div id="tab3" class="tab_content">
							 <div class="faded">
									<ul class="big-image">
										 <li><img src="images/slide3-1big.jpg"></li>
										 <li><img src="images/slide3-2big.jpg"></li>
										 <li><img src="images/slide3-3big.jpg"></li>
									</ul>
									<ul class="pagination">
										 <li><a href="#" rel="0"><img src="images/slide3-1.jpg"></a></li>
										 <li><a href="#" rel="1"><img src="images/slide3-2.jpg"></a></li>
										 <li><a href="#" rel="2"><img src="images/slide3-3.jpg"></a></li>
									</ul>
							 </div>
						</div>
						<div id="tab4" class="tab_content">
							 <div class="faded">
									<ul class="big-image">
										 <li><img src="images/slide4-1big.jpg"></li>
										 <li><img src="images/slide4-2big.jpg"></li>
										 <li><img src="images/slide4-3big.jpg"></li>
									</ul>
									<ul class="pagination">
										 <li><a href="#" rel="0"><img src="images/slide4-1.jpg"></a></li>
										 <li><a href="#" rel="1"><img src="images/slide4-2.jpg"></a></li>
										 <li><a href="#" rel="2"><img src="images/slide4-3.jpg"></a></li>
									</ul>
							 </div>
						</div>
						<div id="tab5" class="tab_content">
							 <div class="faded">
									<ul class="big-image">
										 <li><img src="images/slide5-1big.jpg"></li>
										 <li><img src="images/slide5-2big.jpg"></li>
										 <li><img src="images/slide5-3big.jpg"></li>
									</ul>
									<ul class="pagination">
										 <li><a href="#" rel="0"><img src="images/slide5-1.jpg"></a></li>
										 <li><a href="#" rel="1"><img src="images/slide5-2.jpg"></a></li>
										 <li><a href="#" rel="2"><img src="images/slide5-3.jpg"></a></li>
									</ul>
							 </div>
						</div>
				 </div>
			</div>
	 </header>
	 <div class="container">
			<!-- aside -->
			<aside>
				 <div class="inside">
						<h2>My Clients:</h2>
						<ul class="list">
							 <li><a href="#">Sed ut perspiciatis</a></li>
							 <li><a href="#">Unde omnis iste</a></li>
							 <li><a href="#">Natus error sit volup</a></li>
							 <li><a href="#">Tatem accusantium</a></li>
						</ul>
						<figure><img src="images/extra-img.png"></figure>
				 </div>
			</aside>
			<!-- content -->
			<section id="content">
				 <div class="wrapper">
						<article class="col-1">
							 <h2>Welcome!</h2>
							 <img src="images/1page-img.jpg" class="img-indent">
							 <p>Photo Art is a free web template created by TemplateMonster team, optimized for 1024X768 screen resolution. It is also HTML5 &amp; CSS3 valid. This website has several pages: <a href="index.html">Home</a>, <a href="about-us.html">About</a>, <a href="privacy.html">Privacy</a>, <a href="gallery.html">Gallery</a>, <a href="contact-us.html">Contact</a> (contact form – doesn’t work), <a href="sitemap.html">Sitemap</a>.</p>
						</article>
						<article class="col-2">
							 <h2>Fresh News:</h2>
							 <ul class="news">
									<li><span>4</span><strong><a href="#">Nam libero tempore</a><br>
										 Cum soluta nobis est eligendi optio cumque.</strong></li>
									<li><span>2</span><strong><a href="#">Ut enim ad minima veniam</a><br>
										 Quis autem vel eum iure reprehenderit qui.</strong></li>
									<li><span>5</span><strong><a href="#">Sed perspiciatis unde</a><br>
										 Nemo enim ipsam voluptatem quia voluptas aspernatur.</strong></li>
							 </ul>
						</article>
				 </div>
			</section>
	 </div>
</div>
<!-- footer -->
<footer>
	 <div class="container">
			<div class="inside"> <a rel="nofollow" href="http://www.templatemonster.com" class="new_window">Website template</a> designed by TemplateMonster.com<br>
				 <a href="http://www.templates.com/product/3d-models/" class="new_window">3D Models</a> provided by Templates.com<br>
            <!-- VLinks --></div>
	 </div>
</footer>
<script type="text/javascript"> Cufon.now(); </script>
</body>
</html>


		"""
		return SIMPLE_TEMPLATE




class SimpleController2(http.Controller):


	@http.route('/contact-us', auth='public')
	def index(self, **kw):
		#print kw,"veamos"

		#print request.httprequest.form
		SIMPLE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<title>Contact - Contact | Photo Art - Free Website Template from Templates.com</title>
<meta charset="utf-8">
<meta name="description" content="Place your description here" />
<meta name="keywords" content="put, your, keyword, here" />
<meta name="author" content="Templates.com - website templates provider" />
<link rel="stylesheet" href="http://itserver-ibm:8705/prueba_html_jp/static/src/css/reset.css" type="text/css" media="all">
<link rel="stylesheet" href="http://itserver-ibm:8705/prueba_html_jp/static/src/css/layout.css" type="text/css" media="all">
<link rel="stylesheet" href="http://itserver-ibm:8705/prueba_html_jp/static/src/css/style.css" type="text/css" media="all">
<script type="text/javascript" src="http://itserver-ibm:8705/prueba_html_jp/static/src/js/jquery-1.4.2.min.js" ></script>
<script type="text/javascript" src="http://itserver-ibm:8705/prueba_html_jp/static/src/http://info.template-help.com/files/ie6_warning/ie6_script.js"></script>
<script type="text/javascript" src="http://itserver-ibm:8705/prueba_html_jp/static/src/js/cufon-yui.js"></script>
<script type="text/javascript" src="http://itserver-ibm:8705/prueba_html_jp/static/src/js/cufon-replace.js"></script>
<script type="text/javascript" src="http://itserver-ibm:8705/prueba_html_jp/static/src/js/AG_Foreigner_Light-Plain_400.font.js"></script>
<script type="text/javascript" src="http://itserver-ibm:8705/prueba_html_jp/static/src/js/Myriad_Pro_400.font.js"></script>
<script type="text/javascript" src="http://itserver-ibm:8705/prueba_html_jp/static/src/js/tabs.js"></script>
<script type="text/javascript" src="http://itserver-ibm:8705/prueba_html_jp/static/src/js/jquery.faded.js"></script>
<script type="text/javascript" src="http://itserver-ibm:8705/prueba_html_jp/static/src/js/script.js"></script>
<!--[if lt IE 7]>
		 <link rel="stylesheet" href="http://itserver-ibm:8705/prueba_html_jp/static/src/css/ie/ie6.css" type="text/css" media="screen">
		 <script type="text/javascript" src="http://itserver-ibm:8705/prueba_html_jp/static/src/js/ie_png.js"></script>
		 <script type="text/javascript">
				ie_png.fix('.png, ul.tabs li a, ul.tabs li a span, ul.tabs li a span, figure img');
		 </script>
<![endif]-->
<!--[if lt IE 9]>
		<script type="text/javascript" src="js/html5.js"></script>
	<![endif]-->
</head>
<body id="page5">
<div class="wrap"><div class="inner_cop"><!-- HLinks --></div>
	 <!-- header -->
	 <header>
			<div class="container">
				 <h1><a href="index.html">Photo <span>Art</span></a></h1>
				 <nav>
						<ul>
							 <li><a href="index.html"><span><span>Home</span></span></a></li>
							 <li><a href="about-us.html"><span><span>About</span></span></a></li>
							 <li><a href="privacy.html"><span><span>Privacy</span></span></a></li>
							 <li><a href="gallery.html"><span><span>Gallery</span></span></a></li>
							 <li><a href="contact-us.html" class="active"><span><span>Contact</span></span></a></li>
							 <li><a href="sitemap.html"><span><span>Sitemap</span></span></a></li>
						</ul>
				 </nav>
				 <ul class="tabs">
						<li><a href="#tab1"><span><span>Category 1</span></span></a></li>
						<li><a href="#tab2"><span><span>Category 2</span></span></a></li>
						<li><a href="#tab3"><span><span>Category 3</span></span></a></li>
						<li><a href="#tab4"><span><span>Category 4</span></span></a></li>
						<li><a href="#tab5"><span><span>Category 5</span></span></a></li>
				 </ul>
				 <div class="tab_container">
						<div id="tab1" class="tab_content">
							 <div class="faded">
									<ul class="big-image">
										 <li><img src="images/slide1-1big.jpg"></li>
										 <li><img src="images/slide1-2big.jpg"></li>
										 <li><img src="images/slide1-3big.jpg"></li>
									</ul>
									<ul class="pagination">
										 <li><a href="#" rel="0"><img src="images/slide1-1.jpg"></a></li>
										 <li><a href="#" rel="1"><img src="images/slide1-2.jpg"></a></li>
										 <li><a href="#" rel="2"><img src="images/slide1-3.jpg"></a></li>
									</ul>
							 </div>
						</div>
						<div id="tab2" class="tab_content">
							 <div class="faded">
									<ul class="big-image">
										 <li><img src="images/slide2-1big.jpg"></li>
										 <li><img src="images/slide2-2big.jpg"></li>
										 <li><img src="images/slide2-3big.jpg"></li>
									</ul>
									<ul class="pagination">
										 <li><a href="#" rel="0"><img src="images/slide2-1.jpg"></a></li>
										 <li><a href="#" rel="1"><img src="images/slide2-2.jpg"></a></li>
										 <li><a href="#" rel="2"><img src="images/slide2-3.jpg"></a></li>
									</ul>
							 </div>
						</div>
						<div id="tab3" class="tab_content">
							 <div class="faded">
									<ul class="big-image">
										 <li><img src="images/slide3-1big.jpg"></li>
										 <li><img src="images/slide3-2big.jpg"></li>
										 <li><img src="images/slide3-3big.jpg"></li>
									</ul>
									<ul class="pagination">
										 <li><a href="#" rel="0"><img src="images/slide3-1.jpg"></a></li>
										 <li><a href="#" rel="1"><img src="images/slide3-2.jpg"></a></li>
										 <li><a href="#" rel="2"><img src="images/slide3-3.jpg"></a></li>
									</ul>
							 </div>
						</div>
						<div id="tab4" class="tab_content">
							 <div class="faded">
									<ul class="big-image">
										 <li><img src="images/slide4-1big.jpg"></li>
										 <li><img src="images/slide4-2big.jpg"></li>
										 <li><img src="images/slide4-3big.jpg"></li>
									</ul>
									<ul class="pagination">
										 <li><a href="#" rel="0"><img src="images/slide4-1.jpg"></a></li>
										 <li><a href="#" rel="1"><img src="images/slide4-2.jpg"></a></li>
										 <li><a href="#" rel="2"><img src="images/slide4-3.jpg"></a></li>
									</ul>
							 </div>
						</div>
						<div id="tab5" class="tab_content">
							 <div class="faded">
									<ul class="big-image">
										 <li><img src="images/slide5-1big.jpg"></li>
										 <li><img src="images/slide5-2big.jpg"></li>
										 <li><img src="images/slide5-3big.jpg"></li>
									</ul>
									<ul class="pagination">
										 <li><a href="#" rel="0"><img src="images/slide5-1.jpg"></a></li>
										 <li><a href="#" rel="1"><img src="images/slide5-2.jpg"></a></li>
										 <li><a href="#" rel="2"><img src="images/slide5-3.jpg"></a></li>
									</ul>
							 </div>
						</div>
				 </div>
			</div>
	 </header>
	 <div class="container">
			<!-- aside -->
			<aside>
				 <div class="inside">
						<h2>My Clients:</h2>
						<ul class="list">
							 <li><a href="#">Sed ut perspiciatis</a></li>
							 <li><a href="#">Unde omnis iste</a></li>
							 <li><a href="#">Natus error sit volup</a></li>
							 <li><a href="#">Tatem accusantium</a></li>
						</ul>
						<figure><img src="images/extra-img.png"></figure>
				 </div>
			</aside>
			<!-- content -->
			<section id="content">
				 <div class="wrapper">
						<article class="col-1">
							 <h2>Contact Form:</h2>
							 <form action="pruebax" method="post" enctype="multipart/form-data">
  <input type="text" name="name" required="True" placeholder="Your Name*"/>
  <input type="text" name="email" required="True" placeholder="Your Email*"/>
  <button>Insert</button>
</form>
						</article>
						<article class="col-2">
							 <h2>My Contacts:</h2>
							 <address>
							 <span>Zip Code:</span>50122<br>
							 <span>Country:</span>USA<br>
							 <span>City:</span>New York<br>
							 <span>Telephone:</span>+354 5635600<br>
							 <span>Fax:</span>+354 5635620<br>
							 <span>Email:</span><a href="#">businessco@mail.com</a>
							 </address>
						</article>
				 </div>
			</section>
	 </div>
</div>
<!-- footer -->
<footer>
	 <div class="container">
			<div class="inside"> <a rel="nofollow" href="http://www.templatemonster.com" class="new_window">Website template</a> designed by TemplateMonster.com<br>
				 <a href="http://www.templates.com/product/3d-models/" class="new_window">3D Models</a> provided by Templates.com<br>
            <!-- VLinks --></div>
	 </div>
</footer>
<script type="text/javascript"> Cufon.now(); </script>
</body>
</html>


		"""
		return SIMPLE_TEMPLATE
