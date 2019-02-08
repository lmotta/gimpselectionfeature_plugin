# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : Gimp Selection Feature
Description          : Plugin for adding selected area in GIMP how a feature in shapefile layer
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

__author__ = 'Luiz Motta'
__date__ = '2016-06-16'
__copyright__ = '(C) 2018, Luiz Motta'
__revision__ = '$Format:%H$'


import os, sys, json, datetime, socket, math

from os import path

from qgis.PyQt.QtCore import (
  Qt, QVariant, QObject, QCoreApplication, QTimer, 
  pyqtSlot, pyqtSignal
)
from qgis.PyQt.QtGui import QImage, QColor, QIntValidator
from qgis.PyQt.QtWidgets import (
  QMessageBox, QDockWidget, QLayout, QGridLayout, QGroupBox, QDoubleSpinBox,
  QSpinBox, QLineEdit, QWidget, QLabel, QPushButton, QLineEdit, QCheckBox
)
from qgis.core import (
  QgsApplication, QgsProject, Qgis, QgsMapSettings,
  QgsMapRendererParallelJob, QgsTask,
  QgsMapLayer, QgsVectorLayer, QgsVectorFileWriter, QgsFeatureRequest,
  QgsFeature, QgsField, QgsFields, QgsExpression, QgsGeometry, QgsRectangle, QgsWkbTypes,
  QgsCoordinateTransform, QgsCoordinateReferenceSystem 
)
from qgis.gui import QgsRubberBand
from qgis import utils as QgsUtils

from osgeo import gdal, ogr, osr

from .json2html import getHtmlTreeMetadata


