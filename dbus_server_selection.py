#!/usr/bin/env python

from gimpfu import *
from gimpshelf import shelf

from os import path
import dbus, json, gobject
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop

# DEBUG
pydev_path = '/home/lmotta/eclipse/plugins/org.python.pydev_3.9.2.201502050007/pysrc/'
def startPyDevClient():
  import sys
  sys.path.append(pydev_path)
  started = False
  try:
    import pydevd
    pydevd.settrace(port=5678, suspend=False)
    started = True
  except:
    pass
  return started
####

id_bus_name = "gimp.plugin.dbus.selection"
id_bus_object_path = "/%s" % id_bus_name.replace( '.', '/' )
titleServer = "Selection save image Server"
class DBusService(dbus.service.Object):
  def __init__(self):
    self.addedImages = {}

  def run(self, image):
    DBusGMainLoop(set_as_default=True)
    bus_name = dbus.service.BusName( id_bus_name, bus=dbus.SessionBus())
    dbus.service.Object.__init__(self, bus_name, id_bus_object_path )

    self._loop = gobject.MainLoop()
    gimp.message( "%s Running..." % titleServer )

    vreturn = self.isTifImage( image.filename )
    if not vreturn['isOk']:
      gimp.message( "%s Running -- CLOSE and OPEN the TIF image!!!" % titleServer)

    self._loop.run()
    gimp.message( "%s stopped!" % titleServer)

  def existImage(self, filename):
    if self.addedImages.has_key( filename ):
      image = self.addedImages[ filename ]['image']
      if pdb.gimp_image_is_valid( image ):
        return { 'isOk': True, 'image': image }

    images = gimp.image_list()
    if len ( images ) == 0:
      return { 'isOk': False, 'msg': "Not exist images"  }
    images_by_filename = filter( lambda item: item.filename == filename, images )
    del images
    if len ( images_by_filename ) == 0:
      return { 'isOk': False, 'msg': "Not exist image '%s'" % filename }
    image = images_by_filename[0]
    del images_by_filename
    if not pdb.gimp_image_is_valid( image ):
      return { 'isOk': False, 'msg': "Image '%s' is not valid" % filename }

    return { 'isOk': True, 'image': image }

  def exist_selection_image(self, filename):
    vreturn = self.existImage( filename )
    if not vreturn['isOk']:
      return vreturn

    image = vreturn['image']

    vreturn = self.isTifImage( filename )
    if not vreturn['isOk']:
      return vreturn

    non_empty, x1, y1, x2, y2 = pdb.gimp_selection_bounds( image )
    if non_empty == 0:
      return { 'isOk': False, 'msg': "No selection in '%s'" % filename }

    return { 'isOk': True, 'image': image }

  def isTifImage(self, filename):
    isTif = path.splitext( filename )[1].upper() == '.TIF'
    if not isTif:
      return { 'isOk': False, 'msg': "Image '%s' need be TIF" % filename }
    #
    return { 'isOk': True }

  @dbus.service.method( dbus_interface=id_bus_name )
  def add_image(self, filename):
    vreturn = self.isTifImage( filename )
    if not vreturn['isOk']:
      return json.dumps( vreturn )

    vreturn = self.existImage( filename )
    if vreturn['isOk']:
      msg = "Image '%s' is already open"  % filename
      return json.dumps( { 'isOk': False, 'msg': msg} )

    image = pdb.file_tiff_load( filename, "" )
    display = gimp.Display( image )
    self.addedImages[ filename ] = { 'display': display, 'image': image }
    msg = "Added image '%s'" % filename
    return json.dumps( { 'isOk': True, 'msg': msg } )

  @dbus.service.method( dbus_interface=id_bus_name )
  def add_image_overwrite(self, filename):
    if self.addedImages.has_key( filename ):
      # Check is valid Display (can remove by GIMP user)
      display = self.addedImages[ filename ]['display']
      if pdb.gimp_display_is_valid( display ):
        pdb.gimp_display_delete( display )  
      del self.addedImages[ filename ]

    image = pdb.file_tiff_load( filename, "" )
    display = gimp.Display( image )
    self.addedImages[ filename ] = { 'display': display, 'image': image }
    msg = "Added image '%s'" % filename
    return json.dumps( { 'isOk': True, 'msg': msg } )

  @dbus.service.method( dbus_interface=id_bus_name)
  def create_selection_image(self, filename):
    vreturn = self.exist_selection_image( filename )
    if not vreturn['isOk']:
      return json.dumps( vreturn )

    non_empty, x1, y1, x2, y2 = pdb.gimp_selection_bounds( vreturn['image'] )
    selimage = vreturn['image'].selection.image.duplicate()
    selimage.crop( x2 - x1, y2 - y1, x1, y1 )
    channel = pdb.gimp_selection_save( selimage )
    filename = "%s_select.tif" % path.splitext( filename )[0]
    pdb.file_tiff_save( selimage, channel, filename, "", 0)
    pdb.gimp_image_delete( selimage )
    #
    vreturn = { 'isOk': True, 'tiePoint': ( x1, y1 ), 'filename': filename }
    return json.dumps( vreturn )

  @dbus.service.method( dbus_interface=id_bus_name)
  def quit(self):
    """removes this object from the DBUS connection and exits"""
    self.remove_from_connection()
    shelf['dbus_server'] = False
    self._loop.quit()
    #
    vreturn = { 'isOk': True }
    return json.dumps( vreturn )

def run(image, drawable):
  
  #startPyDevClient()
  if shelf.has_key('dbus_server') and shelf['dbus_server']:
    gimp.message( "WARNING: DBUS server is already running!")
    return
  else:
    shelf['dbus_server'] = True  

  DBusService().run( image )

register(
  "python_fu_dbus-server",
  titleServer, titleServer,
  "Luiz Motta", "IBAMA", "2016",
  "<Image>/Tools/IBAMA/%s" % titleServer,
  "*",
  [],
  [],
  run
)

main()
