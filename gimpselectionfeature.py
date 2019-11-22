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


import os, sys, json, datetime, math, stat, re, shutil, filecmp

from qgis.PyQt.QtCore import (
    QCoreApplication, Qt, QSettings,
    QVariant, QObject,
    pyqtSlot, pyqtSignal
)
from qgis.PyQt.QtGui import QImage, QColor 
from qgis.PyQt.QtWidgets import (
    QWidget, QDockWidget,
    QLayout, QGridLayout,
    QGroupBox, QDoubleSpinBox,
    QCheckBox, QLabel, QLineEdit,
    QSpinBox, QLineEdit, QPushButton
)
from qgis.core import (
    QgsApplication, QgsProject, Qgis, QgsMapSettings,
    QgsTask, QgsMapRendererParallelJob,
    QgsMapLayer, QgsVectorLayer, QgsVectorFileWriter, QgsFeatureRequest,
    QgsFeature, QgsField, QgsFields,
    QgsExpression,
    QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsCoordinateTransformContext,
    QgsGeometry, QgsRectangle, QgsWkbTypes,
    QgsPoint, QgsLineString, QgsPolygon
)

from osgeo import gdal, ogr, osr

from .json2html import getHtmlTreeMetadata
from .mapcanvaseffects import MapCanvasGeometry
from .sockets import SocketClient


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

            def getSpinRemoveAreaPixels(wgt, value):
                sp = QSpinBox( wgt)
                sp.setRange(0, 1000)
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
            msg = QCoreApplication.translate('GimpSelectionFeature', 'Adjust the borders' )
            self.chkAdjustBorder = QCheckBox( msg, wgt )
            self.leditAnnotation = QLineEdit( wgt )
            self.sbRemoveAreaPixels = getSpinRemoveAreaPixels( wgt, 10 )
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
                { 'widget': self.sbRemoveAreaPixels,          'row': 1, 'col': 1 },
                { 'widget': QLabel( msgRemoveVertex, wgt ), 'row': 2, 'col': 0 },
                { 'widget': self.sbAzimuthThreshold,        'row': 2, 'col': 1 },
                { 'widget': gbxSmooth,                      'row': 3, 'col': 0, 'spam': spamSmooth },
                { 'widget': self.chkAdjustBorder,           'row': 4, 'col': 0, }
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
        msg = QCoreApplication.translate('GimpSelectionFeature', 'Visibles Images(total {})')
        self.formatTitleImages = msg
        setupUi()
        self.gsf = GimpSelectionFeature( iface, self )

    # def __del__(self):
    #     del self.gsf

    def clean(self):
        del self.gsf