class DockWidgetGimpSelectionFeature(QDockWidget):
  def __init__(self, iface):
    def setupUi():
      def getLayout(parent, widgets):
        lyt = QGridLayout( parent )
        for item in widgets:
          if 'spam' in item:
            sRow, sCol = item['spam']['row'], item['spam']['col']
            lyt.addWidget( item['widget'], item['row'], item['col'], sRow, sCol, Qt.AlignLeft )
          else:
            lyt.addWidget( item['widget'], item['row'], item['col'], Qt.AlignLeft )
        return lyt

      def getGroupBox(name, parent, widgets):
        lyt = getLayout( parent, widgets )
        gbx = QGroupBox(name, parent )
        gbx.setLayout( lyt )
        return gbx

      def getSpinBoxOffset(wgt, value):
        sp = QDoubleSpinBox( wgt)
        sp.setRange(0.0, 50.0)
        sp.setSingleStep(12.5)
        sp.setDecimals(2)
        sp.setSuffix(' %')
        sp.setValue(value)
        return sp

      def getSpinBoxSieve(wgt, value):
        sp = QSpinBox( wgt)
        sp.setRange(0, 200)
        sp.setSingleStep(1)
        sp.setSuffix(' pixels')
        sp.setValue(value)
        return sp

      def getSpinBoxAzimuth(wgt, value):
        sp = QSpinBox( wgt)
        sp.setRange(0, 45)
        sp.setSingleStep(1)
        sp.setSuffix(' degrees')
        sp.setValue(value)
        msg = QCoreApplication.translate('GimpSelectionFeature', 'Degrees of azimuth between vertexs')
        sp.setToolTip( msg )
        return sp

      def getSpinBoxIteration(wgt, value):
        sp = QSpinBox( wgt)
        sp.setRange(0, 3)
        sp.setSingleStep(1)
        sp.setValue(value)
        return sp

      self.setObjectName('gimpselectionfeature_dockwidget')
      wgt = QWidget( self )
      wgt.setAttribute(Qt.WA_DeleteOnClose)
      # Image
      width = 180
      self.lblLegendImages = QLabel('', wgt )
      self.lblLegendImages.setWordWrap( True )
      self.lblLegendImages.setMaximumWidth(width )
      l_wts = [ { 'widget': self.lblLegendImages,     'row': 0, 'col': 0 } ]
      name = self.formatTitleImages.format(0)
      self.gbxImage = getGroupBox(name, wgt, l_wts)
      # Transfer
      msg = QCoreApplication.translate('GimpSelectionFeature', 'Send image')
      self.btnSendImage = QPushButton(msg, wgt )
      #
      msg = QCoreApplication.translate('GimpSelectionFeature', 'Get features')
      self.btnGetFeatures = QPushButton( msg, wgt )
      msg = QCoreApplication.translate('GimpSelectionFeature', 'Remove last features')
      self.btnRemoveLastFeatures = QPushButton( msg, wgt )
      #
      self.leditAnnotation = QLineEdit( wgt )
      self.sbSieveThreshold = getSpinBoxSieve( wgt, 5 )
      self.sbAzimuthThreshold = getSpinBoxAzimuth( wgt, 0 )
      self.spSmoothOffset = getSpinBoxOffset( wgt, 25 )
      self.sbSmoothIteration  = getSpinBoxIteration( wgt, 1)
      msgLevel = QCoreApplication.translate('GimpSelectionFeature','Level(0-3):')
      msgFraction = QCoreApplication.translate('GimpSelectionFeature','Fraction of line(0-50):')
      l_wts = [
        { 'widget': QLabel( msgLevel, wgt ),    'row': 0, 'col': 0 },
        { 'widget': self.sbSmoothIteration,     'row': 0, 'col': 1 },
        { 'widget': QLabel( msgFraction, wgt ), 'row': 1, 'col': 0 },
        { 'widget': self.spSmoothOffset,        'row': 1, 'col': 1 }
      ]
      msg = QCoreApplication.translate('GimpSelectionFeature', 'Smooth')
      gbxSmooth = getGroupBox( msg, wgt, l_wts)
      spamSmooth = { 'row': 1, 'col': 2 }
      msgAnnotation   = QCoreApplication.translate('GimpSelectionFeature', 'Annotation:' )
      msgRemoveArea   = QCoreApplication.translate('GimpSelectionFeature', 'Remove Area:' )
      msgRemoveVertex = QCoreApplication.translate('GimpSelectionFeature', 'Remove Vertex:' )
      l_wts = [
        { 'widget': QLabel( msgAnnotation, wgt ),   'row': 0, 'col': 0 },
        { 'widget': self.leditAnnotation,           'row': 0, 'col': 1 },
        { 'widget': QLabel( msgRemoveArea, wgt ),   'row': 1, 'col': 0 },
        { 'widget': self.sbSieveThreshold,          'row': 1, 'col': 1 },
        { 'widget': QLabel( msgRemoveVertex, wgt ), 'row': 2, 'col': 0 },
        { 'widget': self.sbAzimuthThreshold,        'row': 2, 'col': 1 },
        { 'widget': gbxSmooth,                      'row': 3, 'col': 0, 'spam': spamSmooth }
      ]
      msg = QCoreApplication.translate('GimpSelectionFeature', 'Setting' )
      self.gbxSettingFeatures = getGroupBox( msg, wgt, l_wts)
      spamSetting = { 'row': 1, 'col': 2 }
      l_wts = [
        { 'widget': self.btnGetFeatures,        'row': 0, 'col': 0 },
        { 'widget': self.btnRemoveLastFeatures, 'row': 0, 'col': 1 },
        { 'widget': self.gbxSettingFeatures,    'row': 1, 'col': 0, 'spam': spamSetting }
      ]
      gbxGQ = getGroupBox( "GIMP->QGIS", wgt, l_wts)
      l_wts = [
        { 'widget': self.btnSendImage,        'row': 0, 'col': 0 }
      ]
      gbxQG = getGroupBox( "QGIS->GIMP", wgt, l_wts)
      spamGroup = { 'row': 1, 'col': 2 }
      l_wts = [
        { 'widget': gbxQG,                'row': 0, 'col': 0, 'spam': spamGroup },
        { 'widget': gbxGQ,                'row': 1, 'col': 0, 'spam': spamGroup }
      ]
      msg = QCoreApplication.translate('GimpSelectionFeature', 'Transfer' )
      gbxTransfer = getGroupBox( msg, wgt, l_wts)
      #
      l_wts = [
        { 'widget': self.gbxImage,  'row': 0, 'col': 0 },
        { 'widget': gbxTransfer,    'row': 1, 'col': 0 }
      ]
      lyt = getLayout( wgt, l_wts )
      lyt.setSizeConstraint( QLayout.SetMaximumSize )
      wgt.setLayout( lyt )
      self.setWidget( wgt )

    super().__init__( "Gimp Selection Feature", iface.mainWindow() )
    #
    msg = QCoreApplication.translate('GimpSelectionFeature', 'Visibles Images(total  {})')
    self.formatTitleImages = msg
    setupUi()
    self.gsf = GimpSelectionFeature( iface, self )

  def __del__(self):
    del self.gsf


