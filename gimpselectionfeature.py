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
import os, sys, json, datetime, socket

from os import path

from PyQt4 import ( QtGui, QtCore )
from qgis import ( core as QgsCore, gui as QgsGui )

from osgeo import ( gdal, ogr, osr, gdalconst )

class WorkerGimpSelectionFeature(QtCore.QObject):
  finished = QtCore.pyqtSignal(dict)
  messageStatus = QtCore.pyqtSignal(dict)
  socketnone = QtCore.pyqtSignal()

  def __init__(self):
    super(WorkerGimpSelectionFeature, self).__init__()
    self.isKilled = None
    self.runProcess = self.paramsImage =  None
    self.paramSmooth = self.paramsSieve = self.layerPolygon = None
    self.socket = None
    self.idAdd = 0

  def setDataRun(self, params, nameProcess):
    self.paramsImage = params['paramsImage']
    self.socket = params['socket']
    if 'addFeatures' == nameProcess:
      self.runProcess = self.addFeatures
      self.paramSmooth = params['paramSmooth']
      self.paramsSieve = params['paramsSieve']
      self.layerPolygon = params['layerPolygon']
    elif 'addImageGimp' == nameProcess:
      self.runProcess = self.addImageGimp
    else:
      self.runProcess = None

  def getDataServer(self, nameFunction, filename):
    data = { 'function': nameFunction, 'filename': filename  }
    sdata = json.dumps( data )
    try:
      self.socket.send( sdata )
      sdata = self.socket.recv(4096)
    except socket.error as msg_socket:
      msg = "Error connection GIMP Server: %s. Run IBAMA plugin in GIMP"  % str( msg_socket )
      self.socketnone.emit()
      return { 'isOk': False, 'msg': msg }
    
    if len( sdata ) == 0:
      msg = "Run IBAMA Plugin, 'Tools/IBAMA/Service for save the selected regions', in GIMP!"
      self.socketnone.emit()
      return { 'isOk': False, 'msg': msg }

    return json.loads( sdata )

  def finishedWarning(self, msg):
    typeMsg = QgsGui.QgsMessageBar.WARNING
    if self.isKilled:
      typeMsg = QgsGui.QgsMessageBar.CRITICAL
    self.messageStatus.emit( { 'type': typeMsg, 'msg': msg } )
    self.finished.emit( { 'isOk': False } )

  def addFeatures(self):
    def setGeorefImage():
      ds = gdal.Open( pImgSel['filename'], gdalconst.GA_Update )
      if gdal.GetLastErrorType() != 0:
        return { 'isOk': False, 'msg': gdal.GetLastErrorMsg() }

      xOrigin = yOrigin = None
      if isView:
        xOrigin = self.paramsImage['view']['extent'].xMinimum()
        yOrigin = self.paramsImage['view']['extent'].yMaximum()
      else:
        xOrigin = self.paramsImage['tiePoint'][0]
        yOrigin = self.paramsImage['tiePoint'][1]
      tiePointOrigin = ( xOrigin, yOrigin )

      i = 0
      xIni = tiePointOrigin[i] + pImgSel['tiePoint'][i] * self.paramsImage['res'][i]
      i = 1
      yIni = tiePointOrigin[i] - pImgSel['tiePoint'][i] * self.paramsImage['res'][i]

      transform = ( xIni, self.paramsImage['res'][0], 0.0, yIni, 0.0, -1*self.paramsImage['res'][1] )
      ds.SetGeoTransform( transform )
      ds.SetProjection( self.paramsImage['wktProj'] )

      band = ds.GetRasterBand( 1 )
      band.SetNoDataValue( 0.0 )

      ds = None

      return { 'isOk': True }

    def polygonizeSelectionImage():
      ds_img = gdal.Open( pImgSel['filename'], gdalconst.GA_ReadOnly )
      if gdal.GetLastErrorType() != 0:
        return { 'isOk': False, 'msg': gdal.GetLastErrorMsg() }
      band = ds_img.GetRasterBand( 1 )

      # Sieve Band
      drv = gdal.GetDriverByName('MEM')
      ds_sieve = drv.Create( '', ds_img.RasterXSize, ds_img.RasterYSize,1, band.DataType )
      ds_sieve.SetGeoTransform( ds_img.GetGeoTransform() )
      ds_sieve.SetProjection( self.paramsImage['wktProj'] )
      band_sieve = ds_sieve.GetRasterBand(1)

      p_threshold = self.paramsSieve['threshold']
      p_connectedness = self.paramsSieve['connectedness']
      gdal.SieveFilter( band, None, band_sieve, p_threshold, p_connectedness, [], callback=None )
      ds_img = band = None
      if gdal.GetLastErrorType() != 0:
        return { 'isOk': False, 'msg': gdal.GetLastErrorMsg() }

      # Memory layer - Polygonize
      srs = osr.SpatialReference()
      srs.ImportFromWkt( self.paramsImage['wktProj'] )
      drv_poly = ogr.GetDriverByName('MEMORY')
      ds_poly = drv_poly.CreateDataSource('memData')
      layer_poly = ds_poly.CreateLayer( 'memLayer', srs, ogr.wkbPolygon )
      field = ogr.FieldDefn("dn", ogr.OFTInteger)
      layer_poly.CreateField( field )
      idField = 0

      gdal.Polygonize( band_sieve, None, layer_poly, idField, [], callback=None )
      ds_sieve = band_sieve = None
      if gdal.GetLastErrorType() != 0:
        return { 'isOk': False, 'msg': gdal.GetLastErrorMsg() }

      # Get Geoms
      geoms = []
      layer_poly.SetAttributeFilter("dn = 255")
      for feat in layer_poly:
        geoms.append( feat.GetGeometryRef().Clone() )
      ds_poly = layer_poly = None

      return { 'isOk': True, 'geoms': geoms }

    def addAttribute(feat):
      self.idAdd += 1
      sdatetime = str( datetime.datetime.now() )
      feat.setAttribute('image', self.paramsImage['filename'] )
      feat.setAttribute('datetime', sdatetime )
      feat.setAttribute('crs', self.paramsImage['desc_crs'] )
      feat.setAttribute('id_add', self.idAdd )

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

    self.isKilled = False
    filename = self.paramsImage['filename']
    isView = QtCore.Qt.Checked == self.paramsImage['view']['checkState']
    if isView:
      filename = self.paramsImage['view']['filename']

    msg = "Creating features in QGIS..."
    self.messageStatus.emit( { 'type': QgsGui.QgsMessageBar.INFO, 'msg': msg } )

    pImgSel = self.getDataServer( 'create_selection_image', filename )
    if not pImgSel['isOk']:
      self.finishedWarning( pImgSel['msg'] )
      return
    if self.isKilled:
      self.finishedWarning( "Processing is stopped by user" )
      os.remove( pImgSel['filename'] )
      return
    vreturn = setGeorefImage()
    if not vreturn['isOk']:
      self.finishedWarning( vreturn['msg'] )
      os.remove( pImgSel['filename'] )
      return
    if self.isKilled:
      self.finishedWarning( "Processing is stopped by user" )
      os.remove( pImgSel['filename'] )
      return
    vreturn = polygonizeSelectionImage()
    os.remove( pImgSel['filename'] )
    if not vreturn['isOk']:
      self.finishedWarning( vreturn['msg'] )
      return
    if self.isKilled:
      self.finishedWarning( "Processing is stopped by user" )
      return

    totalFeats = len( vreturn['geoms'] ) 
    if totalFeats  == 0:
      msg = "Not found features in selections ('%s')" % self.paramsImage['filename']
      self.finishedWarning( msg )
      return

    srsLayerPolygon = osr.SpatialReference()
    srsLayerPolygon.ImportFromWkt( self.layerPolygon.crs().toWkt() )

    feat = QgsCore.QgsFeature( self.layerPolygon.dataProvider().fields() )
    addAttribute( feat )

    isIniEditable = self.layerPolygon.isEditable()
    if not isIniEditable:
      self.layerPolygon.startEditing()

    p_iter = self.paramSmooth['iter']
    p_offset = self.paramSmooth['offset']
    envFeats = None # [ xmin, xmax, ymin, ymax ]
    for geom in vreturn['geoms']:
      geom.TransformTo( srsLayerPolygon )
      envFeats = envelopGeoms( envFeats, geom )
      geomLayer = QgsCore.QgsGeometry.fromWkt( geom.ExportToWkt() ).smooth( p_iter, p_offset )
      geom.Destroy()
      feat.setGeometry( geomLayer )
      self.layerPolygon.addFeature( feat )
      del geomLayer

    feat = None
    self.layerPolygon.commitChanges()
    if isIniEditable:
      self.layerPolygon.startEditing()
    self.layerPolygon.updateExtents()

    msg = "Added %d features in '%s'" % ( totalFeats, self.layerPolygon.name() )
    self.messageStatus.emit( { 'type': QgsGui.QgsMessageBar.INFO, 'msg': msg  } )
    bboxFeats = QgsCore.QgsRectangle( envFeats[0], envFeats[2], envFeats[1], envFeats[3] )
    self.finished.emit( { 'isOk': True, 'bboxFeats': bboxFeats } )

  def addImageGimp(self):
    def createViewImage():
      def addGeoInfo():
        ds = gdal.Open( filename, gdalconst.GA_Update )
        ds.SetProjection( self.paramsImage['wktProj'] )
        res = self.paramsImage['res']
        ds.SetGeoTransform( [ p_e.xMinimum(), res[0], 0, p_e.yMaximum(), 0, -1*res[1] ] )
        del ds
        ds = None

      p_e  = self.paramsImage['view']['extent']
      p_w  = self.paramsImage['view']['widthRead']
      p_h  = self.paramsImage['view']['heightRead']
      
      blockImage = self.paramsImage['renderer'].block( 1, p_e, p_w, p_h )
      blockImage.image().save( self.paramsImage['view']['filename'] )
      addGeoInfo()

    def endWarning(msg):
      if isView:
        if path.exists( filename ):
          os.remove( filename )
      self.finishedWarning( msg )
     
    self.isKilled = False
    msg = None
    filename = ""
    isView = QtCore.Qt.Checked == self.paramsImage['view']['checkState']
    if isView:
      filename = self.paramsImage['view']['filename']
      createViewImage()
      msg = "Adding image view'%s' in GIMP..." % filename
    else:
      filename = self.paramsImage['filename']
      msg = "Adding image '%s' in GIMP..." % filename
    self.messageStatus.emit( { 'type': QgsGui.QgsMessageBar.INFO, 'msg': msg } )

    if isView:
      vreturn = self.getDataServer( 'add_image_overwrite', filename )
    else:
      vreturn = self.getDataServer( 'add_image', filename )
    if not vreturn['isOk']:
      endWarning( vreturn['msg'] )
      self.finished.emit( { 'isOk': False } )
      return

    msg = "GIMP: %s" % vreturn['msg']
    self.messageStatus.emit( { 'type': QgsGui.QgsMessageBar.INFO, 'msg': msg } )
    self.finished.emit( { 'isOk': True } )

  @QtCore.pyqtSlot()
  def run(self):
    if self.runProcess is None:
      msg = "ERROR in Script"
      self.messageStatus.emit( { 'type': QgsGui.QgsMessageBar.CRITICAL, 'msg': msg } )
      self.finished.emit( { 'isOk': False } )
      return

    self.runProcess()