class GimpSelectionFeature(QObject):
    nameModulus = "GimpSelectionFeature"
    def __init__(self, iface, dockWidgetGui):
        def createDirectories():
            dirPlugin = os.path.dirname(__file__)
            dirImage = os.path.join( dirPlugin, 'img' )
            if not os.path.isdir( dirImage ):
                os.mkdir( dirImage )
            dirLayer = os.path.join( dirPlugin, 'db' )
            if not os.path.isdir( dirLayer ):
                os.mkdir( dirLayer )
            return { 'image': dirImage, 'gpkg': dirLayer }

        def copyPluginGimp():
            findedDir = []
            def getDirectories(srcDir, mask, totalSearch):
                for root, _dirs, _files in os.walk( srcDir ):
                    if re.match( mask, root.replace('\\', '/'), re.IGNORECASE ):
                        findedDir.append( root )
                        if len( findedDir ) == totalSearch:
                            break
                return findedDir

            def msgError(dirPlugin):
                msg = QCoreApplication.translate('GimpSelectionFeature', "Not found profile Gimp(2.8 or 2.10) or '{}' inside profile" )
                msg = msg.format( dirPlugin )
                return msg

            def copyNewPlugin(dirPluginQgis, dirsPluginGimp, name):
                fromFile = os.path.join( dirPluginQgis, name )
                toFile = os.path.join( dirsPluginGimp, name )
                if not os.path.exists( toFile ) or not filecmp.cmp( fromFile, toFile ):
                    shutil.copy2( fromFile, toFile )
                    if sys.platform != 'win32': # Add executable
                        st =  os.stat( toFile )
                        os.chmod( toFile, st.st_mode | stat.S_IEXEC )

            dirPluginQgis = os.path.dirname(__file__)
            copyFiles = ('socket_server_selection.py', 'sockets.py')
            s = QSettings()
            dirsPluginGimp = s.value( self.localSetting.format('dirsPluginGimp'), None )
            if not dirsPluginGimp is None and os.path.isdir( dirsPluginGimp ):
                for d in dirsPluginGimp:
                    for f in copyFiles:
                        copyNewPlugin( dirPluginQgis, d, f )
            else:
                # Search GIMP 2.8 and 2.10
                totalSearch = 2
                dirUser = os.path.expanduser('~')
                dirPlugin = "plug-ins"
                mask = r".+/\.?GIMP.2\.[81]0?/{}".format( dirPlugin )
                dirsPluginGimp = getDirectories( dirUser, mask, totalSearch )
                if len( dirsPluginGimp ) == 0:
                    return { 'isOk': False, 'message': msgError( dirPlugin ) }
                s.setValue( self.localSetting.format('dirsPluginGimp'),  dirsPluginGimp )
                dirPluginQgis = os.path.dirname(__file__)
                for item in dirsPluginGimp:
                    copyNewPlugin( dirPluginQgis, item, 'socket_server_selection.py' )
                    copyNewPlugin( dirPluginQgis, item, 'sockets.py' )
                
            return { 'isOk': True }

        super().__init__()
        self.dockWidgetGui = dockWidgetGui
        self.localSetting = 'gimpselectionfeature_plugin/{}'
        self.layerPolygon, self.isIniEditable =  None, None
        self.layerImages = []
        self.hasConnect = None
        self.sc = SocketClient()
        self.canvas, self.msgBar = iface.mapCanvas(), iface.messageBar()
        self.project = QgsProject.instance()
        self.mapCanvasEffects = MapCanvasGeometry()
        self.root = self.project.layerTreeRoot()
        self.taskManager = QgsApplication.taskManager()
        dirs = createDirectories()
        self.defLayerPolygon = {
            'filepath': os.path.join( dirs['gpkg'], 'gimp_selection.gpkg' ),
            'layername': 'gimp_selection'
        }
        self.pathfileImage = os.path.join( dirs['image'], 'tmp_gimp-plugin.tif' )
        self.pathfileImageSelect = os.path.join( dirs['image'], 'tmp_gimp-plugin_sel.tif' )

        self._setEnabledWidgetTransfer( False )
        
        r = copyPluginGimp()
        if not r['isOk']:
            self.msgBar.pushMessage( self.nameModulus, r['message'], Qgis.Critical, 0 )
            return

        self._connect()

    def __del__(self):
        del self.sc

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

    def _setEnabledWidgetTransfer( self, isEnabled,  removeLastFeatures=False):
        wgts = [
                self.dockWidgetGui.btnSendImage,
                self.dockWidgetGui.btnGetFeatures,
                self.dockWidgetGui.btnRemoveLastFeatures,
                self.dockWidgetGui.gbxSettingFeatures
            ]
        [ item.setEnabled( isEnabled ) for item in wgts ]
        self.dockWidgetGui.btnRemoveLastFeatures.setEnabled( removeLastFeatures )

    def _pushMessageTask(self, result, isCanceled, message):
        self.msgBar.clearWidgets()
        if result:
            level = Qgis.Info if not isCanceled else Qgis.Warning
        else:
            level = Qgis.Critical

        self.msgBar.pushMessage( self.nameModulus, message, level )

    def _setLegendImages(self):
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
                txtLegend = f"{names[0]}\n" if len( names ) == 1 else '\n'.join( names )
                hasImages = True
        
        title = self.dockWidgetGui.formatTitleImages.format( totalImages )
        self.dockWidgetGui.gbxImage.setTitle( title )
        self.dockWidgetGui.lblLegendImages.setText( txtLegend )
        self.dockWidgetGui.btnSendImage.setEnabled( hasImages )

    def _getMaximumValueAdd(self):
        if self.layerPolygon.featureCount() == 0:
            return 0
        idx = self.layerPolygon.fields().indexFromName('id_add')
        return self.layerPolygon.maximumValue( idx )

    def _getFirstLayerPolygon(self):
        source = "{}|layername={}".format( self.defLayerPolygon['filepath'], self.defLayerPolygon['layername'] )
        layers = [ ltl.layer() for ltl in self.root.findLayers() if ltl.layer().source() == source ]
        if len( layers ) == 0:
            return { 'isOk': False }
        return { 'isOk': True, 'layer': layers[0] }

    def _setConnectionSocket(self):
        if not self.sc.hasConnect:
            r = self.sc.connect()
            if not r['isOk']:
                self.msgBar.clearWidgets()
                self.msgBar.pushMessage( self.nameModulus, r['message'], Qgis.Critical )
                return False
        return True

    def _getIteratorLastFeatures(self):
        exp = QgsExpression( f"\"id_add\" = {self._getMaximumValueAdd()}" )
        request = QgsFeatureRequest( exp )
        request.setFlags( QgsFeatureRequest.NoGeometry )
        return self.layerPolygon.getFeatures( request )

    @pyqtSlot(str)
    def removeLayer(self, sIdLayer):
        if not self.layerPolygon is None and self.layerPolygon.id() == sIdLayer:
            self.layerPolygon = None
        if self.layerPolygon is None or sIdLayer in [ lyr.id() for lyr in self.layerImages ]:
            self._setLegendImages()

    @pyqtSlot('QDomDocument')
    def readProject(self, dom=None):
        r = self._getFirstLayerPolygon()
        if r['isOk']:
            self.layerPolygon = r['layer']
        self._setLegendImages()

    @pyqtSlot('QgsLayerTreeNode*')
    def visibilityChanged(self, node):
        self._setLegendImages()

    @pyqtSlot()
    def sendImageGimp(self):
        @pyqtSlot(bool, bool, str)
        def finished(result, isCanceled, message):
            self._pushMessageTask( result, isCanceled, message )
            self._setEnabledWidgetTransfer(True)

        if len( self.layerImages ) == 0 or not self._setConnectionSocket():
            return

        self._setEnabledWidgetTransfer( False )
        self._setLegendImages() # Update the order of images
        msg = QCoreApplication.translate('GimpSelectionFeature', 'Sending image to GIMP...')
        self.msgBar.pushMessage( self.nameModulus, msg, Qgis.Info )
        data = {
            'canvas': self.canvas,
            'layers': self.layerImages,
            'filepath': self.pathfileImage
        }
        task = TaskSendImage( self.sc, data )
        task.finish.connect( finished )
        self.taskManager.addTask( task )
        #task.finished( task.run() )

    @pyqtSlot()
    def getFeatures(self):
        def setLayerPolygon():
            def createLayerPolygon():
                def createLayerMemory():
                    atts = {
                        'id_add': 'integer',
                        'total_imgs': 'integer',
                        'images': 'string(254)',
                        'user': 'string(20)',
                        'date_add': 'string(20)',
                        'crs_map': 'string(50)',
                        'extent_map': 'string(200)',
                        'annotation': 'string(100)'
                    }
                    l_fields = [ f"field={k}:{atts[ k ]}" for k in atts ]
                    crs = QgsCoordinateReferenceSystem('EPSG:4326')
                    l_fields.insert( 0, f"polygon?crs={crs.authid().lower()}" )
                    uri = '&'.join( l_fields )
                    return QgsVectorLayer( uri, self.defLayerPolygon['layername'], 'memory' )

                if os.path.isfile( self.defLayerPolygon['filepath'] ):
                    os.remove( self.defLayerPolygon['filepath'] )
                r = { 'isOk': True }
                args = {
                    'layer': createLayerMemory(),
                    'fileName': self.defLayerPolygon['filepath'],
                    'fileEncoding': 'utf-8',
                    'driverName': 'GPKG'
                }
                rc, errmsg = QgsVectorFileWriter.writeAsVectorFormat( **args )
                if not rc == QgsVectorFileWriter.NoError:
                    r = { 'isOk': False, 'message': errmsg }
                if not r['isOk']:
                    return r
                source = "{}|layername={}".format( self.defLayerPolygon['filepath'], self.defLayerPolygon['layername'] )
                r['layer'] = QgsVectorLayer( source, self.defLayerPolygon['layername'], 'ogr' )
                return r

            if self.layerPolygon is None:
                r = self._getFirstLayerPolygon()
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
            tSieve = self.dockWidgetGui.sbRemoveAreaPixels.value() + 1
            tAzimuth = self.dockWidgetGui.sbAzimuthThreshold.value()
            offset = self.dockWidgetGui.spSmoothOffset.value() / 100.0
            viter = self.dockWidgetGui.sbSmoothIteration.value()
            pixelsRemove = None if not self.dockWidgetGui.chkAdjustBorder.isChecked() \
                                else self.dockWidgetGui.sbRemoveAreaPixels.value() + 1
            return {
                'layerPolygon': self.layerPolygon,
                'filepath': self.pathfileImageSelect,
                'id_add': self._getMaximumValueAdd() + 1,
                'user': QgsApplication.userFullName(),
                'annotation': self.dockWidgetGui.leditAnnotation.text(),
                'pixelsRemove': pixelsRemove,
                'smooth': { 'iter': viter, 'offset': offset },
                'sieve': { 'threshold': tSieve, 'connectedness': 4 },
                'azimuth': { 'threshold': tAzimuth }
            }

        def startEditable():
            self.isIniEditable = self.layerPolygon.isEditable()
            if not self.isIniEditable:
                self.layerPolygon.startEditing()

        @pyqtSlot(bool, bool, str)
        def finished(result, isCanceled, message):
            def commit():
                def setRenderLayer():
                    fileStyle = os.path.join( os.path.dirname( __file__ ), "gimpselectionfeature_with_expression.qml" )
                    self.layerPolygon.loadNamedStyle( fileStyle )

                def flashFeatures():
                    geoms = []
                    for feat in self._getIteratorLastFeatures():
                        geoms.append( feat.geometry()  )
                    self.mapCanvasEffects.flash( geoms, self.layerPolygon )

                self.layerPolygon.commitChanges()
                self.layerPolygon.updateExtents()
                if self.isIniEditable:
                    self.layerPolygon.startEditing()
                setRenderLayer()
                flashFeatures()

            self._pushMessageTask( result, isCanceled, message )
            if result and not isCanceled:
                commit()
            self._setEnabledWidgetTransfer(True, True)

        if not setLayerPolygon() or not self._setConnectionSocket():
            return

        self._setEnabledWidgetTransfer(False)
        startEditable() # Task NOT commit
        msg = QCoreApplication.translate('GimpSelectionFeature', 'Adding features...')
        self.msgBar.pushMessage( self.nameModulus, msg, Qgis.Info )
        data = getDataParams()
        task = TaskGetFeatures( self.sc, data )
        task.setDependentLayers( [ self.layerPolygon ] )
        task.finish.connect( finished )
        task.addFeature.connect( self.layerPolygon.addFeature )
        self.taskManager.addTask( task )
        #task.finished( task.run() )

    @pyqtSlot()
    def removeLastFeatures(self):
        self.isIniEditable = self.layerPolygon.isEditable()
        if not self.isIniEditable:
            self.layerPolygon.startEditing()
        for feat in self._getIteratorLastFeatures():
            self.layerPolygon.deleteFeature( feat.id()  )
        self.layerPolygon.commitChanges()
        if self.isIniEditable:
            self.layerPolygon.startEditing()
        self.layerPolygon.updateExtents()
        self.dockWidgetGui.btnRemoveLastFeatures.setEnabled( False )


