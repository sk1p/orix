# -*- coding: utf-8 -*-
# Copyright 2018-2021 the orix developers
#
# This file is part of orix.
#
# orix is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# orix is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with orix.  If not, see <http://www.gnu.org/licenses/>.

"""The fundamental sector for a symmetry in the stereographic
projection.
"""

import numpy as np

from orix.vector import SphericalRegion, Vector3d


class FundamentalSector(SphericalRegion):
    """Fundamental sector for a symmetry in the inverse pole figure,
    defined by a set of (typically three) normals.
    """

    # This is only set for T (23), Th (m-3) and O (432), in the
    # Symmetry.fundamental_sector property, because the UV S2 sampling
    # isn't uniform enough to produce the correct center according to
    # MTEX
    _center = None

    @property
    def vertices(self):
        n = self.size
        if n == 0:
            return Vector3d.empty()
        else:
            normals = self.reshape(1, n)
            u = normals.cross(normals.transpose())
            return Vector3d(u[u <= self]).unique().unit

    @property
    def center(self):
        """Center vector of the fundamental sector.

        Taken from MTEX' :code:`sphericalRegion.center`.
        """
        v = self.vertices.unique()
        n_vertices = v.size
        n_normals = self.size
        if n_normals < 2:
            center = self
        elif n_vertices < 3:
            # Find the pair of maximum angle
            angles = self.angle_with(self.reshape(n_normals, 1)).data
            indices = np.argmax(angles, axis=1)
            center = self[indices].mean()
        elif n_vertices < 4:
            center = v.mean()
        elif isinstance(self._center, Vector3d):
            # Only the case for T (23), Th (m-3) and O (432), for which
            # the S2 sampling isn't uniform enough to produce the
            # correct center according to MTEX
            center = self._center
        else:
            # Avoid circular import
            from orix.sampling import uniform_S2_sample

            v_all = uniform_S2_sample(resolution=1)
            v = v_all[v_all < self]
            center = v.mean()
        return Vector3d(center)

    @property
    def edges(self):
        """Unit vectors which delineates the region in the stereographic
        projection.

        They are sorted in the counter-clockwise direction around the
        sector center in the stereographic projection.

        The first edge is repeated at the end. This is done so that
        :meth:`orix.plot.StereographicPlot.plot` draws bounding lines
        without gaps.
        """
        if self.size == 0:
            return Vector3d.empty()

        edge_steps = 500
        circles = self.get_circle(steps=edge_steps)
        edges = np.zeros((self.size * edge_steps + 3, 3))
        vertices = self.vertices

        if vertices.size == 0:
            return circles

        j = 0
        for ci, vi in zip(circles, vertices):
            # Only get the parts of the great circle that are within
            # this spherical region
            ci_inside = ci[ci <= self]
            v_keep = Vector3d(np.vstack((ci_inside.data, vi.data)))
            v_keep = v_keep.unique()
            order = np.lexsort((v_keep.azimuth.data, v_keep.polar.data))
            v_keep = v_keep[order]
            v_n = v_keep.size
            edges[j : j + v_n] = v_keep.data
            j += v_n
        edges = edges[:j]

        # Sort
        center = self.center
        vz = Vector3d.zvector()
        angle = vz.angle_with(center).data
        axis = vz.cross(center)
        edges_rotated = Vector3d(edges).rotate(axis=axis, angle=-angle)
        order = np.argsort(edges_rotated.azimuth.data)
        edges = edges[order]

        return Vector3d(edges)
