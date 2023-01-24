# -*- coding: utf-8 -*-
"""
/***************************************************************************
 eTracability
                                 A QGIS plugin
 This plugin adds automatic attributes to vector layers, that track who updated or created features, and when. Also adds automatic area and length calculations to Polygons and Lines
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2023-01-24
        copyright            : (C) 2023 by LC Ecological Services/DeltaV Geo
        email                : David@deltavgeo.co.uk
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load eTracability class from file eTracability.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .e_tracability import eTracability
    return eTracability(iface)