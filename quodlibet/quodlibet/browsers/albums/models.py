# -*- coding: utf-8 -*-
# Copyright 2013 Christoph Reiter
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation

from quodlibet.qltk.models import ObjectStore, ObjectModelFilter
from quodlibet.qltk.models import ObjectModelSort


class AlbumItem(object):

    def __init__(self, album):
        self.album = album

    def __repr__(self):
        return repr(self.album)


class AlbumModelMixin(object):

    def get_albums(self, paths):
        values = [self.get_value(self.get_iter(p), 0).album for p in paths]
        try:
            values.remove(None)
        except ValueError:
            return values
        else:
            return [v.album for v in self.itervalues() if v.album]

    def get_album(self, iter_):
        return self.get_value(iter_, 0).album


class AlbumModel(ObjectStore, AlbumModelMixin):

    def __init__(self, library):
        super(AlbumModel, self).__init__()
        self.__library = library

        albums = library.albums
        self.__sigs = [
            albums.connect("added", self._add_albums),
            albums.connect("removed", self._remove_albums),
            albums.connect("changed", self._change_albums)
        ]

        self.append(row=[AlbumItem(None)])
        self.append_many((AlbumItem(a) for a in albums.itervalues()))

    def refresh_all(self):
        """Trigger redraws for all rows"""

        for iter_, value in self.iterrows():
            self.row_changed(self.get_path(iter_), iter_)

    def destroy(self):
        library = self.__library
        for sig in self.__sigs:
            library.albums.disconnect(sig)
        self.__library = None
        self.clear()

    def _update_all(self):
        if not self.is_empty():
            row = self[0]
            self.row_changed(row.path, row.iter)

    def _add_albums(self, library, added):
        self.append_many((AlbumItem(a) for a in added))
        self._update_all()

    def _remove_albums(self, library, removed):
        removed_albums = removed.copy()
        iters_remove = []
        for iter_, item in self.iterrows():
            album = item.album
            if album is not None and album in removed_albums:
                removed_albums.remove(album)
                iters_remove.append(iter_)
                if not removed_albums:
                    break

        for iter_ in iters_remove:
            self.remove(iter_)

        self._update_all()

    def _change_albums(self, library, changed):
        """Trigger a row redraw for each album that changed"""

        changed_albums = changed.copy()
        for iter_, item in self.iterrows():
            album = item.album
            if album is not None and album in changed_albums:
                changed_albums.remove(album)
                self.row_changed(self.get_path(iter_), iter_)
                if not changed_albums:
                    break


class AlbumFilterModel(ObjectModelFilter, AlbumModelMixin):

    def contains_all(self, paths):
        values = (self.get_value(self.get_iter(p), 0).album for p in paths)
        return None in values


class AlbumSortModel(ObjectModelSort, AlbumModelMixin):
    pass
