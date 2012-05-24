# -*- coding: utf-8 -*-

from .options import JSTree

class JSTreeRegister(object):
    """ Описывает поведение jstree деревьев
    """
    def __init__(self):
        self._registry = {} # tree name -> jstree_class instance

    def register(self, name, jstree_class=None):
        """
        Регистрируем JSTree
        """
        if not jstree_class:
            jstree_class = JSTree
        self._registry[name] = jstree_class()

    def unregister(self, name):
        """
        Удаляем jstree
        """
        if name not in self._registry:
            raise ValueError('The instance %s is not registered' % name)
        del self._registry[name]

    def get_urls(self):
        from django.conf.urls import patterns, url, include
        # Добавляем вьюхи для всех зарегистрированных деревьев.
        urlpatterns = []
        for name, jstree_class in self._registry.iteritems():
            urlpatterns += patterns('',
                url(r'^%s/' % (name, ), include(jstree_class.urls))
            )
        return urlpatterns

    @property
    def urls(self):
        return self.get_urls(), 'jstree', 'jstree'

jstree = JSTreeRegister()