class TaskBaseGimp(QgsTask):
    finish = pyqtSignal(bool, bool, str)
    def __init__(self, description, socketClient, data):
        """
        TaskBaseGimp: Base Task for send data for Gimp

        :params str description: Description task
        :params socket socket: Socket for send message for Gimp
        :params dict data: parameters for processing, define in subclasses
        """
        super().__init__( description, QgsTask.CanCancel )
        self.socketClient = socketClient
        self.data = data
        self.message = None
        self.paramsSendData = None

    def _sendData(self):
        r = self.socketClient.send( self.paramsSendData )
        if not r['isOk']:
            msg = QCoreApplication.translate('GimpSelectionFeature', 'Error connection GIMP Server: {}' )
            msg = msg.format( r['message'] )
            return { 'isOk': False, 'message': msg }
        data = r['data']
        if data is None:
            msg = "Run IBAMA Plugin, 'IBAMA/Service for save the selected regions', in GIMP!"
            msg = QCoreApplication.translate('GimpSelectionFeature', "Run IBAMA Plugin, 'IBAMA/Service for save the selected regions', in GIMP!" )
            msg = msg.format( msg )
            return { 'isOk': False, 'message': msg }
        return data
        
    # Overwrite QgsTask methods
    def run(self):
        # Overwrite by subclass
        return True

    def finished(self, result):
        self.finish.emit( result, self.isCanceled(), self.message )

    def cancel(self):
        self.message = QCoreApplication.translate('GimpSelectionFeature', 'Cancel by user')
        super().cancel()


