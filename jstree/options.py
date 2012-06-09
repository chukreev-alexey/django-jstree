# -*- coding: utf-8 -*-
from collections import defaultdict

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
    id_field_name = 'id'
    parent_field_name = 'parent_id'
    title_field_name = 'name'

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

    def _render(self, items):
        self.items = items
        self.result = []
        self.parent_map = defaultdict(list)
        for item in self.items:
            self.parent_map[self._get(item, self.parent_field_name)].\
                append(self._get(item, self.id_field_name))
        #for k, v in self.parent_map.items():
        #    print k, v
        #    print '-------------------'
        return list(self._tree_level())

    def _get(self, item, attr):
        if hasattr(item, attr):
            return getattr(item, attr)
        if type(item) == dict:
            return item.get(attr)
        return None

    def _get_children(self, node):
        if node:
            node = self._get(node, 'id')
        if node in self.parent_map:
            return [item for item in self.items if self._get(item, 'id') in self.parent_map[node]]
        return []

    def _tree_level(self, parent=None):
        for node in self._get_children(parent):
            yield self.get_node_jstree(node)

    def get_queryset(self):
        return self.queryset.values('id', 'parent_id', 'name', 'visible')

    def get_jstree(self):
        """
        Вход в дерево
        """
        if not self.queryset:
            return []
        tree = self._render(self.get_queryset())
        return tree

    def get_node_jstree(self, node):
        node_data = self.get_node_data(node)
        node_data['children'] = list(self._tree_level(node))
        return node_data

    def get_node_data(self, node):
        """
        Возвращает jstree совместимую структуры элемента дерева
        """
        attr = {'id': 'n%d' % self._get(node, 'id')}
        if not self._get(node, 'visible'):
            attr['class'] = 'jstree-hidden'
        return {
            'data': {'title': self._get(node, 'name')},
            'metadata': {'node_id': self._get(node, 'id'), 'visible': self._get(node, 'visible')},
            'attr': attr,
        }

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
                node.save()
            except (InvalidMove, ValueError), e:
                status, resp = 400, {'error': unicode(e)}
        else:
            status, resp = 400, form.errors
        return JsonateResponse(resp, status=status)

    @method_decorator(login_required)
    @method_decorator(require_POST)
    def remove_node(self, request):
        status, resp = 200, {}
        item = get_object_or_404(self.queryset.model, pk=request.POST.get('node'))
        item.delete()
        return JsonateResponse(resp, status=status)

    @method_decorator(login_required)
    @method_decorator(require_POST)
    def toggle_node(self, request, oper):
        status, resp = 200, {}
        item = get_object_or_404(self.queryset.model, pk=request.POST.get('node'))
        item.visible = (oper == 'show')
        item.save()
        return JsonateResponse(resp, status=status)