class GimpSelectionFeature(QtCore.QObject):
  nameModulus = "GimpSelectionFeature"
  def __init__(self, iface, dockWidgetGui):
    super(GimpSelectionFeature, self).__init__()
    self.dockWidgetGui = dockWidgetGui
    self.paramsImage =  self.last_filename = self.layerPolygon = self.layerImage = self.layerChange = None
    self.thread = self.socket = self.forceStopThread = self.hasConnect = None
    ( self.iface, self.canvas,  self.msgBar ) = ( iface, iface.mapCanvas(), iface.messageBar() )
    self.worker = WorkerGimpSelectionFeature()

    self.initThread()
    self._connect()

    self.setEnabledWidgetAdd( False )
    self.dockWidgetGui.btnStopTransfer.setEnabled( False )
    self.dockWidgetGui.btnSelectImage.setEnabled( False )
    self.dockWidgetGui.chkIsView.setCheckState( QtCore.Qt.Checked )

  def __del__(self):
    if not self.socket is None:
      self.socket.close()
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
      { 'signal': self.worker.messageStatus, 'slot': self.messageStatusWorker },
      { 'signal': self.worker.socketnone, 'slot': self.setSocketNone }
    ]
    if isConnect:
      for item in ss:
        item['signal'].connect( item['slot'] )  
    else:
      for item in ss:
        item['signal'].disconnect( item['slot'] )

  def _connect(self, isConnect = True):
    ss = [
      { 'signal': QgsCore.QgsMapLayerRegistry.instance().layerWillBeRemoved, 'slot': self.removeLayer },
      { 'signal': self.canvas.currentLayerChanged, 'slot': self.setSelectImage },
      { 'signal': self.dockWidgetGui.btnSelectImage.clicked, 'slot': self.setParamsImage },
      { 'signal': self.dockWidgetGui.btnAddImage.clicked, 'slot': self.addImageGimp },
      { 'signal': self.dockWidgetGui.btnAddFeatures.clicked, 'slot': self.addFeatures },
      { 'signal': self.dockWidgetGui.btnStopTransfer.clicked, 'slot': self.stopTransfer },
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
    wgts = [ self.dockWidgetGui.chkIsView,
             self.dockWidgetGui.btnAddImage,
             self.dockWidgetGui.btnAddFeatures,
             self.dockWidgetGui.gbxSettingFeatures
           ]
    map( lambda item: item.setEnabled( isEnabled ), wgts )
    self.dockWidgetGui.btnStopTransfer.setEnabled( not isEnabled )

  def setLabelLayer(self, lblLayer, layer=None):
    text = ""
    tip = ""
    if not layer is None:
      text = layer.name()
      tip = layer.source()
    lblLayer.setText( text )
    lblLayer.setToolTip( tip )

  def setSocket(self):
    if self.socket is None:
      self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      try:
        self.socket.connect( ( '127.0.0.1', 10000) ) # ( IP, port)
      except socket.error, e:
        msg = "Run IBAMA Plugin, 'Tools/IBAMA/Service for save the selected regions', in GIMP!"
        self.socket = None
        return { 'isOk': False, 'msg': msg}
      return { 'isOk': True }

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

    self.dockWidgetGui.lblStatus.clear()

    self.thread.quit()
    if self.worker.isKilled: 
      self.thread.wait()

    self.setEnabledWidgetAdd( True )
    if not data['isOk']:
      self.forceStopThread = False
      return

    if data.has_key('bboxFeats'):
      zoomToBBox( data['bboxFeats'] )
      return
    
  @QtCore.pyqtSlot( dict )
  def messageStatusWorker(self, msgStatus):
    self.msgBar.popWidget()
    self.msgBar.pushMessage( self.nameModulus, msgStatus['msg'], msgStatus['type'], 5 )

  @QtCore.pyqtSlot()
  def setSocketNone(self):
    self.socket = None

  @QtCore.pyqtSlot(str)
  def removeLayer(self, sIdLayer):
    if not self.layerImage is None and self.layerImage.id() == sIdLayer:
      if self.thread.isRunning():
        self.worker.isKilled = True
      if self.paramsImage['view'].has_key('filename'):
        if path.exists( self.paramsImage['view']['filename'] ):
          os.remove( self.paramsImage['view']['filename'] )
      del self.paramsImage
      self.paramsImage = self.layerImage = None
      self.setLabelLayer( self.dockWidgetGui.lblCurImage )
      self.setEnabledWidgetAdd( False )
      self.dockWidgetGui.btnStopTransfer.setEnabled( False )
      return
    if not self.layerChange is None and self.layerChange.id() == sIdLayer:
      self.setSelectImage( None )
      return
    if not self.layerPolygon is None and self.layerPolygon.id() == sIdLayer:
      if self.thread.isRunning():
        self.worker.isKilled = True
      self.layerPolygon = None

  @QtCore.pyqtSlot(QgsCore.QgsMapLayer)
  def setSelectImage(self, layer):
    enabled = False
    if not layer is None and layer.type() == QgsCore.QgsMapLayer.RasterLayer:
      self.setLabelLayer( self.dockWidgetGui.lblSelectImage, layer )
      enabled = True
      self.layerChange = layer
    else:
      self.setLabelLayer( self.dockWidgetGui.lblSelectImage )

    self.dockWidgetGui.btnSelectImage.setEnabled( enabled )

  @QtCore.pyqtSlot()
  def setParamsImage(self):
    if self.layerChange is None:
      return
    if not self.layerChange.dataProvider().crs().isValid():
      self.setLabelLayer( self.dockWidgetGui.lblSelectImage )
      msg = "Invalid CRS of Raster layer '%s'" % self.layerChange.name()
      msgStatus = { 'msg': msg, 'type': QgsGui.QgsMessageBar.WARNING } 
      self.messageStatusWorker( msgStatus )
      self.setLabelLayer( self.dockWidgetGui.lblSelectImage )
      self.layerChange = None
      return

    self.layerImage = self.layerChange
    res = ( self.layerImage.rasterUnitsPerPixelX(), self.layerImage.rasterUnitsPerPixelY() )
    tiePoint = ( self.layerImage.extent().xMinimum(), self.layerImage.extent().yMaximum() )
    crs = self.layerImage.crs()
    if not self.paramsImage is None:
      del self.paramsImage
    self.paramsImage = { 
      'filename': self.layerImage.source(),
      'res': res, 'tiePoint': tiePoint,
      'wktProj': str( crs.toWkt() ),
      'desc_crs': crs.description(),
      'view': { 'checkState': QtCore.Qt.Unchecked },
      'renderer': self.layerImage.renderer()
    }
    self.setLabelLayer( self.dockWidgetGui.lblCurImage, self.layerImage )
    self.setEnabledWidgetAdd( True )

  @QtCore.pyqtSlot()
  def addImageGimp(self):
    def setParamsImageView():
      def getIniCoord( cMinLayer, cPoint, res ):
        return int( ( cPoint - cMinLayer ) / res ) * res + cMinLayer

      def getEndCoord( cMaxLayer, cPoint, res ):
        return cMaxLayer - ( int( ( cMaxLayer - cPoint ) / res ) * res )

      mapSettings = self.canvas.mapSettings()
      crsCanvas = mapSettings.destinationCrs()
      extentCanvas = self.canvas.extent()

      if self.layerImage.crs() != crsCanvas:
        extentCanvas = mapSettings.mapToLayerCoordinates( self.layerImage, extentCanvas )

      extentLayer = self.layerImage.extent()
      if not extentCanvas.intersects( extentLayer ):
        msg = "View not intersects Raster '%s'" % self.layerImage.name()
        return { 'isOk': False, 'msg': msg }
      if extentCanvas == extentLayer or extentCanvas.contains( extentLayer):
        msg = "View has all raster '%s'" % self.layerImage.name()
        return { 'isOk': False, 'msg': msg }

      extent = extentCanvas.intersect( extentLayer )

      ( resX, resY ) = ( self.paramsImage['res'][0], self.paramsImage['res'][1] )
      iniX = getIniCoord( self.layerImage.extent().xMinimum(), extent.xMinimum(), resX )
      iniY = getIniCoord( self.layerImage.extent().yMinimum(), extent.yMinimum(), resY )
      endX = getEndCoord( self.layerImage.extent().xMaximum(), extent.xMaximum(), resX )
      endY = getEndCoord( self.layerImage.extent().yMaximum(), extent.yMaximum(), resY )

      extent.set( iniX,iniY, endX, endY  )
      widthRead  = int( extent.width()  / resX )
      heightRead = int( extent.height() / resY )

      sf = '_view'
      filename = path.splitext( self.paramsImage['filename'] )[0]
      filename = "%s%s.tif" % ( filename, sf )

      self.paramsImage['view']['filename']   = filename
      self.paramsImage['view']['extent']     = extent
      self.paramsImage['view']['widthRead']  = widthRead
      self.paramsImage['view']['heightRead'] = heightRead

      return { 'isOk': True }

    if self.paramsImage is None:
      return

    if self.socket is None:
      vreturn = self.setSocket()
      if not vreturn['isOk']:
        msgStatus = { 'msg': vreturn['msg'], 'type': QgsGui.QgsMessageBar.WARNING } 
        self.messageStatusWorker( msgStatus )
        return

    if self.last_filename is None:
       self.last_filename = self.paramsImage['filename']
    else:
      if self.last_filename == self.paramsImage['filename']:
        value = QtGui.QMessageBox.question( self.dockWidgetGui,
                                            self.nameModulus, "Confirm add image in GIMP?",
                                            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No )
        if QtGui.QMessageBox.Yes == value:
          self.last_filename = self.paramsImage['filename']
        else:
          return

    checkState = self.dockWidgetGui.chkIsView.checkState()
    self.paramsImage['view']['checkState'] = checkState
    if QtCore.Qt.Checked == checkState:
      vreturn = setParamsImageView()
      if not vreturn['isOk']:
        self.messageStatusWorker( { 'msg': vreturn['msg'], 'type': QgsGui.QgsMessageBar.WARNING } )
        return

    self.dockWidgetGui.lblStatus.setText( "Add image..." )
    self.setEnabledWidgetAdd( False )

    params = { 'paramsImage': self.paramsImage, 'socket': self.socket }
    self.worker.setDataRun( params,  'addImageGimp')
    self.thread.start()
    #self.worker.run() # QtCore.qDebug("DEBUG 1")

  @QtCore.pyqtSlot()
  def addFeatures(self):
    def createLayerPolygon():
      atts = [ "id_add:integer", "image:string(200)", "datetime:string(20)", "crs:string(100)" ]
      l_fields = map( lambda item: "field=%s" % item, atts  )
      l_fields.insert( 0, "crs=epsg:4326" )
      l_fields.append( "index=yes" )
      s_fields = '&'.join( l_fields )
      self.layerPolygon =  QgsCore.QgsVectorLayer( "Polygon?%s" % s_fields, "gimp_selection_polygon", "memory")
      QgsCore.QgsMapLayerRegistry.instance().addMapLayer( self.layerPolygon )
      self.layerPolygon.loadNamedStyle( os.path.join( os.path.dirname( __file__ ), "gimpselectionfeature.qml" ) )
      self.iface.legendInterface().refreshLayerSymbology( self.layerPolygon )

    if self.paramsImage is None:
      return

    if self.socket is None:
      vreturn = self.setSocket()
      if not vreturn['isOk']:
        msgStatus = { 'msg': vreturn['msg'], 'type': QgsGui.QgsMessageBar.WARNING } 
        self.messageStatusWorker( msgStatus )
        return

    checkState = self.dockWidgetGui.chkIsView.checkState()
    self.paramsImage['view']['checkState'] = checkState
    if QtCore.Qt.Checked == checkState:
      if not self.paramsImage['view'].has_key('filename'):
        msg = "Image view not found. Add image view"
        self.messageStatusWorker( { 'msg': msg, 'type': QgsGui.QgsMessageBar.WARNING } )
        return
      filename = self.paramsImage['view']['filename']
      if not path.exists( filename ):
        msg = "Image view'%s' not found. Add image view again" % filename
        self.messageStatusWorker( { 'msg': msg, 'type': QgsGui.QgsMessageBar.WARNING } )
        return

    self.dockWidgetGui.lblStatus.setText( "Add features..." )
    self.setEnabledWidgetAdd( False )

    if self.layerPolygon is None:
      createLayerPolygon()

    # paramSmooth: iter = interations, offset = 0.0 - 1.0(100%)
    # paramsSieve: threshold = Size in Pixel, connectedness = 4 or 8(diagonal)
    threshold = self.dockWidgetGui.sbSieveThreshold.value() + 1
    offset = self.dockWidgetGui.spSmoothOffset.value() / 100.0
    vinter = self.dockWidgetGui.sbSmoothIteration.value()

    params = {
      'paramsImage': self.paramsImage,
      'socket': self.socket,
      'paramSmooth': { 'iter': vinter, 'offset': offset },
      'paramsSieve': { 'threshold': threshold, 'connectedness': 4 },
      'layerPolygon': self.layerPolygon
    }
    self.worker.setDataRun( params, 'addFeatures' )
    self.thread.start()
    #self.worker.run() # QtCore.qDebug("DEBUG 1")

  @QtCore.pyqtSlot()
  def stopTransfer(self):
    def forceStop():
      if self.forceStopThread:
        self.finishThread()
        self.initThread()

    self.dockWidgetGui.lblStatus.setText( "Stop..." )
    if self.thread.isRunning():
      self.forceStopThread = True
      self.worker.isKilled = True
      QtCore.QTimer.singleShot( 500, forceStop )

class DockWidgetGimpSelectionFeature(QtGui.QDockWidget):
  def __init__(self, iface):
    def setupUi():
      def getLayout(parent, widgets):
        lyt = QtGui.QGridLayout( parent )
        for item in widgets:
          if item.has_key('spam'):
            sRow, sCol = item['spam']['row'], item['spam']['col']
            lyt.addWidget( item['widget'], item['row'], item['col'], sRow, sCol, QtCore.Qt.AlignLeft )
          else:
            lyt.addWidget( item['widget'], item['row'], item['col'], QtCore.Qt.AlignLeft )
        return lyt

      def getGroupBox(name, parent, widgets):
        lyt = getLayout( parent, widgets )
        gbx = QtGui.QGroupBox(name, parent )
        gbx.setLayout( lyt )
        return gbx

      def getSpinBoxOffset(wgt, value):
        sp = QtGui.QDoubleSpinBox( wgt)
        sp.setRange(0.0, 50.0)
        sp.setSingleStep(12.5)
        sp.setDecimals(2)
        sp.setSuffix(' %')
        sp.setValue(value)
        return sp

      def getSpinBoxSieve(wgt, value):
        sp = QtGui.QSpinBox( wgt)
        sp.setMinimum(0.0)
        sp.setSingleStep(1)
        sp.setSuffix(' pixels')
        sp.setValue(value)
        return sp

      def getSpinBoxIteration(wgt, value):
        sp = QtGui.QSpinBox( wgt)
        sp.setRange(0, 3)
        sp.setSingleStep(1)
        sp.setValue(value)
        return sp

      def getLineEditInteger(wgt, value):
        le = QtGui.QLineEdit( wgt )
        validator = QtGui.QIntValidator( wgt )
        le.setValidator( validator )
        le.setText( str(value) )
        return le

      self.setObjectName( "gimpselectionfeature_dockwidget" )
      wgt = QtGui.QWidget( self )
      wgt.setAttribute(QtCore.Qt.WA_DeleteOnClose)
      # Image
      self.lblCurImage = QtGui.QLabel("", wgt )
      self.btnSelectImage = QtGui.QPushButton("Set the layer below how current:", wgt )
      self.lblSelectImage = QtGui.QLabel("Select image in legend", wgt )
      l_wts = [
        { 'widget': QtGui.QLabel("Current:", wgt ), 'row': 0, 'col': 0 },
        { 'widget': self.lblCurImage,               'row': 1, 'col': 0 },
        { 'widget': self.btnSelectImage,            'row': 2, 'col': 0 },
        { 'widget': self.lblSelectImage,            'row': 3, 'col': 0 }
      ]
      gbxImage = getGroupBox( "Image", wgt, l_wts)
      # Transfer
      self.chkIsView = QtGui.QCheckBox("Image view", wgt)
      self.btnAddImage = QtGui.QPushButton("Add image", wgt )
      self.btnAddFeatures = QtGui.QPushButton("Add features", wgt )
      self.sbSieveThreshold = getSpinBoxSieve( wgt, 5 )
      self.spSmoothOffset = getSpinBoxOffset( wgt, 25 )
      self.sbSmoothIteration  = getSpinBoxIteration( wgt, 1)
      self.btnStopTransfer = QtGui.QPushButton("Stop transfer", wgt )
      self.lblStatus = QtGui.QLabel("", wgt )
      l_wts = [
        { 'widget': QtGui.QLabel("Level(0-3):", wgt ),             'row': 0, 'col': 0 },
        { 'widget': self.sbSmoothIteration,                        'row': 0, 'col': 1 },
        { 'widget': QtGui.QLabel("Fraction of line(0-50):", wgt ), 'row': 1, 'col': 0 },
        { 'widget': self.spSmoothOffset,                           'row': 1, 'col': 1 }
      ]
      gbxSmooth = getGroupBox( "Smooth", wgt, l_wts)
      spamSmooth = { 'row': 1, 'col': 2 }
      l_wts = [
        { 'widget': QtGui.QLabel("Remove area:", wgt ), 'row': 0, 'col': 0 },
        { 'widget': self.sbSieveThreshold,              'row': 0, 'col': 1 },
        { 'widget': gbxSmooth,                          'row': 1, 'col': 0, 'spam': spamSmooth }
      ]
      self.gbxSettingFeatures = getGroupBox( "Setting", wgt, l_wts)
      l_wts = [
        { 'widget': self.btnAddFeatures,     'row': 0, 'col': 0 },
        { 'widget': self.gbxSettingFeatures, 'row': 1, 'col': 0 }
      ]
      gbxGQ = getGroupBox( "GIMP->QGIS", wgt, l_wts)
      l_wts = [
        { 'widget': self.btnAddImage,        'row': 0, 'col': 0 }
      ]
      gbxQG = getGroupBox( "QGIS->GIMP", wgt, l_wts)
      l_wts = [
        { 'widget': self.chkIsView,       'row': 0, 'col': 0 },
        { 'widget': gbxQG,                'row': 1, 'col': 0 },
        { 'widget': gbxGQ,                'row': 2, 'col': 0 },
        { 'widget': self.btnStopTransfer, 'row': 3, 'col': 0 }
      ]
      gbxTransfer = getGroupBox( "Transfer", wgt, l_wts)
      #
      l_wts = [
        { 'widget': gbxImage,       'row': 0, 'col': 0 },
        { 'widget': gbxTransfer,    'row': 1, 'col': 0 },
        { 'widget': self.lblStatus, 'row': 2, 'col': 0 }
      ]
      lyt = getLayout( wgt, l_wts )
      wgt.setLayout( lyt)
      self.setWidget( wgt )

    super( DockWidgetGimpSelectionFeature, self ).__init__( "Gimp Selection Feature", iface.mainWindow() )
    #
    setupUi()
    self.gsf = GimpSelectionFeature( iface, self )

  def __del__(self):
    del self.gsf