class TaskSendImage(TaskBaseGimp):
    def __init__(self, socketClient, data):
        """
        TaskSendImage: Task for create canvas image canvas and send message to Gimp

        :params socket socket: Socket for send message for Gimp
        :params dict data: parameters for create image canvas
                        'canvas': MapCanvas
                        'layers': Image layers
                        'filepath': file path of canvas image
        """
        super().__init__('Send image to Gimp', socketClient, data )
        self.message = QCoreApplication.translate('GimpSelectionFeature', "Sent image '{}' to GIMP")
        self.message = self.message.format( data['filepath'] )

    def _setParamsSendData(self, image):
        e = self.data['canvas'].extent()
        imgWidth, imgHeight = image.width(), image.height()
        resX, resY = e.width() / imgWidth, e.height() / imgHeight
        vmap = { l.name(): l.source() for l in self.data['layers'] }
        self.paramsSendData = {
			'function': 'add_image',
			'filename': self.data['filepath'],
			'paramImage': {
                'extent_map': e.asWktCoordinates(), # xMin, yMin, xMax, yMax,
                'crs_map': self.data['canvas'].mapSettings().destinationCrs().authid(),
                'res': { 'X': resX, 'Y': resY },
                'json_images': json.dumps( vmap )
			}
        }

    def _process(self):
        def finished():
            image = job.renderedImage()
            if bool( self.data['canvas'].property('retro') ):
                image = image.scaled( image.width() / 3, image.height() / 3 )
                image = image.convertToFormat( QImage.Format_Indexed8, Qt.OrderedDither | Qt.OrderedAlphaDither )
            image.save( self.data['filepath'], "TIFF", 100 ) # 100: Uncompressed
            self._setParamsSendData( image )

        settings = QgsMapSettings( self.data['canvas'].mapSettings() )
        settings.setBackgroundColor( QColor( Qt.transparent ) )

        settings.setLayers( self.data['layers'] )
        job = QgsMapRendererParallelJob( settings ) 
        job.start()
        job.finished.connect( finished) 
        job.waitForFinished()

    def run(self):
        self._process()
        r = self._sendData()
        if not r['isOk']:
            self.message = r['message']
            return False
        return True