class GimpSelectionFeature(QObject):
  nameModulus = "GimpSelectionFeature"
  def __init__(self, iface, dockWidgetGui):
    def getDefinitionLayerPolygon(dirShape):
      def getFields():
        atts = [
          { 'name': 'id_add', 'type': QVariant.Int },
          { 'name': 'total_imgs', 'type':QVariant.Int },
          { 'name': 'images', 'type': QVariant.String, 'len': 254 },
          { 'name': 'date_add', 'type': QVariant.String, 'len': 20 },
          { 'name': 'crs_map', 'type': QVariant.String, 'len': 50 },
          { 'name': 'extent_map', 'type': QVariant.String, 'len': 200 },
          { 'name': 'annotation', 'type': QVariant.String, 'len': 100 }
        ]
        fields = QgsFields()
        for att in atts:
          f = QgsField( att['name'], att['type'] )
          if 'len' in att:
            f.setLength( att['len'])
          fields.append( f )
        return fields

      return {
        'fileName': os.path.join( dirShape, 'gimp_selection' ),
        'enconding': 'CP1250',
        'fields': getFields(),
        'type': QgsWkbTypes.Polygon, # QgsVectorFileWriter
        'geometryType': QgsWkbTypes.PolygonGeometry, # layer.geometryType()
        'crs': QgsCoordinateReferenceSystem('EPSG:4326'),
        'drive': 'ESRI Shapefile'
      }

    def createDirectories():
      dirPlugin = os.path.dirname(__file__)
      dirImage = os.path.join( dirPlugin, 'img' )
      if not os.path.isdir( dirImage ):
        os.mkdir( dirImage )
      dirShape = os.path.join( dirPlugin, 'shp' )
      if not os.path.isdir( dirShape ):
        os.mkdir( dirShape )
      return { 'image': dirImage, 'shape': dirShape }

    super().__init__()
    self.dockWidgetGui = dockWidgetGui
    self.layerPolygon, self.isIniEditable =  None, None
    self.worker = WorkerTaskGimpSelectionFeature()
    self.layerImages = []
    self.socket, self.hasConnect = None, None
    self.canvas, self.msgBar = iface.mapCanvas(), iface.messageBar()
    self.project = QgsProject.instance()
    self.taskManager = QgsApplication.taskManager()
    self.root = self.project.layerTreeRoot()
    dirs = createDirectories()
    self.pathfileImage = os.path.join( dirs['image'], 'tmp_gimp-plugin.tif' )
    self.pathfileImageSelect = os.path.join( dirs['image'], 'tmp_gimp-plugin_sel.tif' )
    self.defLayerPolygon = getDefinitionLayerPolygon( dirs['shape'] )
    
    self._connect()
    self.setEnabledWidgetTransfer( False )

  def __del__(self):
    if not self.socket is None:
      self.socket.close()
    if not self.hasConnect:
      self._connect( False )

  def _connect(self, isConnect = True):
    ss = [
      { 'signal': self.project.layerWillBeRemoved, 'slot': self.removeLayer },
      { 'signal': self.project.readProject, 'slot': self.readProject },
      { 'signal': self.root.visibilityChanged, 'slot': self.visibilityChanged },
      { 'signal': self.dockWidgetGui.btnSendImage.clicked, 'slot': self.sendImageGimp },
      { 'signal': self.dockWidgetGui.btnGetFeatures.clicked, 'slot': self.getFeatures },
      { 'signal': self.dockWidgetGui.btnRemoveLastFeatures.clicked, 'slot': self.removeLastFeatures }
    ]
    if isConnect:
      self.hasConnect = True
      for item in ss:
        item['signal'].connect( item['slot'] )  
    else:
      self.hasConnect = False
      for item in ss:
        item['signal'].disconnect( item['slot'] )

  def setEnabledWidgetTransfer( self, isEnabled,  removeLastFeatures=False):
    wgts = [
             self.dockWidgetGui.btnSendImage,
             self.dockWidgetGui.btnGetFeatures,
             self.dockWidgetGui.btnRemoveLastFeatures,
             self.dockWidgetGui.gbxSettingFeatures
           ]
    [ item.setEnabled( isEnabled ) for item in wgts ]
    self.dockWidgetGui.btnRemoveLastFeatures.setEnabled( removeLastFeatures )

  def setSocket(self):
    if self.socket is None:
      self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      try:
        self.socket.connect( ( '127.0.0.1', 10000) ) # ( IP, port)
      except socket.error:
        msg = QCoreApplication.translate('GimpSelectionFeature', "Run IBAMA Plugin, 'IBAMA/Service for save the selected regions', in GIMP!")
        self.msgBar.pushMessage( self.nameModulus, msg, Qgis.Warning )
        self.socket = None
        return False
    return True

  def setLegendImages(self):
    def layerIntersectsCanvas(layer):
      mapSettings = self.canvas.mapSettings()
      crsCanvas = mapSettings.destinationCrs()
      extentCanvas = self.canvas.extent()
      if layer.crs() != crsCanvas:
        extentCanvas = mapSettings.mapToLayerCoordinates( layer, extentCanvas )
      extentLayer = layer.extent()
      return extentLayer.intersects( extentCanvas )
     
    del self.layerImages[:]
    txtLegend = ''
    hasImages = False
    totalImages = 0
    rasters = list( filter( lambda l: not l is None and l.type() == QgsMapLayer.RasterLayer, self.root.checkedLayers() ) )
    if len( rasters ) > 0:
      for r in rasters:
        if layerIntersectsCanvas( r ):
          self.layerImages.append( r )
      totalImages = len( self.layerImages )
      if totalImages > 0:
        names = list( map( lambda l: l.name(), self.layerImages ) )
        txtLegend = "{}\n".format( names[0] ) if len( names ) == 1 else '\n'.join( names )
        hasImages = True
    
    title = self.dockWidgetGui.formatTitleImages.format( totalImages )
    if not self.layerPolygon is None and totalImages > 0 and self.project.layerTreeRoot().findLayer( self.layerPolygon.id() ).isVisible():
      title = "{} and {}".format( title, self.layerPolygon.name() )
    self.dockWidgetGui.gbxImage.setTitle( title )
    self.dockWidgetGui.lblLegendImages.setText( txtLegend )
    self.dockWidgetGui.btnSendImage.setEnabled( hasImages )

  def getMaximumValueAdd(self):
    if self.layerPolygon.featureCount() == 0:
      return 0
    idx = self.layerPolygon.fields().indexFromName('id_add')
    return self.layerPolygon.maximumValue( idx )

  def GetFirstLayerPolygon(self):
      def existsFields(names):
        totalExists = 0
        for name in names:
          if name in defNames:
            totalExists += 1
        return totalExists == totalNames

      layers = map( lambda ltl: ltl.layer(), self.root.findLayers() )
      f = lambda l: l.type() == QgsMapLayer.VectorLayer and \
                  l.geometryType() == self.defLayerPolygon['geometryType'] and \
                  l.crs() == self.defLayerPolygon['crs']
      defNames = self.defLayerPolygon['fields'].names()
      totalNames = len( defNames )
      for layer in filter( f, layers ):
        if existsFields( layer.fields().names() ):
          return { 'isOk': True, 'layer': layer }
      return { 'isOk': False }

  def runTask(self, dataRun):
    def finished(exception, dataResult):
      def endEditable():
        self.layerPolygon.commitChanges() # Task NOT commit!
        self.layerPolygon.updateExtents()
        if self.isIniEditable:
          self.layerPolygon.startEditing()

      def setRenderLayer():
        def zoomToBBox(bboxFeats):
          def highlight():
            def removeRB():
                rb.reset( True )
                self.canvas.scene().removeItem( rb )

            rb = QgsRubberBand( self.canvas, QgsWkbTypes.PolygonGeometry)
            rb.setStrokeColor( QColor( 255,  0, 0 ) )
            rb.setWidth( 2 )
            rb.setToGeometry( QgsGeometry.fromRect( extent ), None )
            QTimer.singleShot( 2000, removeRB )

          crsCanvas = self.canvas.mapSettings().destinationCrs()
          ct = QgsCoordinateTransform( self.layerPolygon.crs(), crsCanvas, self.project )
          extent = ct.transform( bboxFeats )
          self.canvas.setExtent( extent )
          self.canvas.zoomByFactor( 1.05 )
          self.canvas.refresh()
          highlight()

        fileStyle = os.path.join( os.path.dirname( __file__ ), "gimpselectionfeature_with_expression.qml" )
        self.layerPolygon.loadNamedStyle( fileStyle )
        zoomToBBox( dataResult['bboxFeats'] )
      
      self.msgBar.clearWidgets()
      if exception:
        self.msgBar.pushMessage( self.nameModulus, str( exception ), Qgis.Critical )
        return
      self.msgBar.pushMessage( self.nameModulus, dataResult['message'], dataResult['level'] )
      if 'getFeatures' == dataResult['process']:
        endEditable()
        imgs =  filter( lambda f: path.exists( f ), ( self.pathfileImage, self.pathfileImageSelect ) )
        [ os.remove( item ) for item in imgs ]
        if dataResult['isOk']:
          setRenderLayer()
          self.setEnabledWidgetTransfer( True, True )
        else:
          self.setEnabledWidgetTransfer( True )
      else:
        self.setEnabledWidgetTransfer( True )

      
    def run(task, data):
      self.worker.setData( task, data )
      return self.worker.run()

    self.setEnabledWidgetTransfer( False )
    task = QgsTask.fromFunction('GimpSelectionFeature Task', run, dataRun, on_finished=finished )
    if not self.layerPolygon is None:
      task.setDependentLayers( [ self.layerPolygon ] )
    self.taskManager.addTask( task )

  @pyqtSlot('QDomDocument')
  def readProject(self, dom=None):
    r = self.GetFirstLayerPolygon()
    if r['isOk']:
      self.layerPolygon = r['layer']
    self.setLegendImages()

  @pyqtSlot('QgsLayerTreeNode*')
  def visibilityChanged(self, node):
    self.setLegendImages()

  @pyqtSlot(str)
  def removeLayer(self, sIdLayer):
    if not self.layerPolygon is None and self.layerPolygon.id() == sIdLayer:
      self.layerPolygon = None
    
    if self.layerPolygon is None or sIdLayer in map( lambda lyr: lyr.id(), self.layerImages ):
      self.setLegendImages()

  @pyqtSlot()
  def sendImageGimp(self):
    if len( self.layerImages ) == 0:
      return
    self.setLegendImages() # Update the order of images

    if not self.setSocket():
      return

    data = {
      'process': 'sendImageGimp',
      'socket': self.socket,
      'paramProcess': {
        'layerImages': self.layerImages,
        'canvas': self.canvas,
        'pathfileImage': self.pathfileImage
      }
    }
    if not self.layerPolygon is None and self.project.layerTreeRoot().findLayer( self.layerPolygon.id() ).isVisible():
      data['paramProcess']['layerPolygon'] = self.layerPolygon

    msg = QCoreApplication.translate('GimpSelectionFeature', 'Sending image to GIMP...')
    self.msgBar.pushMessage( self.nameModulus, msg, Qgis.Info )
    self.runTask( data )

  @pyqtSlot()
  def getFeatures(self):
    def setLayerPolygon():
      def createLayerPolygon():
        r = { 'isOk': True }
        fw, d = QgsVectorFileWriter, self.defLayerPolygon
        writer = fw( d['fileName'], d['enconding'], d['fields'], d['type'], d['crs'], d['drive'] )
        if writer.hasError() != QgsVectorFileWriter.NoError:
          r = { 'isOk': False, 'message': writer.errorMessage() }
        del writer
        if not r['isOk']:
          return r
        fileNameExt, name = "{}.shp".format( d['fileName'] ), os.path.split( d['fileName'] )[-1]
        r['layer'] = QgsVectorLayer( fileNameExt, name, 'ogr' )
        return r

      if self.layerPolygon is None:
        r = self.GetFirstLayerPolygon()
        if  r['isOk']:
          self.layerPolygon = r['layer']
        else:
          r = createLayerPolygon()
          if not r['isOk']:
            self.msgBar.pushMessage( self.nameModulus, r['message'], Qgis.Critical )
            return False
          self.layerPolygon = self.project.addMapLayer( r['layer'] )

      # Refresh Symbology
      self.layerPolygon.loadNamedStyle( os.path.join( os.path.dirname( __file__ ), "gimpselectionfeature_no_expression.qml" ) )
      ltl = self.root.findLayer( self.layerPolygon.id() )
      ltl.setCustomProperty('showFeatureCount', True)
      ltl.setItemVisibilityChecked( True )
      return True

    def getDataParams():
      # paramSmooth: iter = interations, offset = 0.0 - 1.0(100%)
      # paramsSieve: threshold = Size in Pixel, connectedness = 4 or 8(diagonal)
      tSieve = self.dockWidgetGui.sbSieveThreshold.value() + 1
      tAzimuth = self.dockWidgetGui.sbAzimuthThreshold.value()
      offset = self.dockWidgetGui.spSmoothOffset.value() / 100.0
      viter = self.dockWidgetGui.sbSmoothIteration.value()
      return {
        'process': 'getFeatures',
        'socket': self.socket,
        'paramProcess': {
          'layerPolygon': self.layerPolygon,
          'lastAdd': self.getMaximumValueAdd(),
          'pathfileImageSelect': self.pathfileImageSelect,
          'annotation': self.dockWidgetGui.leditAnnotation.text(),
          'smooth': { 'iter': viter, 'offset': offset },
          'sieve': { 'threshold': tSieve, 'connectedness': 4 },
          'azimuth': { 'threshold': tAzimuth }
        }
      }

    def startEditable():
      self.isIniEditable = self.layerPolygon.isEditable()
      if not self.isIniEditable:
        self.layerPolygon.startEditing()

    if not self.setSocket() or not setLayerPolygon():
      return

    data = getDataParams()
    startEditable() # Task NOT commit

    msg = QCoreApplication.translate('GimpSelectionFeature', 'Add features...')
    self.msgBar.pushMessage( self.nameModulus, msg, Qgis.Info )
    self.runTask( data )

  @pyqtSlot()
  def removeLastFeatures(self):
    self.isIniEditable = self.layerPolygon.isEditable()
    if not self.isIniEditable:
      self.layerPolygon.startEditing()
    exp = QgsExpression( '"id_add" = {}'.format( self.getMaximumValueAdd() ) )
    request = QgsFeatureRequest( exp )
    request.setFlags( QgsFeatureRequest.NoGeometry )
    it = self.layerPolygon.getFeatures( request )
    for feat in it:
      self.layerPolygon.deleteFeature( feat.id()  )
    self.layerPolygon.commitChanges()
    if self.isIniEditable:
      self.layerPolygon.startEditing()
    self.layerPolygon.updateExtents()
    self.dockWidgetGui.btnRemoveLastFeatures.setEnabled( False )


