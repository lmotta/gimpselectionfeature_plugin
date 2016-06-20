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
import os, stat, sys, re, shutil, filecmp

from PyQt4 import ( QtGui, QtCore )
from qgis import gui as QgsGui

from gimpselectionfeature import ( DockWidgetGimpSelectionFeature, GimpSelectionFeature )


# darwin is MAC
# http://gimpforums.com/thread-what-is-my-gimp-profile-and-where-do-i-find-it

def classFactory(iface):
  return GimpSelectionFeaturePlugin( iface )

class GimpSelectionFeaturePlugin:

  def __init__(self, iface):
    self.iface = iface
    self.name = u"&Gimp Selection Feature"
    self.dock = self.exitsPluginGimp = None

  def initGui(self):
    def setExistsPluginGimp():
      def getDirGimp():
        mask = r"\.gimp-[0-9]+\.[0-9]+"
        l_dirGimp = [ f for f in os.listdir( dirHome ) if re.match( mask, f)    ]
        return { 'isOk': False } if len( l_dirGimp ) == 0 else { 'isOk': True, 'dirGimp': os.path.join( dirHome, l_dirGimp[0] ) }

      def getDirGimpOSX():
        #  /Users/{your_id}/Library/GIMP/2.8/ or
        #   /Users/{your_id}/Library/Application Support/GIMP/2.8/ 
        mask = r"[0-9]+\.[0-9]+"
        
        dirHome_libray = "%s/Library" % dirHome
        dirHome_osx = "%s/GIMP" % dirHome_libray
        if not os.path.exists( dirHome_osx ):
          dirHome_osx = "%s/Application Support/GIMP" % dirHome_libray
          if not os.path.exists( dirHome_osx ):
            return { 'isOk': False, 'msg': "Not found diretory GIMP in '%s'" % dirHome_libray }
        
        l_dirGimp = [ f for f in os.listdir( dirHome_osx ) if re.match( mask, f)    ]
        return { 'isOk': False } if len( l_dirGimp ) == 0 else { 'isOk': True, 'dirGimp': os.path.join( dirHome_osx, l_dirGimp[0] ) }

      def copyNewPlugin():
        shutil.copy2( gimpPlugin, gimpPluginInstall )
        if sys.platform != 'win32': # Add executable
          st =  os.stat( gimpPluginInstall )
          os.chmod( gimpPluginInstall, st.st_mode | stat.S_IEXEC )

      nameDirPlugin = 'plug-ins'
      namePlugin = 'socket_server_selection.py'
      dirHome = os.path.expanduser('~')
      functionsDirGimp = {
          'win32': getDirGimp,
          'linux2': getDirGimp,
          'darwin': getDirGimpOSX
      }
      if not sys.platform in functionsDirGimp.keys():
        self.exitsPluginGimp = { 'isOk': False, 'msg': "Not found type System (Windows, Linux or OSX), value system is '%s'" % sys.platform }
        return
      vreturn = functionsDirGimp[ sys.platform ]()
      if not vreturn['isOk']:
        self.exitsPluginGimp = { 'isOk': False, 'msg': "Not found diretory GIMP in '%s'" % dirHome }
        return
      dirPluginGimp = os.path.join( vreturn['dirGimp'], nameDirPlugin )
      if not os.path.exists( dirPluginGimp ):
        self.exitsPluginGimp = { 'isOk': False, 'msg': "Not found plugin's diretory in GIMP in '%s'" % dirPluginGimp }
        return
      gimpPlugin = os.path.join( os.path.dirname(__file__), namePlugin )
      gimpPluginInstall = os.path.join( dirPluginGimp, namePlugin )
      if not os.path.exists( gimpPluginInstall ) or not filecmp.cmp( gimpPlugin, gimpPluginInstall ):
        copyNewPlugin()

      self.exitsPluginGimp = { 'isOk': True }

    name = "Gimp Selection Feature"
    about = "Adding selected area in GIMP how a feature in memory layer"
    icon = QtGui.QIcon( os.path.join( os.path.dirname(__file__), 'gimpselectionfeature.svg' ) )
    self.action = QtGui.QAction( icon, name, self.iface.mainWindow() )
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
    self.iface.addDockWidget( QtCore.Qt.RightDockWidgetArea , self.dock )
    self.dock.visibilityChanged.connect( self.dockVisibilityChanged )

  def unload(self):
    self.iface.removeRasterToolBarIcon( self.action )
    self.iface.removePluginRasterMenu( self.name, self.action )

    if self.exitsPluginGimp['isOk']:
      self.dock.close()
      del self.dock
      self.dock = None

    del self.action

  @QtCore.pyqtSlot()
  def run(self):
    if not self.exitsPluginGimp['isOk']:
      ( t, m ) = ( GimpSelectionFeature.nameModulus, self.exitsPluginGimp['msg'] )
      self.iface.messageBar().pushMessage( t, m, QgsGui.QgsMessageBar.CRITICAL, 5 )
      self.action.setChecked( False )
      return

    if self.dock.isVisible():
      self.dock.hide()
    else:
      self.dock.show()

  @QtCore.pyqtSlot(bool)
  def dockVisibilityChanged(self, visible):
    self.action.setChecked( visible )
