# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : Gimp Selection Feature
Description          : Plugin for adding selected area in GIMP how a feature in memory layer
Date                 : June, 2016
copyright            : (C) 2016 by Luiz Motta
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
import os, sys, dbus, json, datetime
from os import path

from PyQt4 import ( QtGui, QtCore )
from qgis import ( core as QgsCore, gui as QgsGui )

from osgeo import ( gdal, ogr, osr )
from gdalconst import ( GA_ReadOnly, GA_Update )

class WorkerGimpSelectionFeature(QtCore.QObject):
  finished = QtCore.pyqtSignal(dict)
  messageStatus = QtCore.pyqtSignal(dict)

  def __init__(self, session_bus, name_bus):
    super(WorkerGimpSelectionFeature, self).__init__()
    self.isKilled = None
    self.runProcess = self.paramsImage = self.layerPolygon = None    
    #
    ( self.session_bus, self.name_bus ) = ( session_bus, name_bus )
    #
    self.idbus = self.proxyDBus = None

  def __del__(self):
    if not self.idbus is None:
      self.idbus.quit()

  def setDataRun(self, paramsImage, layerPolygon, nameProcess):
    ( self.paramsImage, self.layerPolygon ) = ( paramsImage, layerPolygon ) 
    if nameProcess == 'addFeatures':
      self.runProcess = self.addFeatures
    elif nameProcess == 'addImageGimp':
      self.runProcess = self.addImageGimp

  def setInterfaceDBus(self):
    if not self.name_bus['uri'] in self.session_bus.list_names():
      return { 'isOk': False, 'msg': "Active 'Selection save image Server' in Gimp Plugin!" }

    if self.idbus is None:
      del self.idbus
      del self.proxyDBus
    self.proxyDBus = self.session_bus.get_object( self.name_bus['uri'], self.name_bus['path'] )
    self.idbus = dbus.Interface( self.proxyDBus, self.name_bus['uri'] )

    return { 'isOk': True }

  def finishedWarnig(self, msg):
    self.messageStatus.emit( { 'type': QgsGui.QgsMessageBar.WARNING, 'msg': msg } )
    self.finished.emit( { 'isOk': False } )

  def addFeatures(self):
    def setGeorefImage():
      ds = gdal.Open( pImgSel['filename'], GA_Update )
      if gdal.GetLastErrorType() != 0:
        return { 'isOk': False, 'msg': gdal.GetLastErrorMsg() }
      #
      i = 0
      xIni = self.paramsImage['tiePoint'][i] + pImgSel['tiePoint'][i] * self.paramsImage['res'][i]
      i = 1
      yIni = self.paramsImage['tiePoint'][i] + pImgSel['tiePoint'][i] * self.paramsImage['res'][i]
      #
      transform = ( xIni, self.paramsImage['res'][0], 0.0, yIni, 0.0, self.paramsImage['res'][1] )
      ds.SetGeoTransform( transform )
      ds.SetProjection( self.paramsImage['wktProj'] )
      #
      band = ds.GetRasterBand( 1 )
      band.SetNoDataValue( 0.0 )
      #
      ds = None

      return { 'isOk': True }

    def polygonizeSelectionImage():
      ds_img = gdal.Open( pImgSel['filename'], GA_ReadOnly )
      if gdal.GetLastErrorType() != 0:
        return { 'isOk': False, 'msg': gdal.GetLastErrorMsg() }
      band = ds_img.GetRasterBand( 1 )

      # Memory layer - Polygonize
      srs = osr.SpatialReference()
      srs.ImportFromWkt( self.paramsImage['wktProj'] )
      drv = ogr.GetDriverByName('MEMORY')
      ds = drv.CreateDataSource('memData')
      layer = ds.CreateLayer( 'memLayer', srs, ogr.wkbPolygon )
      field = ogr.FieldDefn("dn", ogr.OFTInteger)
      layer.CreateField( field )
      idField = 0

      gdal.Polygonize( band, None, layer, idField, [], callback=None )
      if gdal.GetLastErrorType() != 0:
        return { 'isOk': False, 'msg': gdal.GetLastErrorMsg() }

      ds_img = band = None

      # Get Geoms
      geoms = []
      layer.SetAttributeFilter("dn = 255")
      for feat in layer:
        geoms.append( feat.GetGeometryRef().Clone() )

      return { 'isOk': True, 'geoms': geoms }

    def addAttribute(feat):
      sdatetime = datetime.datetime.now().strftime( "%Y-%m-%d %H:%M:%s")
      feat.setAttribute('image', self.paramsImage['filename'] )
      feat.setAttribute('datetime', sdatetime )
      feat.setAttribute('crs', self.paramsImage['desc_crs'] )

    def envelopGeoms(envFeats, geom):
      env = list( geom.GetEnvelope() ) #  [ xmin, xmax, ymin, ymax ]
      if envFeats is None:
        return env

      for id in ( 0, 2 ): # Min
        if envFeats[id] > env[id]:
          envFeats[id] = env[id]
      for id in ( 1, 3 ): # Max
        if envFeats[id] < env[id]:
          envFeats[id] = env[id]

      return envFeats

    vreturn = self.setInterfaceDBus()
    if not vreturn['isOk']:
      self.finishedWarnig( vreturn['msg'] )
      return

    msg = "Creating features in QGIS..."
    self.messageStatus.emit( { 'type': QgsGui.QgsMessageBar.INFO, 'msg': msg } )
    pImgSel = json.loads( str( self.idbus.create_selection_image( self.paramsImage['filename'] ) ) )
    if not pImgSel['isOk']:
      self.finishedWarnig( pImgSel['msg'] )
      return
    vreturn = setGeorefImage()
    if not vreturn['isOk']:
      self.finishedWarnig( vreturn['msg'] )
      return
    vreturn = polygonizeSelectionImage()
    if not vreturn['isOk']:
      self.finishedWarnig( vreturn['msg'] )
      return

    totalFeats = len( vreturn['geoms'] ) 
    if totalFeats  == 0:
      msg = "Not found features in selections ('%s')" % self.paramsImage['filename']
      self.finishedWarnig( msg )
      return

    srsLayerPolygon = osr.SpatialReference()
    srsLayerPolygon.ImportFromWkt( self.layerPolygon.crs().toWkt() )

    feat = QgsCore.QgsFeature( self.layerPolygon.pendingFields() )
    addAttribute( feat )

    isIniEditable = self.layerPolygon.isEditable()
    if not isIniEditable:
      self.layerPolygon.startEditing()

    envFeats = None # [ xmin, xmax, ymin, ymax ]
    tolerance = 1 # Pixels ??
    totErrorGeom = 0
    for geom in vreturn['geoms']:
      #geomSmoot = geom.ConvexHull()
      #geomSmoot = geom.DelaunayTriangulation( tolerance ) # Not exist
      geomSmoot = geom.SimplifyPreserveTopology( tolerance )
      if geomSmoot is None:
        totErrorGeom += 1
        geom.Destroy()
        continue
      geom.Destroy()
      geomSmoot.TransformTo( srsLayerPolygon )
      envFeats = envelopGeoms( envFeats, geomSmoot )
      geomLayer = QgsCore.QgsGeometry.fromWkt( geomSmoot.ExportToWkt() )
      geomSmoot.Destroy()
      feat.setGeometry( geomLayer )
      self.layerPolygon.addFeature( feat )
      del geomLayer

    feat = None
    self.layerPolygon.commitChanges()
    if isIniEditable:
      self.layerPolygon.startEditing()
    self.layerPolygon.updateExtents()

    msg = "Added %d features in '%s'" % ( totalFeats, self.layerPolygon.name() )
    typMsg = QgsGui.QgsMessageBar.INFO
    if totErrorGeom > 0:
      msg = "Added %d features in '%s' (%d selection with missing geoemtry)" % ( totalFeats, self.layerPolygon.name() )
      typMsg = QgsGui.QgsMessageBar.WARNING
    self.messageStatus.emit( { 'type': typMsg, 'msg': msg  } )
    bboxFeats = QgsCore.QgsRectangle( envFeats[0], envFeats[2], envFeats[1], envFeats[3] )
    self.finished.emit( { 'isOk': True, 'bboxFeats': bboxFeats } )

  def addImageGimp(self):
    vreturn = self.setInterfaceDBus()
    if not vreturn['isOk']:
      self.finishedWarnig( vreturn['msg'] )
      return

    msg = "Adding image '%s' in GIMP..." % self.paramsImage['filename']
    self.messageStatus.emit( { 'type': QgsGui.QgsMessageBar.INFO, 'msg': msg } )
    vreturn = json.loads( str( self.idbus.add_image( self.paramsImage['filename'] ) ) )
    if not vreturn['isOk']:
      self.finishedWarnig( vreturn['msg'] )
      return

    msg = "GIMP: %s" % vreturn['msg']
    self.messageStatus.emit( { 'type': QgsGui.QgsMessageBar.INFO, 'msg': msg } )
    self.finished.emit( { 'isOk': True } )

  @QtCore.pyqtSlot()
  def run(self):
    self.runProcess()

