# -*- coding: utf-8 -*-

from django import forms
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST

from jsonate.decorators import jsonate_request
from jsonate.http import JsonateResponse

class JSTree(object):
    """
    Описывает поведение конкретного jstree дерева
    """
    queryset = None
    tree_form = None
    add_node_form = None
    move_node_form = None
    maxdepth = 3

    def get_urls(self):
        from django.conf.urls import patterns, url, include
        urlpatterns = patterns('',
            url(r'^tree/$', self.tree, name='tree-load'),
            url(r'^move_node/$', self.move_node, name='tree-move-node'),
            url(r'^add_node/$', self.add_node, name='tree-add-node'),
            url(r'^remove_node/$', self.remove_node, name='tree-remove-node'),
            url(r'^(?P<oper>hide|show)_node/$', self.toggle_node, name='tree-toggle-node'),
        )
        return urlpatterns

    @property
    def urls(self):
        return self.get_urls(), 'jstree', 'jstree'

    def get_jstree(self):
        """
        Вход в дерево
        """
        if not self.queryset:
            return []
        root_nodes = self.queryset.filter(parent__isnull=True)
        ret = []
        for node in root_nodes:
            ret.append(self.get_node_jstree(node))
        return ret

    def get_node_jstree(self, node, **kwargs):
        """
        Рекурсивная функция отрисовки элементов дерева
        """
        maxdepth = kwargs.get('maxdepth', 1)
        ret, kwargs = self.get_node_data(node, **kwargs)
        if not node.visible:
            ret['attr']['class'] = 'jstree-hidden'
        if maxdepth >= 0 or maxdepth is None:
            queryset = node.get_children()
            children = []
            for child in queryset:
                children.append(self.get_node_jstree(child, **kwargs))
            ret['children'] = children
        elif node.is_leaf_node():
            ret['children'] = []
        else:
            ret['state'] = 'closed'
        return ret

    def get_node_data(self, node, **kwargs):
        """
        Возвращает jstree совместимую структуры элемента дерева
        """
        return {
            'data': {'title': node.name},
            'metadata': {'node_id': node.id, 'visible': node.visible},
            'attr': {'id': 'n%d' % node.id},
        }, kwargs

    def get_treeform_class(self):
        """
        Возвращает класс формы для корректной выдачи поддеревьев
        """
        if self.tree_form:
            return self.tree_form
        from .forms import GetSubTreeForm
        form_class = GetSubTreeForm
        form_class.base_fields['parent'].queryset = self.queryset
        return form_class

    @method_decorator(login_required)
    @method_decorator(jsonate_request)
    def tree(self, request):
        form_class = self.get_treeform_class()
        form = form_class(request.GET)
        if form.is_valid():
            parent = form.cleaned_data['parent']
            if parent:
                return self.get_node_jstree(parent)['children']
            else:
                return self.get_jstree()
        return []

    def get_add_node_form_class(self):
        """
        Возвращает класс формы для корректной выдачи поддеревьев
        """
        if self.add_node_form:
            return self.add_node_form
        from .forms import AddNodeForm
        form_meta = type('Meta', (), {
            "model": self.queryset.model,
            "fields": AddNodeForm._meta.fields
        })
        form_class = type('modelform', (AddNodeForm,), {"Meta": form_meta})
        return form_class

    @method_decorator(login_required)
    @method_decorator(require_POST)
    def add_node(self, request):
        status, resp = 200, {}
        form_class = self.get_add_node_form_class()
        form = form_class(request.POST)
        if form.is_valid():
            #node = form.save(commit=False)
            #node.visible = True
            #node.save()
            node = form.save()
            resp = self.get_node_jstree(node)
        else:
            status, resp = 400, form.errors
        return JsonateResponse(resp, status=status)

    def get_move_node_form_class(self):
        """
        Возвращает класс формы для корректной выдачи поддеревьев
        """
        if self.move_node_form:
            return self.move_node_form
        from .forms import MoveNodeForm
        form_class = MoveNodeForm
        form_class.base_fields['node'].queryset = self.queryset
        form_class.base_fields['target'].queryset = self.queryset
        return form_class

    @method_decorator(login_required)
    @method_decorator(require_POST)
    def move_node(self, request):
        status, resp = 200, {}
        form_class = self.get_move_node_form_class()
        form = form_class(request.POST)
        if form.is_valid():
            node = form.cleaned_data['node']
            target = form.cleaned_data['target']
            position = form.cleaned_data['position']
            try:
                node.move_to(target, position=position)
            except (InvalidMove, ValueError), e:
                status, resp = 400, {'error': unicode(e)}
        else:
            status, resp = 400, form.errors
        return JsonateResponse(resp, status=status)

    @method_decorator(login_required)
    @method_decorator(require_POST)
    def remove_node(self, request):
        status, resp = 200, {}
        """ удалить узел, при этом перетащив всех его потомков в родительский узел """
        item = get_object_or_404(self.queryset.model, pk=request.POST.get('node'))
        for child in item.get_children():
            child.parent = item.parent
            child.save()
        item.delete()
        return JsonateResponse(resp, status=status)

    @method_decorator(login_required)
    @method_decorator(require_POST)
    def toggle_node(self, request, oper):
        status, resp = 200, {}
        """ удалить узел, при этом перетащив всех его потомков в родительский узел """
        item = get_object_or_404(self.queryset.model, pk=request.POST.get('node'))
        item.visible = (oper == 'show')
        item.save()
        return JsonateResponse(resp, status=status)