class WorkerTaskGimpSelectionFeature():
  def __init__(self):
    self.runProcess, self.task, self.socket, self.paramProcess, self.lastAdd = None, None, None, None, None
  
  def setData(self, task, data ):
    def setRunProcess():
      if 'sendImageGimp' == data['process']:
        self.runProcess = self.sendImageGimp
      elif 'getFeatures' == data['process']:
        self.runProcess = self.getFeatures
        self.lastAdd = data['paramProcess']['lastAdd']
      else:
        self.runProcess = None

    self.task         = task
    self.socket       = data['socket']
    self.paramProcess = data['paramProcess']

    setRunProcess()

  def getDataServer(self):
    def getSendData():
      if self.runProcess == self.sendImageGimp:
        data = {
          'function': 'add_image',
          'filename': self.paramProcess['pathfileImage'],
          'paramImage': {
            'extent_map': self.paramProcess['extent_map'],
            'crs_map': self.paramProcess['crs_map'],
            'res': { 'X': self.paramProcess['res']['X'], 'Y': self.paramProcess['res']['Y'] },
            'json_images': self.paramProcess['json_images']
          }
        }
      elif self.runProcess == self.getFeatures:
        data = {
          'function': 'create_selection_image',
          'filename': self.paramProcess['pathfileImageSelect']
        }
      return data

    receive_data = None
    try:
      send_data = json.dumps( getSendData() )
      self.socket.send( send_data.encode() )
      receive_data = self.socket.recv(4096)
    except socket.error as msg_socket:
      msg = QCoreApplication.translate('GimpSelectionFeature', 'Error connection GIMP Server: {}. Run IBAMA plugin in GIMP')
      msg = msg.format( str( msg_socket ) )
    if receive_data is None:
      return { 'isOk': False, 'message': msg }
    
    if len( receive_data ) == 0:
      msg = QCoreApplication.translate('GimpSelectionFeature', "Run IBAMA Plugin, 'IBAMA/Service for save the selected regions', in GIMP!")
      return { 'isOk': False, 'message': msg }

    return json.loads( receive_data )

  def getErrorReturn(self, message, process, level=Qgis.Warning):
    return { 'isOk': False, 'message': message, 'process': process, 'level': level }

  def getFeatures(self):
    def getGeorefImage():
     # Show error _TIFFVSetField: when read Selected Image
     # Try use 'gdal.UseExceptions()' and try / except RuntimeError: but not work..
      ds = gdal.Open( self.paramProcess['pathfileImageSelect'], gdal.GA_Update )
      if gdal.GetLastErrorType() != 0:
        return { 'isOk': False, 'message': gdal.GetLastErrorMsg() }

      p = paramsImgSel
      smin, smax = p['extent_map'].split(',')
      ulX = float( smin.split(' ')[0])
      ulY = float( smax.strip().split(' ')[1])
      ulX_SelImage = ulX + p['ulPixelSelect']['X'] *  p['res']['X']
      ulY_SelImage = ulY - p['ulPixelSelect']['Y'] *  p['res']['Y']

      transform = ( ulX_SelImage,  p['res']['X'], 0.0, ulY_SelImage, 0.0, -1 *  p['res']['Y'] )
      ds.SetGeoTransform( transform )
      ds.SetProjection( wktProj )

      band = ds.GetRasterBand( 1 )
      band.SetNoDataValue( 0.0 )

      return { 'isOk': True, 'dataset': ds }

    def polygonizeSelectionImage(ds_img):
      def setGeomAzimuthTolerance(geom, threshold):
        def changeRing(ring):
          def azimuth(p1, p2):
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            az = math.atan2( dx, dy ) * 180.0 / math.pi
            return az
          
          if ring.GetPointCount() < 4:
            return

          points = ring.GetPoints()
          ids_new = [ 0 ]
          upperIdPoints = len( points ) -1
          for i in range( 1, upperIdPoints ):
            aznew = azimuth( points[ ids_new[-1] ], points[ i ] )
            az = azimuth( points[ i ], points[ i+1 ] )
            if abs( az - aznew ) > threshold:
              ids_new.append( i )
          ids_new.append( upperIdPoints )
          if len( ids_new ) < len( points ):
            ids_remove = list( set( range( len( points ) ) ) - set( ids_new ) )
            ids_remove.sort()
            ids_remove.reverse()
            for i in range( len( ids_remove ) ):
              del points[ ids_remove[ i ] ]
            
            ring.Empty()
            for i in range( len( points ) ):
              ring.SetPoint_2D( i, points[i][0], points[i][1])

        numPolygons = geom.GetGeometryCount()
        for id1 in range(  numPolygons ):
          polygon = geom.GetGeometryRef( id1 )
          numRings = polygon.GetGeometryCount()
          if numRings == 0:
            changeRing( polygon ) # Only Out ring! 
          else:
            for id2 in range(  numRings ):
              ring = polygon.GetGeometryRef( id2)
              changeRing( ring )

      band = ds_img.GetRasterBand( 1 )
      # Sieve Band
      drv = gdal.GetDriverByName('MEM')
      ds_sieve = drv.Create( '', ds_img.RasterXSize, ds_img.RasterYSize,1, band.DataType )
      ds_sieve.SetGeoTransform( ds_img.GetGeoTransform() )
      band_sieve = ds_sieve.GetRasterBand(1)

      p_threshold = self.paramProcess['sieve']['threshold']
      p_connectedness = self.paramProcess['sieve']['connectedness']
      gdal.SieveFilter( band, None, band_sieve, p_threshold, p_connectedness, [], callback=None )
      ds_img, band = None, None
      if gdal.GetLastErrorType() != 0:
        return { 'isOk': False, 'message': gdal.GetLastErrorMsg() }

      # Memory layer - Polygonize
      srs = osr.SpatialReference()
      srs.ImportFromWkt( wktProj )
      drv_poly = ogr.GetDriverByName('MEMORY')
      ds_poly = drv_poly.CreateDataSource('memData')
      layer_poly = ds_poly.CreateLayer( 'memLayer', srs, ogr.wkbPolygon )
      field = ogr.FieldDefn("dn", ogr.OFTInteger)
      layer_poly.CreateField( field )
      idField = 0

      gdal.Polygonize( band_sieve, None, layer_poly, idField, [], callback=None )
      ds_sieve = band_sieve = None
      if gdal.GetLastErrorType() != 0:
        return { 'isOk': False, 'message': gdal.GetLastErrorMsg() }

      # Get Geoms - Apply Azimuth tolerance
      geoms = []
      layer_poly.SetAttributeFilter("dn = 255")
      p_threshold = self.paramProcess['azimuth']['threshold']
      if p_threshold > 0:
        p_threshold = float( p_threshold )
        for feat in layer_poly:
          geom = feat.GetGeometryRef()
          setGeomAzimuthTolerance( geom, p_threshold )
          geoms.append( geom.Clone() )
      else:
        for feat in layer_poly:
          geoms.append( feat.GetGeometryRef().Clone() )

      ds_poly = layer_poly = None

      return { 'isOk': True, 'geoms': geoms }

    def addFeatures(geoms):
      def addAttribute(feat):
        self.lastAdd += 1
        feat.setAttribute('id_add', self.lastAdd )
        sdatetime = str( datetime.datetime.today().replace(microsecond=0) )
        feat.setAttribute('date_add', sdatetime )
        v_json = json.loads( paramsImgSel['json_images'] )
        html  = getHtmlTreeMetadata( v_json, '')
        feat.setAttribute('images', html )
        feat.setAttribute('total_imgs', len( v_json ) )
        feat.setAttribute('crs_map', paramsImgSel['crs_map'] )
        feat.setAttribute('extent_map', paramsImgSel['extent_map'] )
        feat.setAttribute('annotation', self.paramProcess['annotation'] )

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

      layerPolygon = self.paramProcess['layerPolygon']
      srsLayerPolygon = osr.SpatialReference()
      srsLayerPolygon.ImportFromWkt( layerPolygon.crs().toWkt() )

      feat = QgsFeature( layerPolygon.dataProvider().fields() )
      addAttribute( feat )

      p_iter = self.paramProcess['smooth']['iter']
      p_offset = self.paramProcess['smooth']['offset']
      envFeats = None # [ xmin, xmax, ymin, ymax ]
      for geom in geoms:
        geom.TransformTo( srsLayerPolygon )
        envFeats = envelopGeoms( envFeats, geom )
        geomLayer = QgsGeometry.fromWkt( geom.ExportToWkt() ).smooth( p_iter, p_offset )
        geom.Destroy()
        feat.setGeometry( geomLayer )
        layerPolygon.addFeature( feat )
        del geomLayer
      feat = None
      return envFeats

    process = 'getFeatures'

    paramsImgSel = self.getDataServer()
    if not paramsImgSel['isOk']:
      return self.getErrorReturn( paramsImgSel['message'], process )

    if self.task.isCanceled():
      return { 'isOk': False }
    wktProj = QgsCoordinateReferenceSystem( paramsImgSel['crs_map'] ).toWkt()
    
    r = getGeorefImage()
    if not r['isOk']:
      return self.getErrorReturn( r['message'], process )
    if self.task.isCanceled():
      return { 'isOk': False }
    ds_img = r['dataset']

    r = polygonizeSelectionImage( ds_img )
    if not r['isOk']:
      return self.getErrorReturn( r['message'], process )
    if self.task.isCanceled():
      return { 'isOk': False }
    geoms = r['geoms']

    totalFeats = len( geoms )
    if totalFeats  == 0:
      msg = QCoreApplication.translate('GimpSelectionFeature', "Not found features in selections ('{}')")
      msg = msg.format( self.paramProcess['pathfileImageSelect'] )
      return self.getErrorReturn( msg, process )

    envFeats = addFeatures( geoms ) # NOT commit in Task!

    msg = QCoreApplication.translate('GimpSelectionFeature', "Added {} features in '{}'")
    msg = msg.format( totalFeats, self.paramProcess['layerPolygon'].name() )
    bboxFeats = QgsRectangle( envFeats[0], envFeats[2], envFeats[1], envFeats[3] )
    return {
      'isOk': True,
      'message': msg,
      'level': Qgis.Info,
      'process': 'getFeatures',
      'bboxFeats': bboxFeats
    }

  def sendImageGimp(self):
    def createImageParams():
      def finished():
        def addParams():
          def getJsonImages():
            vmap = {}
            for l in self.paramProcess['layerImages']:
              vmap[ l.name() ] = l.source()
            return json.dumps( vmap )

          e =  self.paramProcess['canvas'].extent()
          imgWidth, imgHeight = image.width(), image.height()
          resX, resY = e.width() / imgWidth, e.height() / imgHeight
          self.paramProcess['json_images'] = getJsonImages()
          self.paramProcess['crs_map'] = self.paramProcess['canvas'].mapSettings().destinationCrs().authid()
          self.paramProcess['extent_map'] = e.asWktCoordinates() # xMin, yMin, xMax, yMax
          self.paramProcess['res'] = { 'X': resX, 'Y': resY } 

        image = job.renderedImage()
        if bool( self.paramProcess['canvas'].property('retro') ):
          image = image.scaled( image.width() / 3, image.height() / 3 )
          image = image.convertToFormat( QImage.Format_Indexed8, Qt.OrderedDither | Qt.OrderedAlphaDither )
        image.save( self.paramProcess['pathfileImage'], "TIFF", 100 ) # 100: Uncompressed
        addParams()

      settings = QgsMapSettings( self.paramProcess['canvas'].mapSettings() )
      settings.setBackgroundColor( QColor( Qt.transparent ) )
      
      layers = self.paramProcess['layerImages']
      if 'layerPolygon' in self.paramProcess:
        layers = [ self.paramProcess['layerPolygon'] ] + layers
      settings.setLayers( layers )
      job = QgsMapRendererParallelJob( settings ) 
      job.start()
      job.finished.connect( finished) 
      job.waitForFinished()

    createImageParams()
    r = self.getDataServer()
    if not r['isOk']:
      return self.getErrorReturn( r['message'], 'sendImageGimp' )
    msg = QCoreApplication.translate('GimpSelectionFeature', r['message'])
    return { 'isOk': True, 'message': msg, 'level': Qgis.Info, 'process': 'sendImageGimp' }

  def run(self):
    if self.runProcess is None:
      msg = QCoreApplication.translate('GimpSelectionFeature', 'ERROR in Script')
      return self.getErrorReturn( msg, None, Qgis.Critical )

    return self.runProcess()
