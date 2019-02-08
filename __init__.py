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
__author__ = 'Luiz Motta'
__date__ = '2016-06-16'
__copyright__ = '(C) 2018, Luiz Motta'
__revision__ = '$Format:%H$'


import os, stat, sys, re, shutil, filecmp

from qgis.PyQt.QtCore import Qt, QObject, pyqtSlot, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from qgis.core import Qgis

from .gimpselectionfeature import ( DockWidgetGimpSelectionFeature, GimpSelectionFeature )
from .translate import Translate


def classFactory(iface):
  return GimpSelectionFeaturePlugin( iface )

class GimpSelectionFeaturePlugin(QObject):

  def __init__(self, iface):
    super().__init__()
    self.iface = iface
    self.name = u"&Gimp Selection Feature"
    self.dock = self.exitsPluginGimp = None
    self.translate = Translate( 'gimpselectionfeature' )

  def initGui(self):
    def setExistsPluginGimp():
      def getDirPluginGimp():
        dirPlugin = None
        mask = r".*gimp.[0-9]+.[0-9]+/%s" % nameDirPlugin # Linux Format
        for root, dirs, files in os.walk( dirHome ):
          if re.match( mask, root.replace('\\', '/'), re.IGNORECASE ):
            dirPlugin = root
            break

        return dirPlugin

      def copyNewPlugin():
        shutil.copy2( gimpPlugin, gimpPluginInstall )
        if sys.platform != 'win32': # Add executable
          st =  os.stat( gimpPluginInstall )
          os.chmod( gimpPluginInstall, st.st_mode | stat.S_IEXEC )

      dirHome = os.path.expanduser('~')
      nameDirPlugin = "plug-ins"
      dirPluginGimp = getDirPluginGimp()
      if dirPluginGimp is None:
        msg = "Not found diretory 'GIMP' or 'GIMP {}' in '{}'".format( nameDirPlugin, dirHome )
        self.exitsPluginGimp = { 'isOk': False, 'msg': msg }
        return

      namePlugin = 'socket_server_selection.py'
      gimpPlugin = os.path.join( os.path.dirname(__file__), namePlugin )
      gimpPluginInstall = os.path.join( dirPluginGimp, namePlugin )
      if not os.path.exists( gimpPluginInstall ) or not filecmp.cmp( gimpPlugin, gimpPluginInstall ):
        copyNewPlugin()

      self.exitsPluginGimp = { 'isOk': True }

    name = "Gimp Selection Feature"
    about = QCoreApplication.translate('GimpSelectionFeature', 'Adding selected area in GIMP how a feature in shapefile')
    icon = QIcon( os.path.join( os.path.dirname(__file__), 'gimpselectionfeature.svg' ) )
    self.action = QAction( icon, name, self.iface.mainWindow() )
    self.action.setObjectName( name.replace(' ', '') )
    self.action.setWhatsThis( about )
    self.action.setStatusTip( about )
    self.action.setCheckable( True )
    self.action.triggered.connect( self.run )

    self.iface.addRasterToolBarIcon( self.action )
    self.iface.addPluginToRasterMenu( self.name, self.action )

    setExistsPluginGimp()
    if not self.exitsPluginGimp['isOk']:
      return

    self.dock = DockWidgetGimpSelectionFeature( self.iface )
    self.iface.addDockWidget( Qt.RightDockWidgetArea , self.dock )
    self.dock.visibilityChanged.connect( self.dockVisibilityChanged )

  def unload(self):
    self.iface.removeRasterToolBarIcon( self.action )
    self.iface.removePluginRasterMenu( self.name, self.action )

    if self.exitsPluginGimp['isOk']:
      self.dock.close()
      del self.dock
      self.dock = None

    del self.action

  @pyqtSlot()
  def run(self):
    if not self.exitsPluginGimp['isOk']:
      ( t, m ) = ( GimpSelectionFeature.nameModulus, self.exitsPluginGimp['msg'] )
      self.iface.messageBar().pushMessage( t, m, Qgis.Critical, 5 )
      self.action.setChecked( False )
      return

    if self.dock.isVisible():
      self.dock.hide()
    else:
      self.dock.show()

  @pyqtSlot(bool)
  def dockVisibilityChanged(self, visible):
    self.action.setChecked( visible )
