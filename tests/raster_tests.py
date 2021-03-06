""" Unit tests for raster functions """

import unittest
import os
import numpy as np
from test_helper import TESTDATA

import karta

class RegularGridTests(unittest.TestCase):

    def setUp(self):
        pe = peaks(n=49)
        self.rast = karta.RegularGrid((0.0, 0.0, 30.0, 30.0, 0.0, 0.0), values=pe)
        return

    def test_get_resolution(self):
        grid = karta.RegularGrid([0.0, 0.0, 25.0, 35.0, 10.0, 10.0])
        self.assertEqual(grid.resolution, (25.0, 35.0))
        return

    def test_add_rgrid(self):
        rast2 = karta.RegularGrid(self.rast.transform,
                                  values=np.random.random(self.rast.size))
        res = self.rast + rast2
        self.assertTrue(np.all(res[:,:] == self.rast[:,:]+rast2[:,:]))
        return

    def test_sub_rgrid(self):
        rast2 = karta.RegularGrid(self.rast.transform,
                                  values=np.random.random(self.rast.size))
        res = self.rast - rast2
        self.assertTrue(np.all(res[:,:] == self.rast[:,:]-rast2[:,:]))
        return

    def test_center_coords(self):
        grid = karta.RegularGrid((0.0, 0.0, 30.0, 30.0, 0.0, 0.0),
                                 values=np.zeros([49, 49]))
        ans = np.meshgrid(np.arange(15.0, 1471.0, 30.0),
                          np.arange(15.0, 1471.0, 30.0))
        self.assertEqual(0.0, np.sum(grid.center_coords()[0] - ans[0]))
        self.assertEqual(0.0, np.sum(grid.center_coords()[1] - ans[1]))
        return

    def test_center_coords_skewed(self):
        grid = karta.RegularGrid((15.0, 15.0, 30.0, 30.0, 20.0, 10.0),
                                 values=np.zeros([5, 5]))
        X, Y = grid.center_coords()
        self.assertEqual(X[0,0], 40.0)
        self.assertEqual(Y[0,0], 35.0)
        self.assertEqual(X[-1,0], 120.0)
        self.assertEqual(Y[-1,0], 155.0)
        self.assertEqual(X[-1,-1], 240.0)
        self.assertEqual(Y[-1,-1], 195.0)
        return

    def test_apply(self):
        msk = np.zeros([8, 8], dtype=np.bool)
        msk[3, 2] = True
        msk[:2,3:] = True
        val = np.arange(64, dtype=np.float64).reshape([8,8])
        val_ = val.copy()
        val[msk] = -1
        grid = karta.RegularGrid([0, 0, 1, 1, 0, 0], values=val, nodata_value=-1)
        grid.apply(lambda x: x**2)

        self.assertTrue(np.all(grid[:,:][msk] == -1))
        self.assertTrue(np.all(grid[:,:][~msk] == val_[~msk]**2))
        return

    def test_merge(self):
        grid1 = karta.RegularGrid([10, 20, 1, 1, 0, 0], values=np.ones([8, 8]))
        grid2 = karta.RegularGrid([7, 22, 1, 1, 0, 0], values=2*np.ones([4, 6]))
        grid3 = karta.RegularGrid([12, 15, 1, 1, 0, 0], values=3*np.ones([5, 5]))
        grid_combined = karta.raster.merge([grid1, grid2, grid3])
        self.assertEqual(grid_combined.transform, (7.0, 15.0, 1.0, 1.0, 0.0, 0.0))
        self.assertEqual(grid_combined.size, (13, 11))
        self.assertEqual(np.sum(np.isnan(grid_combined[:,:])), 42)
        return

    def test_merge_weighted(self):
        grid1 = karta.RegularGrid([10, 20, 1, 1, 0, 0], values=np.ones([8, 8]))
        grid2 = karta.RegularGrid([7, 22, 1, 1, 0, 0], values=2*np.ones([4, 6]))
        grid3 = karta.RegularGrid([12, 19, 1, 1, 0, 0], values=3*np.ones([5, 5]))
        grid_combined = karta.raster.merge([grid1, grid2, grid3], weights=[1, 2, 3])
        self.assertAlmostEqual(grid_combined[4,4], 1.66666666666)
        self.assertAlmostEqual(grid_combined[2,8], 2.5)
        self.assertAlmostEqual(grid_combined[4,5], 2.33333333333)
        return

    def test_resample(self):
        # use linear function so that nearest neighbour and linear interp are
        # exact
        def makegrid(start, finish, n, res):
            xx, yy = np.meshgrid(np.linspace(start, finish, n),
                                 np.linspace(start, finish, n))
            zz = 2.0*xx - 3.0*yy
            return karta.RegularGrid((0.0, 0.0, res, res, 0.0, 0.0), values=zz)

        # node numbers from a line with extreme edges at [0, 1]
        g = makegrid(1.0/300, 1.0-1.0/300, 150, 1.0)
        sol = makegrid(3.0/300, 1.0-3.0/300, 50, 3.0)
        gnew = g.resample(3.0, 3.0)
        residue = gnew[:,:] - sol[:,:]
        self.assertTrue(np.max(np.abs(residue)) < 1e-12)
        return

    def test_sample_nearest(self):
        grid = karta.RegularGrid([0.0, 0.0, 1.0, 1.0, 0.0, 0.0],
                                 values=np.array([[0, 1], [1, 0.5]]))
        self.assertEqual(grid.sample_nearest(0.6, 0.7), 0.0)
        self.assertEqual(grid.sample_nearest(0.6, 1.3), 1.0)
        self.assertEqual(grid.sample_nearest(1.4, 0.3), 1.0)
        self.assertEqual(grid.sample_nearest(1.6, 1.3), 0.5)
        return

    def test_sample_multipoint(self):
        grid = karta.RegularGrid([0.0, 0.0, 1.0, 1.0, 0.0, 0.0],
                                 values=np.array([[0, 1], [1, 0.5]]))
        mp = karta.Multipoint([(0.6, 0.7), (0.6, 1.3), (1.4, 0.3), (1.6, 1.3)],
                              crs=grid.crs)
        self.assertTrue(np.all(np.allclose(grid.sample(mp, method="nearest"),
                                           np.array([0.0, 1.0, 1.0, 0.5]))))
        return

    def test_sample_nearest_skewed(self):
        grid = karta.RegularGrid([0.0, 0.0, 1.0, 1.0, 0.5, 0.2],
                                 values=np.array([[0, 1], [1, 0.5]]))
        self.assertEqual(grid.sample_nearest(1, 0.75), 0.0)
        self.assertEqual(grid.sample_nearest(1.5, 1.05), 1.0)
        self.assertEqual(grid.sample_nearest(1.2, 1.4), 1.0)
        self.assertEqual(grid.sample_nearest(2.0, 1.7), 0.5)
        return

    def test_sample_bilinear(self):
        grid = karta.RegularGrid([0.0, 0.0, 1.0, 1.0, 0.0, 0.0],
                                 values=np.array([[0, 1], [1, 0.5]]))
        self.assertEqual(grid.sample_bilinear(1.0, 1.0), 0.625)
        return

    def test_sample_bilinear_skewed(self):
        grid = karta.RegularGrid([0.0, 0.0, 1.0, 1.0, 0.5, 0.2],
                                 values=np.array([[0, 1], [1, 0.5]]))
        self.assertEqual(grid.sample_bilinear(1.5, 1.2), 0.625)
        return

    def test_sample_bilinear2(self):
        grid = karta.RegularGrid([0.0, 0.0, 1.0, 1.0, 0.0, 0.0],
                                 values=np.array([[0, 1], [1, 0.5]]))
        xi, yi = np.meshgrid(np.linspace(0.5, 1.5), np.linspace(0.5, 1.5))
        z = grid.sample_bilinear(xi.ravel(), yi.ravel())
        self.assertEqual([z[400], z[1200], z[1550], z[2120]],
                         [0.16326530612244894, 0.48979591836734693,
                          0.63265306122448983, 0.74052478134110788])
        return

    def test_vertex_coords(self):
        grid = karta.RegularGrid((0.0, 0.0, 30.0, 30.0, 0.0, 0.0),
                                 values=np.zeros([49, 49]))
        ans = np.meshgrid(np.arange(15.0, 1486.0, 30.0),
                          np.arange(15.0, 1486.0, 30.0))
        self.assertTrue(np.sum(grid.vertex_coords()[0] - ans[0]) < 1e-10)
        self.assertTrue(np.sum(grid.vertex_coords()[1] - ans[1]) < 1e-10)
        return

    def test_vertex_coords_skewed(self):
        grid = karta.RegularGrid((0.0, 0.0, 30.0, 30.0, 20.0, 10.0),
                                 values=np.zeros([5, 5]))
        ans = np.meshgrid(np.arange(15.0, 1486.0, 30.0),
                          np.arange(15.0, 1486.0, 30.0))
        self.assertTrue(np.sum(self.rast.vertex_coords()[0] - ans[0]) < 1e-10)
        self.assertTrue(np.sum(self.rast.vertex_coords()[1] - ans[1]) < 1e-10)
        return

    def test_get_extent(self):
        ereg = (0.0, 1470.0, 0.0, 1470.0)
        creg = (15.0, 1455.0, 15.0, 1455.0)
        self.assertEqual(self.rast.get_extent(reference='center'), creg)
        self.assertEqual(self.rast.get_extent(reference='edge'), ereg)
        return

    def test_get_extent_crs(self):
        pe = peaks(n=49)
        crs = karta.crs.ProjectedCRS("+proj=utm +zone=12 +ellps=WGS84 +north=True", "UTM 12N (WGS 84)")
        rast_utm12N = karta.RegularGrid((0.0, 0.0, 10000.0, 10000.0, 0.0, 0.0),
                                        values=pe,
                                        crs=crs)
        a,b,c,d = rast_utm12N.get_extent(reference='center',
                                         crs=karta.crs.LonLatWGS84)
        self.assertAlmostEqual(a, -115.45687156)
        self.assertAlmostEqual(b, -111.13480112)
        self.assertAlmostEqual(c, 0.0450996517)
        self.assertAlmostEqual(d, 4.3878488543)
        return

    def test_minmax_nodata(self):
        values = np.array([[4, 5, 3], [4, 2, -9], [3, 6, 1]])

        self.rast = karta.RegularGrid((0.0, 0.0, 30.0, 30.0, 0.0, 0.0),
                                      values=values, nodata_value=-9)
        minmax = self.rast.minmax()
        self.assertEqual(minmax, (1, 6))
        return

    def test_minmax_nodata2(self):
        values = -9*np.ones([3,3])

        self.rast = karta.RegularGrid((0.0, 0.0, 30.0, 30.0, 0.0, 0.0),
                                      values=values, nodata_value=-9)
        minmax = self.rast.minmax()
        self.assertTrue(np.isnan(minmax[0]))
        self.assertTrue(np.isnan(minmax[1]))
        return

    def test_minmax(self):
        minmax = self.rast.minmax()
        self.assertEqual(minmax, (-6.5466445243204294, 8.075173545159231))
        return

    def test_clip(self):
        clipped = self.rast.clip(500, 950, 500, 950)
        self.assertEqual(clipped.size, (15, 15))
        self.assertEqual(clipped.transform, (510, 510, 30, 30, 0, 0))
        X, Y = clipped.center_coords()
        self.assertEqual(X[0,0], 525)
        self.assertEqual(X[0,-1], 945)
        self.assertEqual(Y[0,0], 525)
        self.assertEqual(Y[-1,0], 945)
        return

    def test_clip_to_extent(self):
        proto = karta.RegularGrid((500, 500, 30, 30, 0, 0), np.zeros((15,15)))
        clipped = self.rast.clip(*proto.get_extent("edge"))
        self.assertEqual(clipped.size, (15, 15))
        self.assertEqual(clipped.transform, (510, 510, 30, 30, 0, 0))
        X, Y = clipped.center_coords()
        self.assertEqual(X[0,0], 525)
        self.assertEqual(X[0,-1], 945)
        self.assertEqual(Y[0,0], 525)
        self.assertEqual(Y[-1,0], 945)
        return

    def test_resize_smaller(self):
        proto = karta.RegularGrid((500, 500, 30, 30, 0, 0), values=peaks(50))
        newgrid = proto.resize([620, 650, 1370, 1310])
        self.assertEqual(newgrid.transform, (620.0, 650.0, 30.0, 30.0, 0.0, 0.0))
        self.assertTrue(np.all(newgrid[:,:] == proto[5:27,4:29]))
        return

    def test_resize_larger(self):
        proto = karta.RegularGrid((500, 500, 30, 30, 0, 0), values=peaks(50))
        newgrid = proto.resize([380, 320, 380+30*60, 320+30*62])
        self.assertEqual(newgrid.transform, (380.0, 320.0, 30.0, 30.0, 0.0, 0.0))
        self.assertTrue(np.all(newgrid[6:56,4:54] == proto[:,:]))
        return

    def test_resize_lower_left(self):
        proto = karta.RegularGrid((500, 500, 30, 30, 0, 0), values=peaks(50))
        newgrid = proto.resize([380, 320, 380+30*30, 320+30*32])
        self.assertEqual(newgrid.transform, (380.0, 320.0, 30.0, 30.0, 0.0, 0.0))
        self.assertTrue(np.all(newgrid[6:,4:] == proto[:26,:26]))
        return

    def test_resize_upper_right(self):
        proto = karta.RegularGrid((500, 500, 30, 30, 0, 0), values=peaks(50))
        newgrid = proto.resize([1940, 1910, 1940+30*10, 1910+30*7])
        self.assertEqual(newgrid.transform, (1940.0, 1910.0, 30.0, 30.0, 0.0, 0.0))
        self.assertTrue(np.all(newgrid[:3,:2] == proto[-3:,-2:]))
        return

    def test_data_mask_nan(self):
        T = [0.0, 0.0, 1.0, 1.0, 0.0, 0.0]
        v = np.arange(64, dtype=np.float64).reshape([8, 8])
        v[0,2:7] = np.nan
        g = karta.RegularGrid(T, values=v, nodata_value=np.nan)
        self.assertEqual(np.sum(g.data_mask), 59)
        return

    def test_data_mask_nonnan(self):
        T = [0.0, 0.0, 1.0, 1.0, 0.0, 0.0]
        v = np.arange(64, dtype=np.int8).reshape([8, 8])
        v[0,2:7] = -1
        g = karta.RegularGrid(T, values=v, nodata_value=-1)
        self.assertEqual(np.sum(g.data_mask), 59)
        return

    def test_mask_poly(self):
        t = -np.linspace(0, 2*np.pi, 200)
        xp = ((2+np.cos(7*t)) * np.cos(t+0.3) + 4) * 12
        yp = ((2+np.cos(7*t)) * np.sin(t+0.2) + 4) * 12
        poly = karta.Polygon(zip(xp, yp), crs=karta.crs.Cartesian)
        grid = karta.RegularGrid([0.0, 0.0, 0.1, 0.1, 0.0, 0.0],
                                 values=np.arange(1e6).reshape(1000, 1000),
                                 crs=karta.crs.Cartesian)
        masked_grid = grid.mask_by_poly(poly)
        self.assertEqual(int(np.nansum(masked_grid[:,:])), 97048730546)
        return

    def test_mask_poly_inplace(self):
        t = -np.linspace(0, 2*np.pi, 200)
        xp = ((2+np.cos(7*t)) * np.cos(t+0.3) + 4) * 12
        yp = ((2+np.cos(7*t)) * np.sin(t+0.2) + 4) * 12
        poly = karta.Polygon(zip(xp, yp), crs=karta.crs.Cartesian)
        grid = karta.RegularGrid([0.0, 0.0, 0.1, 0.1, 0.0, 0.0],
                                 values=np.arange(1e6).reshape(1000, 1000),
                                 crs=karta.crs.Cartesian)
        grid.mask_by_poly(poly, inplace=True)
        self.assertEqual(int(np.nansum(grid[:,:])), 97048730546)
        return

    def test_mask_poly_partial(self):
        # test case where polygon is partly outside the grid extents
        # simply ensures that it doesn't crash for now
        t = -np.linspace(0, 2*np.pi, 200)
        xp = ((2+np.cos(7*t)) * np.cos(t+0.3) + 2) * 12
        yp = ((2+np.cos(7*t)) * np.sin(t+0.2) + 2) * 12
        poly = karta.Polygon(zip(xp, yp), crs=karta.crs.Cartesian)
        grid = karta.RegularGrid([0.0, 0.0, 0.1, 0.1, 0.0, 0.0],
                                 values=np.arange(1e6).reshape(1000, 1000),
                                 crs=karta.crs.Cartesian)
        masked_grid = grid.mask_by_poly(poly)
        return

    def test_mask_poly_multipl(self):
        t = -np.linspace(0, 2*np.pi, 200)
        xp = ((2+np.cos(7*t)) * np.cos(t+0.3) + 4) * 4 + 15
        yp = ((2+np.cos(7*t)) * np.sin(t+0.2) + 4) * 4 + 72
        poly = karta.Polygon(zip(xp, yp), crs=karta.crs.Cartesian)
        xp2 = ((2+np.cos(7*t)) * np.cos(t+0.3) + 4) * 6 + 40
        yp2 = ((2+np.cos(7*t)) * np.sin(t+0.2) + 4) * 6 + 30
        poly2 = karta.Polygon(zip(xp2, yp2), crs=karta.crs.Cartesian)
        grid = karta.RegularGrid([0.0, 0.0, 0.1, 0.1, 0.0, 0.0],
                                 values=np.arange(1e6).reshape(1000, 1000),
                                 crs=karta.crs.Cartesian)
        masked_grid = grid.mask_by_poly([poly, poly2])
        self.assertEqual(int(np.nansum(masked_grid[:,:])), 47081206720)
        return

    def test_get_positions(self):
        grid = karta.RegularGrid([0.0, 0.0, 1.0, 1.0, 0.0, 0.0],
                                 values=np.zeros((3,3)))
        (i, j) = grid.get_positions(1.5, 1.5)
        self.assertEqual((i,j), (1.0, 1.0))
        (i, j) = grid.get_positions(2.0, 1.5)
        self.assertEqual((i,j), (1.0, 1.5))
        return

    def test_get_indices(self):
        ind = self.rast.get_indices(15.0, 15.0)
        self.assertEqual(tuple(ind), (0, 0))
        ind = self.rast.get_indices(1455.0, 1455.0)
        self.assertEqual(tuple(ind), (48, 48))
        return

    def test_get_indices_onevec(self):
        ind = self.rast.get_indices([15.0], [15.0])
        self.assertEqual(tuple(ind), (0, 0))
        ind = self.rast.get_indices(1455.0, 1455.0)
        self.assertEqual(tuple(ind), (48, 48))
        return

    def test_get_indices_vec(self):
        ind = self.rast.get_indices(np.arange(15.0, 1470, 5),
                                    np.arange(15.0, 1470, 5))

        xi = np.array([ 0,  0,  0,  0,  1,  1,  1,  1,  1,  2,  2,  2,  2, 2,
            2, 2,  3, 3,  3,  3,  3,  4,  4,  4,  4,  4,  4,  4,  5,  5, 5,  5,
            5,  6, 6,  6,  6,  6,  6,  6,  7,  7,  7,  7,  7,  8,  8, 8,  8, 8,
            8, 8,  9,  9,  9,  9,  9, 10, 10, 10, 10, 10, 10, 10, 11, 11, 11,
            11, 11, 12, 12, 12, 12, 12, 12, 12, 13, 13, 13, 13, 13, 14, 14, 14,
            14, 14, 14, 14, 15, 15, 15, 15, 15, 16, 16, 16, 16, 16, 16, 16, 17,
            17, 17, 17, 17, 18, 18, 18, 18, 18, 18, 18, 19, 19, 19, 19, 19, 20,
            20, 20, 20, 20, 20, 20, 21, 21, 21, 21, 21, 22, 22, 22, 22, 22, 22,
            22, 23, 23, 23, 23, 23, 24, 24, 24, 24, 24, 24, 24, 25, 25, 25, 25,
            25, 26, 26, 26, 26, 26, 26, 26, 27, 27, 27, 27, 27, 28, 28, 28, 28,
            28, 28, 28, 29, 29, 29, 29, 29, 30, 30, 30, 30, 30, 30, 30, 31, 31,
            31, 31, 31, 32, 32, 32, 32, 32, 32, 32, 33, 33, 33, 33, 33, 34, 34,
            34, 34, 34, 34, 34, 35, 35, 35, 35, 35, 36, 36, 36, 36, 36, 36, 36,
            37, 37, 37, 37, 37, 38, 38, 38, 38, 38, 38, 38, 39, 39, 39, 39, 39,
            40, 40, 40, 40, 40, 40, 40, 41, 41, 41, 41, 41, 42, 42, 42, 42, 42,
            42, 42, 43, 43, 43, 43, 43, 44, 44, 44, 44, 44, 44, 44, 45, 45, 45,
            45, 45, 46, 46, 46, 46, 46, 46, 46, 47, 47, 47, 47, 47, 48, 48, 48,
            48, 48, 48])


        yi = np.array([ 0,  0,  0,  0,  1,  1,  1,  1,  1,  2,  2,  2,  2,  2,
            2, 2,  3, 3,  3,  3,  3,  4,  4,  4,  4,  4,  4,  4,  5,  5,  5,
            5, 5,  6, 6,  6,  6,  6,  6,  6,  7,  7,  7,  7,  7,  8,  8,  8,
            8, 8,  8, 8,  9,  9,  9,  9,  9, 10, 10, 10, 10, 10, 10, 10, 11,
            11, 11, 11, 11, 12, 12, 12, 12, 12, 12, 12, 13, 13, 13, 13, 13, 14,
            14, 14, 14, 14, 14, 14, 15, 15, 15, 15, 15, 16, 16, 16, 16, 16, 16,
            16, 17, 17, 17, 17, 17, 18, 18, 18, 18, 18, 18, 18, 19, 19, 19, 19,
            19, 20, 20, 20, 20, 20, 20, 20, 21, 21, 21, 21, 21, 22, 22, 22, 22,
            22, 22, 22, 23, 23, 23, 23, 23, 24, 24, 24, 24, 24, 24, 24, 25, 25,
            25, 25, 25, 26, 26, 26, 26, 26, 26, 26, 27, 27, 27, 27, 27, 28, 28,
            28, 28, 28, 28, 28, 29, 29, 29, 29, 29, 30, 30, 30, 30, 30, 30, 30,
            31, 31, 31, 31, 31, 32, 32, 32, 32, 32, 32, 32, 33, 33, 33, 33, 33,
            34, 34, 34, 34, 34, 34, 34, 35, 35, 35, 35, 35, 36, 36, 36, 36, 36,
            36, 36, 37, 37, 37, 37, 37, 38, 38, 38, 38, 38, 38, 38, 39, 39, 39,
            39, 39, 40, 40, 40, 40, 40, 40, 40, 41, 41, 41, 41, 41, 42, 42, 42,
            42, 42, 42, 42, 43, 43, 43, 43, 43, 44, 44, 44, 44, 44, 44, 44, 45,
            45, 45, 45, 45, 46, 46, 46, 46, 46, 46, 46, 47, 47, 47, 47, 47, 48,
            48, 48, 48, 48, 48])

        self.assertTrue(np.all(ind[0] == xi))
        self.assertTrue(np.all(ind[1] == yi))
        return

    def test_profile(self):
        path = karta.Line([(15.0, 15.0), (1484.0, 1484.0)], crs=karta.crs.Cartesian)
        pts, z = self.rast.profile(path, resolution=42.426406871192853, method="nearest")
        expected = self.rast[:,:].diagonal()
        self.assertEqual(len(pts), 49)
        self.assertTrue(np.allclose(z, expected))
        return

    def test_gridpoints(self):
        np.random.seed(49)
        x = np.random.rand(20000)*10.0-5.0
        y = np.random.rand(20000)*10.0-5.0
        z = x**2+y**3

        T = [-5.0, -5.0, 0.25, 0.25, 0.0, 0.0]
        grid = karta.raster.gridpoints(x, y, z, T, karta.crs.Cartesian)

        Xg, Yg = grid.center_coords()
        self.assertTrue(np.sum(np.abs(Xg**2+Yg**3-grid[:,:]))/Xg.size < 0.45)
        return

    def test_read_aai(self):
        grid = karta.read_aai(os.path.join(TESTDATA,'peaks49.asc'))
        self.assertTrue(np.all(grid[::-1] == self.rast[:,:]))
        return

    def test_set_nodata(self):
        v = np.arange(64, dtype=np.float64).reshape([8,8])
        v[2:4, 5:7] = -1
        grid = karta.RegularGrid([0, 0, 1, 1, 0, 0], values=v, nodata_value=-1)
        self.assertEqual(grid.nodata, -1.0)
        grid.set_nodata_value(np.nan)
        self.assertTrue(np.isnan(grid.nodata))
        self.assertEqual(np.sum(np.isnan(grid[:,:])), 4)
        self.assertEqual(np.sum(grid[:,:] == -1.0), 0)
        return

