var TreeWidget, NEW_ITEM = "Новый элемент";
$(function(){
  TreeWidget = Backbone.View.extend({
    el: '#tree-container',
    initialize: function(options){
      options || (options = {});
      this.urlRoot = options.urlRoot;
      this.options = options;
      // Custom options
      if (options.select_node) this.select_node = options.select_node;
      if (options.hover) this.hover = options.hover;
      this.render();
    },
    events: {
      'loaded.jstree': 'load_tree',
      'move_node.jstree': 'move_node',
      'select_node.jstree': 'select_node',
      'create.jstree': 'create_node',
      'hover_node.jstree': 'hover',
      'click .js_fold': 'hide_show_node'
    },
    render: function(){
      // Набор опций для дерева
      var jstree_options = {
        json_data: {
          ajax: {
            url: this.urlRoot + 'tree/',
            data : function (li) {
              return (li == -1) ? {} : {parent: li.data().node_id};
            }
          }
        },
        core: {strings: { loading: "Загрузка...", new_node: NEW_ITEM }},
        ui: { select_limit: 1 },
        //themes : {theme : "default"},
        plugins: this.options.plugins ? this.options.plugins : ["themes", "json_data", "dnd", "crrm", "ui", "cookies"]
      };
      this.$el.jstree(jstree_options);
      return this;
    },
    load_tree: function(e, data){
      data.inst.open_all();
    },
    select_node: function(e, node){},
    move_node: function(e, data){
      var self = this,
        position = {'last': 'last-child', 'before': 'left', 'after': 'right'}[data.rslt.p],
        target = data.rslt.np.data().node_id;
      data.rslt.o.each(function (i) {
        $.ajax({
          async : false,
          type: 'POST',
          url: self.urlRoot + 'move_node/',
          data : {
            "node" : $(this).data().node_id,
            "target" : data.rslt.r.data().node_id,
            "position" : position
          }
        })
        .fail(function(){
          $.jstree.rollback(data.rlbk);
        });
      });
    },
    create_node: function(e, data){
      var parentId = data.rslt.parent === -1 ? "" : data.rslt.parent.data().node_id,
        postData = {
          'name': data.rslt.name,
          'parent': parentId
        },
        li = data.rslt.obj;
      $.ajax({
        async: false,
        url: this.urlRoot + 'add_node/',
        type: "POST",
        data: postData,
        dataType: "json"
      })
      .done(function(resp){
        $.each(resp.attr, function (key, value) {
          li.attr(key, value);
        });
        li.data(resp.metadata);
      })
      .fail(function(){
        $.jstree.rollback(data.rlbk);
      });
    },
    hover: function(e, data){},
    hide_show_node: function(e){
      e.stopPropagation();
      var node = $(e.target).closest('li');
      $.ajax({
        async : false,
        type: 'POST',
        url: this.urlRoot + (node.hasClass('jstree-hidden') ? 'show' : 'hide')+"_node/",
        data : {
          "node" : node.data().node_id
        }
      })
      .done(function(){
        node.find('.js_fold').removeClass('show hide');
        if (node.hasClass('jstree-hidden')) {
          node.removeClass('jstree-hidden');
          node.find('.js_fold').addClass('hide');
        }
        else {
          node.addClass('jstree-hidden');
          node.find('.js_fold').addClass('show');
        }
      });
      return false;
    }
  });
});
