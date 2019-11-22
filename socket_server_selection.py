#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : Service for save the selected regions
Description          : Plugin for enable service for save selected regions and add image by client
Date                 : June, 2016
copyright            : (C) 2016 by Luiz Motta
email                : motta.luiz@gmail.com
Gimp version         : 2.8 and 2.10

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
import json

#
import sys
sys.path.append(  path.dirname( path.abspath(__file__) ) )
from sockets import SocketService
#

class Service(object):
    titleServer = "Service for save the selected regions"
    @staticmethod
    def printMessage(message):
        pdb.gimp_progress_end()
        gimp.message( message )

    def __init__(self):
        super( Service, self ).__init__()
        self.addedImages = {}
        self.pathfileImage, self.pathfileImageSelect = None, None
        self.paramImage = {}
        self.ss = SocketService()
        self.isVersion2_10 = True if gimp.version[1] == 10 else False
    
    def __del__(self):
        del self.ss

    def run(self):
        def process(response):
            if not response['isOk']:
                self.printMessage( response['message'] )
                gimp_shelf['socket_server'] = False
                return
            data = response['data']
            if not 'function' in data:
                return
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
            functions[ data['function'] ]( response['socket'] )

        r = self.ss.init()
        if not r['isOk']:
            msg = "{}: {}".format( self.titleServer, r['message'])
            self.printMessage( msg )
            gimp_shelf['socket_server'] = False
            return
        msg = "'{}' is runnig...".format( self.titleServer )
        self.printMessage( msg )
        gimp_shelf['socket_server'] = True  
        self.ss.receive( process )

    def _isTifImage(self):
        isTif = path.splitext( self.pathfileImage )[1].upper() == '.TIF'
        if not isTif:
            return { 'isOk': False, 'message': "Image '{}' need be TIF".format( self.pathfileImage ) }
        return { 'isOk': True }

    def add_image(self, socket):
        r = self._isTifImage()
        if not r['isOk']:
            socket.send( json.dumps( r ) )
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
        msg = "Added image '{}'".format( self.pathfileImage )
        socket.send( json.dumps( { 'isOk': True, 'message': msg } ) )

    def create_selection_image(self, socket):
        def existImage():
            if self.pathfileImage in self.addedImages:
                image = self.addedImages[ self.pathfileImage ]['image']
                if pdb.gimp_image_is_valid( image ):
                    return { 'isOk': True, 'image': image }
            images = gimp.image_list()
            if len ( images ) == 0:
                return { 'isOk': False, 'message': "Not exist images"  }
            images_by_filename = [ item for item in images if item.filename == self.pathfileImage ]
            del images
            if len ( images_by_filename ) == 0:
                return { 'isOk': False, 'message': "Not exist image '{}'".format( self.pathfileImage ) }
            image = images_by_filename[0]
            del images_by_filename
            if not pdb.gimp_image_is_valid( image ):
                return { 'isOk': False, 'message': "Image '{}' is not valid".format( self.pathfileImage ) }
            return { 'isOk': True, 'image': image }

        r = existImage()
        if not r['isOk']:
            socket.send( json.dumps( r ) )
            return
        image = r['image']
        r = self._isTifImage()
        if not r['isOk']:
            socket.send( json.dumps( r ) )
            return
        is_empty = pdb.gimp_selection_is_empty( image )
        if is_empty == 1:
            data = { 'isOk': False, 'message': "No selection in '{}'".format( self.pathfileImage) }
            socket.send( json.dumps( data ) )
            return

        _non_empty, x1, y1, x2, y2 = pdb.gimp_selection_bounds( image )
        # Verify Version
        sel_image = image.duplicate() if self.isVersion2_10 else image.selection.image.duplicate()
        #
        sel_image.crop( x2 - x1, y2 - y1, x1, y1 )
        pdb.gimp_selection_sharpen( sel_image )
        channel = pdb.gimp_selection_save( sel_image )
        # Verify Version
        if self.isVersion2_10:
            sel_layer = pdb.gimp_selection_float( channel, 0, 0 ) # Add selection how top layer 
            pdb.gimp_image_remove_layer( sel_image, sel_image.layers[-1] ) # Remove original layer
            pdb.file_tiff_save( sel_image, sel_layer, self.pathfileImageSelect, '', 0)
        else:
            pdb.file_tiff_save( sel_image, channel, self.pathfileImageSelect, "", 0)
        #
        pdb.gimp_image_delete( sel_image )
        data = {
            'isOk': True,
            'ulPixelSelect': { 'X': x1, 'Y': y1 }
        }
        data.update( self.paramImage )
        socket.send( json.dumps( data ) )


def run():
    if gimp_shelf.has_key('socket_server') and gimp_shelf['socket_server']:
        msg = "WARNING: '{}' is already running!".format( Service.titleServer )
        Service.printMessage( msg  )
        return

    serv = Service()
    serv.run()
    del serv

register(
    "python_fu_socket_server",
    Service.titleServer, Service.titleServer,
    "Luiz Motta", "IBAMA", "2016",
    "<Toolbox>/IBAMA/{}".format( Service.titleServer ),
    "",
    [],
    [],
    run
)

main()