class GimpSelectionFeature(QtCore.QObject):
  def __init__(self, iface, dockWidgetGui):
    super(GimpSelectionFeature, self).__init__()
    self.dockWidgetGui = dockWidgetGui
    self.setEnabledWidgetAdd( False )
    dockWidgetGui['stopProcess'].setEnabled( False )
    #
    self.paramsImage =  self.layerPolygon = self.thread = self.hasConnect = None
    #
    self.nameModulus = "GimpSelectionFeature"
    ( self.iface, self.canvas,  self.msgBar ) = ( iface, iface.mapCanvas(), iface.messageBar() )
    self.session_bus = dbus.SessionBus()
    uri = "gimp.plugin.dbus.selection"
    name_bus = { 'uri': uri, 'path': "/%s" % uri.replace( '.', '/' ) }
    self.worker = WorkerGimpSelectionFeature( self.session_bus, name_bus )
    #
    self.initThread()
    self._connect()

  def createLayerPolygon(self):
    l_fields = map( lambda item: "field=%s" % item, [ "image:string(200)", "datetime:string(20)", "crs:string(100)" ] )
    l_fields.insert( 0, "crs=epsg:4326" )
    l_fields.append( "index=yes" )
    s_fields = '&'.join( l_fields )
    self.layerPolygon =  QgsCore.QgsVectorLayer( "Polygon?%s" % s_fields, "gimp_polygon", "memory")
    QgsCore.QgsMapLayerRegistry.instance().addMapLayer( self.layerPolygon )

  def __del__(self):
    self.session_bus.close()
    self.finishThread()
    if not self.hasConnect:
      self._connect( False )

  def initThread(self):
    self.thread = QtCore.QThread( self )
    self.thread.setObjectName( self.nameModulus )
    self.worker.moveToThread( self.thread )
    self._connectWorker()

  def finishThread(self):
    self._connectWorker( False )
    self.worker.deleteLater()
    self.thread.wait()
    self.thread.deleteLater()
    self.thread = self.worker = None

  def _connectWorker(self, isConnect = True):
    ss = [
      { 'signal': self.thread.started, 'slot': self.worker.run },
      { 'signal': self.worker.finished, 'slot': self.finishedWorker },
      { 'signal': self.worker.messageStatus, 'slot': self.messageStatusWorker }
    ]
    if isConnect:
      for item in ss:
        item['signal'].connect( item['slot'] )  
    else:
      for item in ss:
        item['signal'].disconnect( item['slot'] )

  def _connect(self, isConnect = True):
    ss = [
      { 'signal': self.canvas.currentLayerChanged, 'slot': self.setParamsImage },
      { 'signal': QgsCore.QgsMapLayerRegistry.instance().layerWillBeRemoved, 'slot': self.removeLayer },
      { 'signal': self.dockWidgetGui['addFeatures'].clicked, 'slot': self.addFeature },
      { 'signal': self.dockWidgetGui['addImageGimp'].clicked, 'slot': self.addImageGimp },
      { 'signal': self.dockWidgetGui['stopProcess'].clicked, 'slot': self.stopProcess },
    ]
    if isConnect:
      self.hasConnect = True
      for item in ss:
        item['signal'].connect( item['slot'] )  
    else:
      self.hasConnect = False
      for item in ss:
        item['signal'].disconnect( item['slot'] )

  def setEnabledWidgetAdd( self, isEnabled ):
    self.dockWidgetGui['addFeatures'].setEnabled( isEnabled )
    self.dockWidgetGui['addImageGimp'].setEnabled( isEnabled )
    self.dockWidgetGui['stopProcess'].setEnabled( not isEnabled )

  def setEndProcess(self):
    self.setEnabledWidgetAdd( True )
    self.dockWidgetGui['status'].setText( self.paramsImage['layername'] )

  @QtCore.pyqtSlot(dict)
  def finishedWorker(self, data):
    def zoomToBBox(bboxFeats):
      def highlight():
        def removeRB():
          rb.reset( True )
          self.canvas.scene().removeItem( rb )

        rb = QgsGui.QgsRubberBand( self.canvas, QgsCore.QGis.Polygon)
        rb.setBorderColor( QtGui.QColor( 255,  0, 0 ) )
        rb.setWidth( 2 )
        rb.setToGeometry( QgsCore.QgsGeometry.fromRect( extent ), None )
        QtCore.QTimer.singleShot( 2000, removeRB )

      crsCanvas = self.canvas.mapSettings().destinationCrs()
      ct = QgsCore.QgsCoordinateTransform( self.layerPolygon.crs(), crsCanvas )
      extent = ct.transform( bboxFeats )
      self.canvas.setExtent( extent )
      self.canvas.zoomByFactor( 1.05 )
      self.canvas.refresh()
      highlight()

    self.thread.quit()
    if self.worker.isKilled: 
      self.thread.wait()
    if data['isOk'] and data.has_key('bboxFeats'):
      zoomToBBox( data['bboxFeats'] )

  @QtCore.pyqtSlot( dict )
  def messageStatusWorker(self, msgStatus):
    self.msgBar.popWidget()
    self.msgBar.pushMessage( self.nameModulus, msgStatus['msg'], msgStatus['type'], 5 )

  @QtCore.pyqtSlot(QgsCore.QgsMapLayer)
  def setParamsImage(self, layer):
    if layer is None or not layer.type() == QgsCore.QgsMapLayer.RasterLayer:
      return

    res = ( layer.rasterUnitsPerPixelX(), -1 * layer.rasterUnitsPerPixelY() )
    tiePoint = ( layer.extent().xMinimum(), layer.extent().yMaximum() )
    crs = layer.crs()
    self.paramsImage = { 
      'filename': layer.source(),
      'layername': layer.name(),
      'sIdLayer': layer.id(),
      'res': res, 'tiePoint': tiePoint,
      'wktProj': str( crs.toWkt() ), 'desc_crs': crs.description()
    }
    msg = "Image '%s' actived " % self.paramsImage['filename']
    self.msgBar.popWidget()
    self.msgBar.pushMessage( self.nameModulus, msg, QgsGui.QgsMessageBar.INFO, 5 )
    #
    self.setEndProcess()

  @QtCore.pyqtSlot(str)
  def removeLayer(self, sIdLayer):
    if not self.paramsImage is None and self.paramsImage['sIdLayer'] == sIdLayer:
      if self.thread.isRunning():
        self.worker.isKilled = True

      del self.paramsImage
      self.paramsImage = None
      self.setEnabledWidgetAdd( False )
      self.dockWidgetGui['stopProcess'].setEnabled( False )
      self.dockWidgetGui['status'].setText( "" )
      #
      return

    if not self.layerPolygon is None and self.layerPolygon.id() == sIdLayer:
      if self.thread.isRunning():
        self.worker.isKilled = True

      self.layerPolygon = None

  @QtCore.pyqtSlot()
  def addFeature(self):
    if self.paramsImage is None:
      return

    self.dockWidgetGui['status'].setText( "Add features..." )
    self.setEnabledWidgetAdd( False )

    if self.layerPolygon is None:
      self.createLayerPolygon()

    self.worker.setDataRun( self.paramsImage, self.layerPolygon, 'addFeatures' )
    self.thread.start()
    #self.worker.addFeatures() # DEBUG

    self.setEndProcess()

  @QtCore.pyqtSlot()
  def addImageGimp(self):
    if self.paramsImage is None:
      return

    self.dockWidgetGui['status'].setText( "Add image..." )
    self.setEnabledWidgetAdd( False )

    self.worker.setDataRun( self.paramsImage, self.layerPolygon,  'addImageGimp')
    self.thread.start()
    #self.worker.addImageGimp() # DEBUG

    self.setEndProcess()

  @QtCore.pyqtSlot()
  def stopProcess(self):
    self.dockWidgetGui['status'].setText( "Stop..." )
    if self.thread.isRunning():
      self.worker.isKilled = True
    msg = "Image '%s' actived " % self.paramsImage['filename']
    self.dockWidgetGui['status'].setText( self.paramsImage['layername'] )

