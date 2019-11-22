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


import os

from qgis.PyQt.QtCore import Qt, QObject, pyqtSlot, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from qgis.core import Qgis

from .gimpselectionfeature import DockWidgetGimpSelectionFeature
from .translate import Translate


def classFactory(iface):
  return GimpSelectionFeaturePlugin( iface )

class GimpSelectionFeaturePlugin(QObject):

  def __init__(self, iface):
    super().__init__()
    self.iface = iface
    self.name = u"&Gimp Selection Feature"
    self.dock = None
    self.translate = Translate( 'gimpselectionfeature' )

  def initGui(self):
    name = "Gimp Selection Feature"
    about = QCoreApplication.translate('GimpSelectionFeature', 'Adding selected area in GIMP how a feature')
    icon = QIcon( os.path.join( os.path.dirname(__file__), 'gimpselectionfeature.svg' ) )
    self.action = QAction( icon, name, self.iface.mainWindow() )
    self.action.setObjectName( name.replace(' ', '') )
    self.action.setWhatsThis( about )
    self.action.setStatusTip( about )
    self.action.setCheckable( True )
    self.action.triggered.connect( self.run )

    self.iface.addRasterToolBarIcon( self.action )
    self.iface.addPluginToRasterMenu( self.name, self.action )

    self.dock = DockWidgetGimpSelectionFeature( self.iface )
    self.iface.addDockWidget( Qt.RightDockWidgetArea , self.dock )
    self.dock.visibilityChanged.connect( self.dockVisibilityChanged )

  def unload(self):
    self.iface.removeRasterToolBarIcon( self.action )
    self.iface.removePluginRasterMenu( self.name, self.action )

    self.dock.close()
    self.dock.clean()
    self.dock = None

    del self.action

  @pyqtSlot()
  def run(self):
    if self.dock.isVisible():
      self.dock.hide()
    else:
      self.dock.show()

  @pyqtSlot(bool)
  def dockVisibilityChanged(self, visible):
    self.action.setChecked( visible )
