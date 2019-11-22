#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : Sockets server and client
Description          : Enable socket service
Date                 : November, 2019
copyright            : (C) 2019 by Luiz Motta
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
__date__ = '2019-11-19'
__copyright__ = '(C) 2019, Luiz Motta'
__revision__ = '$Format:%H$'


# Use by Python 2 and Python 3

import socket, json

SOCKET_CONFIG = {
    'type': (socket.AF_INET, socket.SOCK_STREAM),
    'addr': ('127.0.0.1', 10000), # ( IP, port)
    'total': 1, # Total connections
    'size': 4096, # Size of message
}

class SocketService(object):
    def __init__(self):
        super( SocketService, self ).__init__()
        self.socket = socket.socket( *SOCKET_CONFIG['type'] )

    def __del__(self):
        self.socket.close()
        self.socket = None

    def init(self):
        try:
            self.socket.bind( SOCKET_CONFIG['addr'] )
        except socket.error as msg_socket:
            return { 'isOk': False, 'message': str( msg_socket ) }
        self.socket.listen( SOCKET_CONFIG['total'] )
        return { 'isOk': True }

    def receive(self, funcProcess):
        def receiveData(socketClient):
            def initSocket():
                socketClient.close()
                self.socket.close()
                self.socket = socket.socket( *SOCKET_CONFIG['type'] )

            try:
                data = socketClient.recv( SOCKET_CONFIG['size'] )
            except socket.error as msg_socket:
                return { 'isOk': False, 'message': str( msg_socket ) }
            if not data:
                initSocket()
                return { 'isOk': False, 'message': 'Close conection by client' }
            return { 'isOk': True, 'data': data }
        """
        funcProcess( dict data )
        """
        ( socketClient, _address ) = self.socket.accept()
        while True:
            r = receiveData(socketClient)
            if not r['isOk']:
                funcProcess( r )
                break
            try:
                data = json.loads( r['data'] )
            except ValueError:
                continue
            r['data'] = data
            r['socket'] = socketClient
            funcProcess( r )


class SocketClient(object):
    def __init__(self):
        super( SocketClient, self ).__init__()
        self.socket = socket.socket( *SOCKET_CONFIG['type'] )
        self.hasConnect = False
    
    def __del__(self):
        if self.hasConnect:
            self.socket.close()
        self.socket = None

    def connect(self):
        try:
            self.socket.connect( SOCKET_CONFIG['addr'] )
        except socket.error as msg_socket:
            return { 'isOk': False, 'message': str( msg_socket ) }
        self.hasConnect = True
        return { 'isOk':True }

    def send(self, data):
        def reconnect():
            self.socket.close()
            self.socket = socket.socket( *SOCKET_CONFIG['type'] )
            self.hasConnect = False
            self.connect()

        send_data = json.dumps( data )
        self.socket.send( send_data.encode() )
        try:
            receive_data = self.socket.recv( SOCKET_CONFIG['size'] )
        except socket.error as msg_socket:
            return { 'isOk': False, 'message':  str( msg_socket ) }
        if len( receive_data ) == 0:
            reconnect()
            return { 'isOk': True, 'data': None }
        return { 'isOk': True, 'data': json.loads( receive_data ) }
