# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : Json2HTML
Description          : Function to get dictionary(json) and create HTML how a list
Date                 : June, 2018
copyright            : (C) 2018 by Luiz Motta
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
def getHtmlTreeMetadata(value, html):
    if isinstance( value, dict ):
        html += "<ul>"
        for key, val in sorted( iter( value.items() ) ):
            if not isinstance( val, dict ):
                html += "<li>%s: %s</li> " % ( key, val )
            else:
                html += "<li>%s</li> " % key
            html = getHtmlTreeMetadata( val, html )
        html += "</ul>"
        return html
    return html