class DockWidgetGimpSelectionFeature(QtGui.QDockWidget):
  def __init__(self, iface):
    def setupUi():
      self.setObjectName( "gimpselectionfeature_dockwidget" )
      wgt = QtGui.QWidget( self )
      wgt.setAttribute(QtCore.Qt.WA_DeleteOnClose)
      #
      gridLayout = QtGui.QGridLayout( wgt )
      gridLayout.setContentsMargins( 0, 0, gridLayout.verticalSpacing(), gridLayout.verticalSpacing() )
      #
      ( iniY, iniX, spanY, spanX ) = ( 0, 0, 1, 1 )
      self.addFeatures = QtGui.QPushButton( "Add features", wgt )
      self.addFeatures.setToolTip( "Add features from GIMP" )
      gridLayout.addWidget( self.addFeatures, iniY, iniX, spanY, spanX )
      #
      iniY += 1
      self.addImageGimp = QtGui.QPushButton( "Add image", wgt )
      self.addImageGimp.setToolTip( "Add current image to GIMP" )
      gridLayout.addWidget( self.addImageGimp, iniY, iniX, spanY, spanX )
      #
      iniY += 1
      self.stopProcess = QtGui.QPushButton( "Stop", wgt )
      self.stopProcess.setToolTip( "Stop current process" )
      gridLayout.addWidget( self.stopProcess, iniY, iniX, spanY, spanX )
      #
      iniY += 1
      self.status = QtGui.QLabel( "", wgt )
      self.status.setToolTip( "Current image for GIMP" )
      gridLayout.addWidget( self.status, iniY, iniX, spanY, spanX )
      #
      wgt.setLayout( gridLayout )
      self.setWidget( wgt )

    super( DockWidgetGimpSelectionFeature, self ).__init__( "Gimp Selection Feature", iface.mainWindow() )
    #
    setupUi()
    self.dockWidgetGui = {
      'addFeatures': self.addFeatures, 'addImageGimp': self.addImageGimp, 'stopProcess': self.stopProcess,
      'status': self.status
    }
    self.gsf = GimpSelectionFeature( iface, self.dockWidgetGui )

  def __del__(self):
    del self.gsf