class WarpedGridTests(unittest.TestCase):

    def setUp(self):
        ii = np.arange(50.0)
        jj = np.arange(50.0)
        X, Y = np.meshgrid(np.sin(ii/25.0 * 2*np.pi),
                           np.sin(jj/50.0 * 2*np.pi))
        values = karta.raster.witch_of_agnesi(50, 50)
        self.rast = karta.WarpedGrid(X=X, Y=Y, values=values)

    def test_add_sgrid(self):
        rast2 = karta.WarpedGrid(X=self.rast.X, Y=self.rast.Y,
                                 values=np.random.random(self.rast.values.shape))
        res = self.rast + rast2
        self.assertTrue(np.all(res.values == self.rast.values+rast2.values))
        return

    def test_sub_sgrid(self):
        rast2 = karta.WarpedGrid(X=self.rast.X, Y=self.rast.Y,
                                 values=np.random.random(self.rast.values.shape))
        res = self.rast - rast2
        self.assertTrue(np.all(res.values == self.rast.values-rast2.values))
        return

#class TestInterpolation(unittest.TestCase):
#
#    def test_idw(self):
#        # Test inverse weighted distance interpolation
#        Xm, Ym = np.meshgrid(np.arange(10), np.arange(10))
#        G = np.c_[Xm.flat, Ym.flat]
#        obs = np.array(((2,4,5),(6,3,4),(3,9,9)))
#        D = raster.interpolation.interp_idw(G, obs, wfunc=lambda d: 1.0/(d+1e-16)**0.5)
#        self.assertEqual(D, np.array([ 5.77099225,  5.73080888,  5.68934588,
#                            5.64656361,  5.60263926, 5.56391335,  5.54543646,
#                            5.55810434,  5.59468599,  5.64001991, 5.7666018 ,
#                            5.71712039,  5.66733266,  5.61528705,  5.55254697,
#                            5.48200769,  5.44194711,  5.4718629 ,  5.54176929,
#                            5.61255561, 5.76627041,  5.70140932,  5.64212525,
#                            5.59011147,  5.50963694, 5.36912109,  5.24490032,
#                            5.34965772,  5.49388958,  5.59812945, 5.7765376 ,
#                            5.67823283,  5.58875282,  5.57796102,  5.51352082,
#                            5.30130025,  4.00000002,  5.2696964 ,  5.49251053,
#                            5.61373077, 5.81944097,  5.68356449,  5.00000001,
#                            5.61034065,  5.60629104, 5.47740263,  5.34297441,
#                            5.43952794,  5.57499849,  5.6693856 , 5.91915228,
#                            5.83714501,  5.76171956,  5.78893204,  5.78328667,
#                            5.71759216,  5.65687878,  5.66124481,  5.70678887,
#                            5.75517987, 6.06116315,  6.0515271 ,  6.04980015,
#                            6.05331942,  6.02324779, 5.95580534,  5.88858853,
#                            5.8514621 ,  5.84418368,  5.85242989, 6.21638838,
#                            6.27774217,  6.35281161,  6.38711869,  6.31999906,
#                            6.19926611,  6.09004119,  6.01415787,  5.96971255,
#                            5.94708184, 6.35785785,  6.4954344 ,  6.70982294,
#                            6.88076712,  6.68090612, 6.43193841,  6.26024319,
#                            6.14772366,  6.07568133,  6.03068086, 6.45468497,
#                            6.63857194,  6.9936249 ,  8.99999996,  6.97005635,
#                            6.58706897,  6.37686191,  6.24425398,  6.15677403,
#                            6.09829941]))
#        return

def peaks(n=49):
    """ 2d peaks function of MATLAB logo fame. """
    X, Y = np.meshgrid(np.linspace(-3, 3, n), np.linspace(-3, 3, n))
    return 3.0 * (1-X)**2 * np.exp(-X**2 - (Y+1)**2) \
            - 10.0 * (X/5.0 - X**3 - Y**5) * np.exp(-X**2 - Y**2) \
            - 1.0/3.0 * np.exp(-(X+1)**2 - Y**2)

if __name__ == "__main__":
    unittest.main()