class TaskGetFeatures(TaskBaseGimp):
    addFeature = pyqtSignal(QgsFeature)
    def __init__(self, socketClient, data):
        """
        TaskGetFeatures: Task for get features from Gimp

        :params socket socket: Socket for send message for Gimp
        :params dict data: parameters for get features
                        'filepath': file path of selection image
                        'layerPolygon': Layer of polygon
                        'smooth': Parameters { 'iter', 'offset' }
                        'sieve': Parameters { 'threshold', 'connectedness' }
                        'azimuth': Parameters { 'threshold' }
        """
        super().__init__('Get features from Gimp', socketClient, data )
        self.project = QgsProject.instance()
        self.message = QCoreApplication.translate('GimpSelectionFeature', 'Received features from GIMP')
        self.paramsProcess = data
        self.paramsSendData = {
          'function': 'create_selection_image',
          'filename': data['filepath']
        }

    def _process(self, paramsReceive):
        def getParamsTransform(extent_map, ulPixelSelect, resolution):
            smin, smax = extent_map.split(',')
            ulX = float( smin.split(' ')[0])
            ulY = float( smax.strip().split(' ')[1])
            ulX_SelImage = ulX + ulPixelSelect['X'] * resolution['X']
            ulY_SelImage = ulY - ulPixelSelect['Y'] * resolution['Y']

            return ( ulX_SelImage,  resolution['X'], 0.0, ulY_SelImage, 0.0, -1 *  resolution['Y'] )

        def getBandSelect():
            ds = gdal.Open( self.paramsProcess['filepath'], gdal.GA_ReadOnly )
            if gdal.GetLastErrorType() != 0:
                ds = None
                return { 'isOk': False, 'message': gdal.GetLastErrorMsg() }

            band = ds.GetRasterBand( 1 )
            band.SetNoDataValue( 0.0 )
            return { 'isOk': True, 'dataset': ds, 'band': band}

        def polygonizeSelectionBand(ds_Select, band_Select, paramsTransform, wktProj):
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
                            ring.SetPoint_2D( i, points[i][0], points[i][1] )

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

            # Sieve Band
            drvMem = gdal.GetDriverByName('MEM')
            ds_sieve = drvMem.Create( '', ds_Select.RasterXSize, ds_Select.RasterYSize, 1, band_Select.DataType )
            ds_sieve.SetGeoTransform( paramsTransform )
            band_sieve = ds_sieve.GetRasterBand(1)

            p_threshold = self.paramsProcess['sieve']['threshold']
            p_connectedness = self.paramsProcess['sieve']['connectedness']
            gdal.SieveFilter( band_Select, None, band_sieve, p_threshold, p_connectedness, [], callback=None )
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
                ds_poly,layer_poly = None, None
                return { 'isOk': False, 'message': gdal.GetLastErrorMsg() }

            # Get Geoms - Apply Azimuth tolerance
            geoms = []
            layer_poly.SetAttributeFilter("dn = 255")
            p_threshold = self.paramsProcess['azimuth']['threshold']
            if p_threshold > 0:
                p_threshold = float( p_threshold )
                for feat in layer_poly:
                    geom = feat.GetGeometryRef()
                    setGeomAzimuthTolerance( geom, p_threshold )
                    geoms.append( geom.Clone() )
            else:
                for feat in layer_poly:
                    geoms.append( feat.GetGeometryRef().Clone() )

            ds_poly,layer_poly = None, None
            return { 'isOk': True, 'geoms': geoms }

        def calcAreaPixelInLayerPolygon(crs_map, paramsTransform):
            crsImage = QgsCoordinateReferenceSystem( crs_map )
            crsLayer = self.paramsProcess['layerPolygon'].crs()
            ct =  QgsCoordinateTransform( crsImage, crsLayer, QgsCoordinateTransformContext() )
            p1 = ct.transform( paramsTransform[0], paramsTransform[3] )
            p2 = ct.transform( p1.x() + paramsTransform[1], p1.y() + paramsTransform[5] )
            dist = p1.distance( p2 )
            return dist * dist

        def getAttributes(json_images, crs_map, extent_map):
            v_json = json.loads( json_images )
            html  = getHtmlTreeMetadata( v_json, '')
            sdatetime = str( datetime.datetime.today().replace(microsecond=0) )
            return {
                'images': html,
                'total_imgs': len( v_json ),
                'crs_map': crs_map,
                'extent_map': extent_map,
                'date_add': sdatetime,
                'id_add': self.paramsProcess['id_add'],
                'user': self.paramsProcess['user'],
                'annotation': self.paramsProcess['annotation']
            }

        def addFeatures(geoms, attributes, areaPixel):
            def getGeometryAdjustedBorder(geom, areaMinInLayer):
                def getGeomPolygonRing(rings, idRing):
                    # rings = [ QgsPointXY ]
                    ringPoints = [ QgsPoint( p ) for p in rings[ idRing  ] ]  # [ QgsPoint ]
                    line = QgsLineString( ringPoints )
                    del ringPoints[:]
                    polygon = QgsPolygon()
                    polygon.setExteriorRing( line )
                    del line
                    return QgsGeometry( polygon )

                def getGeomOutCombines(geom):
                    geomCombines = None
                    iter = self.paramsProcess['layerPolygon'].getFeatures( geom.boundingBox() )
                    feat = QgsFeature()
                    while iter.nextFeature( feat ):
                        g = getGeomPolygonRing( feat.geometry().asPolygon(), 0 )
                        if geom.overlaps( g ):
                            if geomCombines is None:
                                geomCombines = g
                            else:
                                gTemp = geomCombines.combine( g )
                                geomCombines = gTemp
                    return geomCombines

                def getGapsBorder(geom, geomBorder):
                    geomOutRing = getGeomPolygonRing( geom.asPolygon(), 0 )
                    g = geomOutRing.combine( geomBorder )
                    del geomOutRing
                    polygons = g.asPolygon()
                    del polygons[0] # Out ring
                    del g
                    return polygons

                def addGapsInGeom(geom, polygonGaps, areaMinInLayer):
                    geomResult = geom
                    for id in range( len( polygonGaps ) ):
                        g = getGeomPolygonRing( polygonGaps, id )
                        if g.area() <= areaMinInLayer:
                            gTemp = geomResult.combine( g )
                            geomResult = gTemp
                        del g
                    return geomResult

                geomCombines = getGeomOutCombines(geom) # No holes
                if geomCombines is None:
                    return geom
                geomDiff = geom.difference( geomCombines )
                polygonsGap = getGapsBorder( geomDiff, geomCombines )
                return addGapsInGeom( geomDiff, polygonsGap, areaMinInLayer )

            feature = QgsFeature( self.paramsProcess['layerPolygon'].fields() )
            for k in attributes.keys():
                feature.setAttribute( k, attributes[ k ] )

            args = (
                QgsCoordinateReferenceSystem( paramsReceive['crs_map'] ),
                self.paramsProcess['layerPolygon'].crs(),
                self.project
            )
            ct = QgsCoordinateTransform( *args )
            p_iter = self.paramsProcess['smooth']['iter']
            p_offset = self.paramsProcess['smooth']['offset']
            for geom in geoms:
                _geom = QgsGeometry.fromWkt( geom.ExportToIsoWkt() )
                geom.Destroy() # OGR
                _geom.transform( ct )
                geomLayer = _geom.smooth( p_iter, p_offset )
                del _geom
                if not self.paramsProcess['pixelsRemove'] is None:
                    areaMinInLayer = areaPixel * self.paramsProcess['pixelsRemove']
                    geomLayer = getGeometryAdjustedBorder( geomLayer, areaMinInLayer )
                feat = QgsFeature( feature )
                feat.setGeometry( geomLayer )
                self.addFeature.emit( feat )
                del geomLayer

        # Calculate Geometry
        r = getBandSelect()
        if not r['isOk']:
            self.message = r['message']
            return False
        if self.isCanceled():
            r['dataset'], r['band'] = None, None
            return True
        ds_Select = r['dataset']
        band_Select =  r['band']
        args = ( paramsReceive['extent_map'], paramsReceive['ulPixelSelect'], paramsReceive['res'] )
        paramsTransform = getParamsTransform( *args )
        wktProj = QgsCoordinateReferenceSystem( paramsReceive['crs_map'] ).toWkt()
        r = polygonizeSelectionBand( ds_Select, band_Select, paramsTransform, wktProj )
        band_Select, ds_Select = None, None
        if not r['isOk']:
            self.message = r['message']
            return False
        if self.isCanceled():
            return True
        geoms = r['geoms']
        totalFeats = len( geoms )
        if totalFeats  == 0:
            msg = QCoreApplication.translate('GimpSelectionFeature', "Not found features in selections ('{}')")
            msg = msg.format( self.paramsProcess['filepath'] )
            self.message = msg
            return False
        # Send data for create Features
        msg = QCoreApplication.translate('GimpSelectionFeature', "Added {} features in '{}'")
        msg = msg.format( totalFeats, self.paramsProcess['layerPolygon'].name() )
        self.message = msg
        args = ( paramsReceive['json_images'],  paramsReceive['crs_map'], paramsReceive['extent_map'] )
        atts = getAttributes( *args )
        areaPixel = calcAreaPixelInLayerPolygon( paramsReceive['crs_map'], paramsTransform )
        addFeatures( geoms, atts, areaPixel )
        return True

    def run(self):
        r = self._sendData()
        if not r['isOk']:
            self.message = r['message']
            return False
        return self._process( r )
