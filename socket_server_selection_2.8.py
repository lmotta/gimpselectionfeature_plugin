#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : Service for save the selected regions
Description          : Plugin for enable service for save selected regions and add image by client
Date                 : June, 2016
copyright            : (C) 2016 by Luiz Motta
email                : motta.luiz@gmail.com
Gimp version         : 2.8

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
__date__ = '2016-06-01'
__copyright__ = '(C) 2015, Luiz Motta'
__revision__ = '$Format:%H$'


from gimpfu import gimp, pdb, register, main
from gimpshelf import shelf as gimp_shelf

from os import path
import socket, json

class SocketService(object):
  titleServer = "Service for save the selected regions"
  def __init__(self):
    super( SocketService, self ).__init__()
    self.addedImages = {}
    self.pathfileImage, self.pathfileImageSelect = None, None
    self.paramImage = {}
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.conn, self.port = None, 10000
    
  def __del__(self):
    if not self.conn is None:
      self.conn.close()
      self.conn = None

  def run(self):
    # Socket
    try:
      self.sock.bind( ( '127.0.0.1', self.port ) )
    except socket.error as msg_socket:
      msg = "Socket Error: %s" % str( msg_socket )
      gimp.message( "%s: %s!" % ( self.titleServer, msg ) )
      self.quit()
      return
    self.sock.listen( 1 )

    gimp.message( "'%s' is running..." % self.titleServer )
    gimp_shelf['socket_server'] = True  

    self.conn, client = self.sock.accept()
    while True:
      sdata = self.conn.recv(4096)
      if not sdata:
        self.quit() # Call by client sock.close()
        break

      try:
        data = json.loads( sdata )
      except ValueError:
        continue

      if not 'function' in data:
        continue

      if data['function'] == 'add_image':
        self.pathfileImage = data['filename']
        self.paramImage.clear() 
        self.paramImage = data['paramImage']
      else:
        self.pathfileImageSelect = data['filename']

      functions = {
        'add_image':              self.add_image,
        'create_selection_image': self.create_selection_image
      }
      functions[ data['function'] ]()

  def existImage(self):
    if self.pathfileImage in self.addedImages:
      image = self.addedImages[ self.pathfileImage ]['image']
      if pdb.gimp_image_is_valid( image ):
        return { 'isOk': True, 'image': image }

    images = gimp.image_list()
    if len ( images ) == 0:
      return { 'isOk': False, 'message': "Not exist images"  }
    images_by_filename = filter( lambda item: item.filename == self.pathfileImage, images )
    del images
    if len ( images_by_filename ) == 0:
      return { 'isOk': False, 'message': "Not exist image '%s'" % self.pathfileImage }
    image = images_by_filename[0]
    del images_by_filename
    if not pdb.gimp_image_is_valid( image ):
      return { 'isOk': False, 'message': "Image '%s' is not valid" % self.pathfileImage }

    return { 'isOk': True, 'image': image }

  def isTifImage(self):
    isTif = path.splitext( self.pathfileImage )[1].upper() == '.TIF'
    if not isTif:
      return { 'isOk': False, 'message': "Image '%s' need be TIF" % self.pathfileImage }
    #
    return { 'isOk': True }

  def add_image(self):
    r = self.isTifImage()
    if not r['isOk']:
      self.conn.send( json.dumps( r ) )
      return

    if self.pathfileImage in self.addedImages:
      # Check is valid Display (can remove by GIMP user)
      display = self.addedImages[ self.pathfileImage ]['display']
      if pdb.gimp_display_is_valid( display ):
        pdb.gimp_display_delete( display )  
      del self.addedImages[ self.pathfileImage ]

    image = pdb.file_tiff_load( self.pathfileImage, "" )
    display = gimp.Display( image )
    self.addedImages[ self.pathfileImage ] = { 'display': display, 'image': image }
    msg = "Added image '%s'" % self.pathfileImage
    
    self.conn.send( json.dumps( { 'isOk': True, 'message': msg } ) )

  def create_selection_image(self):
    vreturn = self.existImage()
    if not vreturn['isOk']:
      self.conn.send( json.dumps( vreturn ) )
      return
    image = vreturn['image']
    vreturn = self.isTifImage()
    if not vreturn['isOk']:
      self.conn.send( json.dumps( vreturn ) )
      return
    is_empty = pdb.gimp_selection_is_empty( image )
    if is_empty == 1:
      self.conn.send( json.dumps( { 'isOk': False, 'message': "No selection in '%s'" % self.pathfileImage } ) )
      return

    non_empty, x1, y1, x2, y2 = pdb.gimp_selection_bounds( image )
    selimage = image.selection.image.duplicate()
    selimage.crop( x2 - x1, y2 - y1, x1, y1 )
    pdb.gimp_selection_sharpen( selimage )
    channel = pdb.gimp_selection_save( selimage )
    pdb.file_tiff_save( selimage, channel, self.pathfileImageSelect, "", 0)
    pdb.gimp_image_delete( selimage )
    #
    data = {
      'isOk': True,
      'ulPixelSelect': { 'X': x1, 'Y': y1 }
    }
    data.update( self.paramImage )
    self.conn.send( json.dumps( data ) )

  def quit(self):
    gimp.message( "%s: Stopped!" % self.titleServer)
    gimp_shelf['socket_server'] = False
    self.conn = None


def run():
  
  if gimp_shelf.has_key('socket_server') and gimp_shelf['socket_server']:
    gimp.message( "WARNING: '%s' is already running!" % SocketService.titleServer)
    return

  SocketService().run()

register(
  "python_fu_socket_server",
  SocketService.titleServer, SocketService.titleServer,
  "Luiz Motta", "IBAMA", "2016",
  "<Toolbox>/IBAMA/%s" % SocketService.titleServer,
  "",
  [],
  [],
  run
)

main()
