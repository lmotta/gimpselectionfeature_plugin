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
import os.path

from PyQt4 import ( QtGui, QtCore )

from gimpselectionfeature import DockWidgetGimpSelectionFeature

def classFactory(iface):
  return GimpSelectionFeaturePlugin( iface )

class GimpSelectionFeaturePlugin:

  def __init__(self, iface):
    self.iface = iface
    self.name = u"&Gimp Selection Feature"
    self.dock = None

  def initGui(self):
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

    self.dock = DockWidgetGimpSelectionFeature( self.iface )
    self.iface.addDockWidget( QtCore.Qt.LeftDockWidgetArea , self.dock )
    self.dock.visibilityChanged.connect( self.dockVisibilityChanged )

  def unload(self):
    self.iface.removeRasterToolBarIcon( self.action )
    self.iface.removePluginRasterMenu( self.name, self.action )

    self.dock.close()
    del self.dock
    self.dock = None

    del self.action

  @QtCore.pyqtSlot()
  def run(self):
    if self.dock.isVisible():
      self.dock.hide()
    else:
      self.dock.show()

  @QtCore.pyqtSlot(bool)
  def dockVisibilityChanged(self, visible):
    self.action.setChecked( visible )
