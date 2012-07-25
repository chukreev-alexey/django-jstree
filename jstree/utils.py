# -*- coding: utf-8 -*-
from collections import defaultdict

class TreeAsDict(object):
    parent_map = defaultdict(list)
    id_field_name = 'id'
    parent_field_name = 'parent_id'
    title_field_name = 'name'

    def __init__(self, items):
        self.items = items
        self.result = []
        self.parent_map = {}
        for item in self.items:
            self.parent_map[self.get(item, self.parent_field_name)].\
                append(self.get(item, self.id_field_name))
        self.result = list(self.tree_level())

    def get(self, item, attr):
        if hasattr(item, attr):
            return getattr(item, attr)
        if type(item) == dict:
            return item.get(attr)
        return None

    def get_children(self, node):
        if node:
            node = self.get(node, 'id')
        if node in self.parent_map:
            return [item for item in self.items if self.get(item, 'id') in self.parent_map[node]]
        return []

    def tree_node(self, node):
        children = list(self.tree_level(node))
        return dict(name=self.get(node, self.title_field_name), children=children)

    def tree_level(self, parent=None):
        for node in self.get_children(parent):
            yield self.tree_node(node)