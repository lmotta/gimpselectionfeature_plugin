# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : Map Canvas Effects
Description          : Tools for making effects of geometries within the mapcanvas
Date                 : January, 2019
copyright            : (C) 2019 by Luiz Motta
email                : motta.luiz@gmail.com

 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Luiz Motta'
__date__ = '2019-01-31'
__copyright__ = '(C) 2019, Luiz Motta'
__revision__ = '$Format:%H$'

from qgis.PyQt.QtCore import QTimer
from qgis.PyQt.QtGui import QColor

from qgis import utils as QgsUtils
from qgis.core import QgsProject, QgsCoordinateTransform, QgsFeature
from qgis.gui import QgsHighlight

class  MapCanvasEffects():
    def __init__(self):
        self.project = QgsProject().instance()
        self.canvas = QgsUtils.iface.mapCanvas()
        self.timer = QTimer( self.canvas )
        self.flash = None

    def highlight(self, layer, geometry):
        def getFlash():
            h = QgsHighlight( self.canvas, geometry, layer )
            h.setColor(     QColor( 255, 0, 0, 255 ) )
            h.setFillColor( QColor( 255, 0, 0, 100 ) )
            h.setWidth( 2 )
            return h

        def finished():
            self.timer.stop()
            self.timer.timeout.disconnect( finished )
            del self.flash

        self.flash = getFlash()
        self.timer.timeout.connect( finished )
        self.timer.start( 500 ) # Milliseconds before finishing the flash

    def zoom(self, layer, geometry):
        def getBoudingBoxGeomCanvas():
            crsLayer = layer.crs()
            crsCanvas = self.project.crs()
            if not crsLayer == crsCanvas:
                ct = QgsCoordinateTransform( layer.crs(), self.project.crs(), self.project )
                bbox = ct.transform( geometry.boundingBox() )
            else:
                bbox = geometry.boundingBox()
            return bbox

        self.canvas.setExtent( getBoudingBoxGeomCanvas() )
        self.canvas.zoomByFactor( 1.05 )
        self.canvas.refresh()
        self.highlight( layer, geometry )

    def highlightFeature(self, layer, feature):
        if not feature.hasGeometry():
            return
        geom = feature.geometry()
        self.highlight( layer, geom )

    def zoomFeature(self, layer, feature):
        if not feature.hasGeometry():
            return
        geom = feature.geometry()
        self.zoom( layer, geom )
