import os, sys, dbus, json, datetime
from os import path
from optparse import OptionParser

from PyQt4 import ( QtGui, QtCore )
from qgis import ( core as QgsCore, gui as QgsGui )

from osgeo import ( gdal, ogr, osr )
from gdalconst import ( GA_ReadOnly, GA_Update )

class DBusGimpPolygonSelection(QtCore.QObject):
  def __init__(self, iface):
    def setDBusGimp():
      uri = "gimp.plugin.dbus.selection"
      path = "/%s" % uri.replace( '.', '/' )
      self.name_bus = { 'uri': uri, 'path': path }
      self.session_bus = dbus.SessionBus()
    #
    def createLayerPolygon():
      l_fields = map( lambda item: "field=%s" % item, [ "image:string(200)", "datetime:string(20)", "crs:string(100)" ] )
      l_fields.insert( 0, "crs=epsg:4326" )
      l_fields.append( "index=yes" )
      s_fields = '&'.join( l_fields )
      self.layerPolygon =  QgsVectorLayer( "Polygon?%s" % s_fields, "gimp_polygon", "memory")
      QgsMapLayerRegistry.instance().addMapLayer( self.layerPolygon )
    #
    super(DBusGimpPolygonSelection, self).__init__()
    self.iface = iface
    self.canvas = iface.mapCanvas()
    self.titleMsg = "DBus Gimp Polygon Selection"
    self.msgError = None
    #
    self.session_bus = self.idbus = self.proxyDBus = None
    setDBusGimp()
    self.paramsImage = None
    self.setParamsImage( self.iface.activeLayer() )
    self.layerPolygon = None
    createLayerPolygon()
    if self.checkGimpSelection()['isOk']:
      self.addFeatures( False )
    #
    self._connect()

  def __del__(self):
    self._connect( False )
    if not self.idbus is None:
      self.idbus.quit()
    if not self.session_bus is None:
      self.session_bus.close()

  def _connect(self, isConnect = True):
    ss = [
      { 'signal': self.canvas.currentLayerChanged, 'slot': self.setParamsImage }
    ]
    if isConnect:
      self.hasConnect = True
      for item in ss:
        item['signal'].connect( item['slot'] )  
    else:
      self.hasConnect = False
      for item in ss:
        item['signal'].disconnect( item['slot'] )

  def setInterfaceDBus(self):
    if not self.name_bus['uri'] in self.session_bus.list_names():
      return { 'isOk': False, 'msg': "Active 'Selection save image Server' in Gimp Plugin!" }
    #
    self.proxyDBus = self.session_bus.get_object( self.name_bus['uri'], self.name_bus['path'] )
    self.idbus = dbus.Interface( self.proxyDBus, self.name_bus['uri'] )
    return { 'isOk': True }

  def checkGimpSelection(self):
    if self.idbus is None:
      vreturn = self.setInterfaceDBus()
      if not vreturn['isOk']:
        return vreturn
    #
    vreturn = json.loads( str( self.idbus.get_filename() ) )
    if not vreturn['isOk']:
      vreturn['msg'] = "%s ('%s') in GIMP" % ( vreturn['msg'], self.paramsImage['filename'] )
      return vreturn
    #
    if not vreturn['filename'] == self.paramsImage['filename']:
      msg = "Active layer QGIS '%s' not equal Active Layer GIMP '%s'!" % ( self.paramsImage['filename'], vreturn['filename'] )
      return { 'isOk': False, 'msg': msg }
    #
    vreturn = json.loads( str( self.idbus.exist_selection_image() ) )
    if not vreturn['isOk']:
      vreturn['msg'] = "GIMP: %s" % vreturn['msg']
      return vreturn
    #
    return { 'isOk': True }

  def addFeatures(self, showMsg=True):
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
    #
    def polygonizeSelectionImage():
      ds_img = gdal.Open( pImgSel['filename'], GA_ReadOnly )
      if gdal.GetLastErrorType() != 0:
        return { 'isOk': False, 'msg': gdal.GetLastErrorMsg() }
      band = ds_img.GetRasterBand( 1 )
      #
      filename = "%s.geojson" % path.splitext( pImgSel['filename'] )[0]
      drv = ogr.GetDriverByName("GeoJSON")
      if path.exists( filename ):
        drv.DeleteDataSource( filename )
      ds_json = drv.CreateDataSource( filename )
      srs = osr.SpatialReference()
      srs.ImportFromWkt( self.paramsImage['wktProj'] )
      layer = ds_json.CreateLayer( "polygonize" , srs=srs )
      field = ogr.FieldDefn("dn", ogr.OFTInteger)
      layer.CreateField( field )
      idField = 0
      #
      gdal.Polygonize( band, None, layer, idField, [], callback=None )
      #
      ds_img = band = None
      ds_json.Destroy()
      ds_json = None
      #
      return { 'isOk': True, 'filename':filename }

    def addAttribute(feat):
      sdatetime = datetime.datetime.now().strftime( "%Y-%m-%d %H:%M:%s")
      feat.setAttribute('image', self.paramsImage['filename'] )
      feat.setAttribute('datetime', sdatetime )
      feat.setAttribute('crs', self.paramsImage['desc_crs'] )

    if self.paramsImage is None:
      if showMsg:
        msg = "Active raster image in QGIS"
        self.iface.messageBar().pushMessage( self.titleMsg, msg, QgsGui.QgsMessageBar.WARNING, 5 )
      return
    #
    vreturn = self.checkGimpSelection()
    if not vreturn['isOk']:
      if showMsg:
        self.iface.messageBar().pushMessage( self.titleMsg, vreturn['msg'], QgsGui.QgsMessageBar.WARNING, 5 )
      return
    #
    pImgSel = json.loads( str( self.idbus.create_selection_image() ) )
    vreturn = setGeorefImage()
    if not vreturn['isOk']:
      if showMsg:
        self.iface.messageBar().pushMessage( self.titleMsg, vreturn['msg'], QgsGui.QgsMessageBar.WARNING, 5 )
      return
    vreturn = polygonizeSelectionImage()
    if not vreturn['isOk']:
      if showMsg:
        self.iface.messageBar().pushMessage( self.titleMsg, vreturn['msg'], QgsGui.QgsMessageBar.WARNING, 5 )
      return
    #
    with open( vreturn['filename'] ) as f:
      data = json.load(f)
    #
    feats255 = filter( lambda item: item['properties']['dn'] == 255, data['features'] )
    del data
    #
    totalFeats = len( feats255 )
    feat = QgsCore.QgsFeature( self.layerPolygon.pendingFields() )
    addAttribute( feat )
    #
    crsImg = QgsCore.QgsCoordinateReferenceSystem()
    crsImg.createFromString( self.paramsImage['wktProj'] )
    ct = QgsCore.QgsCoordinateTransform( crsImg, self.layerPolygon.crs() )
    #
    #
    isIniEditable = self.layerPolygon.isEditable()
    if not isIniEditable:
      self.layerPolygon.startEditing()
    #
    median_res = ( self.paramsImage['res'][0] + self.paramsImage['res'][1] ) / 2.0
    tolerance = 0.5 * median_res
    for id in xrange( totalFeats ):
      geomGdal = ogr.CreateGeometryFromJson( json.dumps( feats255[id]['geometry'] ) )
      #geomSmoot = geom.ConvexHull()
      #geomSmoot = geom.DelaunayTriangulation( tolerance ) # Not exist
      geomSmootGdal = geomGdal.SimplifyPreserveTopology( tolerance )
      #
      geom = QgsCore.QgsGeometry.fromWkt( geomSmootGdal.ExportToWkt() )
      geom.transform( ct )
      feat.setGeometry( geom )
      self.layerPolygon.addFeature( feat )
      #
      geomGdal.Destroy()
      geomSmootGdal.Destroy()
      del geom
    feat = None
    self.layerPolygon.commitChanges()
    if isIniEditable:
      self.layerPolygon.startEditing()
    self.layerPolygon.updateExtents()
    #
    msg = "Add %d features in '%s'" % ( totalFeats, self.layerPolygon.name() )
    self.iface.messageBar().pushMessage( self.titleMsg, msg, QgsGui.QgsMessageBar.INFO, 5 )

  def addImageGimp(self):
    if self.paramsImage is None:
      msg = "Active raster image in QGIS"
      self.iface.messageBar().pushMessage( self.titleMsg, msg, QgsGui.QgsMessageBar.WARNING, 5 )
      return
    #
    if self.idbus is None:
      vreturn = self.setInterfaceDBus()
      if not vreturn['isOk']:
        self.iface.messageBar().pushMessage( self.titleMsg, vreturn['msg'], QgsGui.QgsMessageBar.WARNING, 5 )
        return
    #
    vreturn = json.loads( str( self.idbus.add_image( self.paramsImage['filename'] ) ) )
    if not vreturn['isOk']:
      self.iface.messageBar().pushMessage( self.titleMsg, vreturn['msg'], QgsGui.QgsMessageBar.WARNING, 5 )
      return

  @QtCore.pyqtSlot(QgsCore.QgsMapLayer)
  def setParamsImage(self, layer ):
    if not layer is None and layer.type() == QgsCore.QgsMapLayer.RasterLayer:
      res = ( layer.rasterUnitsPerPixelX(), -1 * layer.rasterUnitsPerPixelY() )
      tiePoint = ( layer.extent().xMinimum(), layer.extent().yMaximum() )
      crs = layer.crs()
      self.paramsImage = { 
        'filename': layer.source(), 
        'res': res, 'tiePoint': tiePoint, 
        'wktProj': str( crs.toWkt() ), 'desc_crs': crs.description()
      }
      msg = "Image '%s' actived " % self.paramsImage['filename']
      self.iface.messageBar().pushMessage( self.titleMsg, msg, QgsGui.QgsMessageBar.INFO, 5 )

###########
"""
dg = DBusGimpPolygonSelection( iface )
dg.addFeatures()
dg.addImageGimp()
"""
