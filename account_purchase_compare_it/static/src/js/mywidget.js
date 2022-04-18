openerp.account_purchase_compare_it = function (instance) {
    id_anterior_pon = 0;
    var globalinterval = null;
    instance.web.form.widgets.add('mywidget_purchase_order_notify','instance.account_purchase_compare_it.mywidget_purchase_order_notify');
    instance.account_purchase_compare_it.mywidget_purchase_order_notify = instance.web.form.AbstractField.extend({
    init: function (field_manager, node) {
        this._super(field_manager, node);
        this.password = this.node.attrs.password === 'True' || this.node.attrs.password === '1';
            id_anterior_pon = 0;
    },
        get_value:function(){
            //   $.notify("Abriendo! "+ this.field_manager.datarecord.display_name +" "+ this.field_manager.datarecord.id, {color: "#fff", background: "#D44950",blur: 0.6,animationType:"scale",align:"center", verticalAlign:"top"});
         ////   if (id_anterior_pon == this.field_manager.datarecord.id)
         ////   {
         ////   }
         ////   else
          ////  {

    //        $.notify("Abriendo! "+ this.field_manager.datarecord.display_name +" "+ this.field_manager.datarecord.id);



            if (this.field_manager.datarecord.state != 'draft'){

            var model = new instance.web.Model("purchase.order");
            var ids = this.field_manager.datarecord.id;
            ////if (globalinterval != null)
           //// {
             ////   clearInterval(globalinterval);
           //// }
           //// globalinterval = setInterval(function(){ 
                model.call("get_temporal", [[ids]]).then(function(result) 
                 {
                    if (result == false)
                    {                        
                    }
                    else
                    {
                        tipo = result[0];
                        if (tipo=='1')
                        {
                           var n = noty({
                              text        : '<div class="activity-item"> <i class="fa fa-check-square-o"></i> <div class="activity"> '+ result.substring(1) + ' <span>Pedido de Compras</span> </div> </div>',
                              type        : 'success',
                              dismissQueue: true,
                             // layout      : 'topLeft',
                              closeWith   : ['click', 'backdrop'],
                              theme       : 'relax',
                              maxVisible  : 10,
                              modal       : true,
                              layout      : 'center',
                              animation   : {
                                  open  : 'animated bounceInLeft',
                                  close : 'animated bounceOutLeft',
                                  easing: 'swing',
                                  speed : 500
                              }
                          });
                        //    $.notifyjp( result.substring(1) ,'success');
                        }
                        if (tipo=='2')
                        {
                           var n = noty({
                              text        : '<div class="activity-item"> <i class="fa fa-bullhorn"></i> <div class="activity"> '+ result.substring(1) + ' <span>Pedido de Compras</span> </div> </div>',
                              type        : 'notification',
                              dismissQueue: true,
                             // layout      : 'topLeft',
                              closeWith   : ['click', 'backdrop'],
                              theme       : 'relax',
                              maxVisible  : 10,
                              modal       : true,
                              layout      : 'center',
                              animation   : {
                                  open  : 'animated bounceInLeft',
                                  close : 'animated bounceOutLeft',
                                  easing: 'swing',
                                  speed : 500
                              }
                          });
                         //   $.notifyjp( result.substring(1) ,'info');
                        }
                        if (tipo=='3')
                        {
                           var n = noty({
                              text        : '<div class="activity-item"> <i class="fa fa-warning"></i> <div class="activity"> '+ result.substring(1) + ' <span>Pedido de Compras</span> </div> </div>',
                              type        : 'warning',
                              dismissQueue: true,
                             // layout      : 'topLeft',
                              closeWith   : ['click', 'backdrop'],
                              theme       : 'relax',
                              maxVisible  : 10,
                              modal       : true,
                              layout      : 'center',
                              animation   : {
                                  open  : 'animated bounceInLeft',
                                  close : 'animated bounceOutLeft',
                                  easing: 'swing',
                                  speed : 500
                              }
                          });
                         //   $.notifyjp( result.substring(1) ,'warn');
                        }
                        if (tipo=='4')
                        {
                           var n = noty({
                              text        : '<div class="activity-item"> <i class="fa fa-exclamation-circle"></i> <div class="activity"> '+ result.substring(1) + ' <span>Pedido de Compras</span> </div> </div>',
                              type        : 'error',
                              dismissQueue: true,
                             // layout      : 'topLeft',
                              closeWith   : ['click', 'backdrop'],
                              theme       : 'relax',
                              maxVisible  : 10,
                              modal       : true,
                              layout      : 'center',
                              animation   : {
                                  open  : 'animated bounceInLeft',
                                  close : 'animated bounceOutLeft',
                                  easing: 'swing',
                                  speed : 500
                              }
                          });
                         //   $.notifyjp( result.substring(1) ,'error');
                        }                        
                    }                   
                 });}
          ////  },3000);
            
          //  model.call("write", [[this.field_manager.datarecord.id], {'temporal2': "james"}]).then(function(result){
            //           console.log("main resultttttttttttt", result);  
             //     });
return this.get('value')[0] && this.get('value')[1] ? (this.get('value')[0] + ',' + this.get('value')[1]) : false;
            }

        
    });

    //
    //here you can add more widgets if you need, as above...
    //
};
