# -*- coding: utf-8 -*-
"""
/***************************************************************************
 eTracability
                                 A QGIS plugin
 This plugin adds automatic attributes to vector layers, that track who updated or created features, and when. Also adds automatic area and length calculations to Polygons and Lines
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2023-01-24
        git sha              : $Format:%H$
        copyright            : (C) 2023 by LC Ecological Services/DeltaV Geo
        email                : David@deltavgeo.co.uk
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
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import Qgis
from qgis.utils import iface
from qgis.core import QgsProject
from qgis.core import QgsMapLayer
from qgis.core import QgsVectorLayer
from qgis.core import QgsWkbTypes
from qgis.core import QgsField
from qgis.core import QgsDefaultValue
from qgis.core import QgsMessageLog
from qgis.gui import QgsMessageBar
from qgis.PyQt.QtCore import QVariant

# Initialize Qt resources from file resources.py
from .resources import *
import os.path

def checkAttributes(layer, geometryType):

    # Check if layer is editable
    if not layer.isEditable():
        if(not layer.startEditing()):
            iface.messageBar().pushMessage("Error", "Layer is not editable", level=Qgis.Critical, duration=5)
            exit
    # Check if author is present
    checkAttribute(layer, 'author','Author', QVariant.String, '@user_full_name', False)
    checkAttribute(layer, 'created','Date Created', QVariant.DateTime, 'now()', False)
    checkAttribute(layer, 'updated','Date Updated', QVariant.DateTime, 'now()', True)

    if geometryType == QgsWkbTypes.LineGeometry:
        checkAttribute(layer, 'length','length', QVariant.Int, '$length', True)
        updateAttribute(layer, 'length')
                
    if geometryType == QgsWkbTypes.PolygonGeometry:
        checkAttribute(layer, 'area','area', QVariant.Double, 'round($area/10000,4)', True)
        updateAttribute(layer, 'area')
        
    layer.updateFields()
    #Save the changes
    layer.commitChanges()


def setReadOnlyAttribute(layer, attribute_index):
    form_config = layer.editFormConfig()
    form_config.setReadOnly(attribute_index, True)
    layer.setEditFormConfig(form_config)

def checkAttribute(layer, attribute_name, alias, attribute_type, default_value, applyOnUpdate, readOnly = True):
    # Check if attribute is present
    attributeIndex = layer.fields().indexFromName(attribute_name)
    aliasIndex = layer.fields().indexFromName(alias)
    if attributeIndex == -1 and aliasIndex == -1:
        print("Layer" + layer.name() + " does not have attribute " + attribute_name + " or alias " + alias)
        # If the attribute isn't present and the alias is also not present, create the column
        if (layer.addAttribute(QgsField(attribute_name, attribute_type))):
            print("Layer" + layer.name() + " created attribute " + attribute_name)
            attributeIndex = layer.fields().indexFromName(attribute_name)  
            setDefaultValues(layer, attributeIndex, default_value, applyOnUpdate, readOnly)
            #Set the friendly alias for the layer
            setAlias(layer, attributeIndex, alias)
        #Because Shapefiles are a piece of crap....
        elif (attribute_type == QVariant.DateTime):
            print("Layer" + layer.name() + " created attribute " + attribute_name + " as a Date, as it did not create it as a DateTime, possibly because the file is a shapefile")
            checkAttribute(layer, attribute_name,alias, QVariant.Date, default_value, applyOnUpdate, readOnly)
        else:
            iface.messageBar().pushMessage("Error", "Error creating attribute " + attribute_name, level=Qgis.Critical, duration=5)
            exit
    else:
        attributeIndex = max(attributeIndex, aliasIndex)
        # If the attribute is present already, confirm the data type
        if layer.fields().field(attributeIndex).type() != attribute_type:
            # If the data type is wrong, delete the column and create it again

            #Check whether the data type is a DateTime, but the column is a Date
            if (layer.fields().field(attributeIndex).type() == QVariant.Date and attribute_type == QVariant.DateTime):
                print("Layer" + layer.name() + " has attribute " + attribute_name + " as a Date, so it may be a shapefile, we'll just make sure the default value is set")
                setDefaultValues(layer, attributeIndex, default_value, applyOnUpdate, readOnly)
            
            #Otherwise, delete the column and create it again
            elif (layer.deleteAttribute(attributeIndex)):
                
                if (layer.addAttribute(QgsField(attribute_name, attribute_type))):
                    attributeIndex = layer.fields().indexFromName(attribute_name)
                    print("Layer" + layer.name() + " created attribute " + attribute_name + "After deleting the previous, because the data types didn't match")
                    #Set the default values for the form
                    setDefaultValues(layer, attributeIndex, default_value, applyOnUpdate, readOnly)
                    # Set the default values for existing geometry
                    updateAttribute(layer, attribute_name)
        else:
            # If the data type is correct, set the default values for the form
            print("Layer" + layer.name() + " has attribute " + attribute_name + " with the correct data type, so we're just going to update the default values")
            setDefaultValues(layer, attributeIndex, default_value, applyOnUpdate, readOnly)

#Set the attributes to the default value for existing geometry
def updateAttribute(layer, attribute_name):
    attributeIndex = layer.fields().indexFromName(attribute_name)
    if attributeIndex != -1:
        for feat in layer.getFeatures():
            layer.changeAttributeValue(feat.id(), attributeIndex, 0)

def setDefaultValues(layer, attributeIndex, default_value, applyOnUpdate, readOnly = True):
    layer.setDefaultValueDefinition(attributeIndex, QgsDefaultValue(default_value,applyOnUpdate=applyOnUpdate))
    if readOnly:
        setReadOnlyAttribute(layer, attributeIndex)

def setAlias(layer, attributeIndex, alias):
    layer.setFieldAlias(attributeIndex, alias)

class eTracability:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'eTracability_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&eTracability Automatic Accountability Tracker')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('eTracability', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/e_tracability/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'eTraceability - Current layer'),
            callback=self.run_single,
            parent=self.iface.mainWindow())

        # Icon for multi-layer processing
        icon_path = ':/plugins/e_tracability/iconmultiple.png'
        self.add_action(
            icon_path,
            text=self.tr(u'eTraceability - All layers'),
            callback=self.run,
            parent=self.iface.mainWindow())
        
        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginVectorMenu(
                self.tr(u'&eTraceability Automatic Accountability Tracker'),
                action)
            self.iface.removeToolBarIcon(action)


    def run(self):
        project = QgsProject.instance()
        # Get the layers
        layerList = project.mapLayers()

        for layer in layerList.values():
            if layer.type() == QgsMapLayer.VectorLayer:
                checkAttributes(layer, layer.geometryType())
        iface.messageBar().pushMessage("eTraceability", "Done!", level=Qgis.Info, duration=5)

    def run_single(self):
        project = QgsProject.instance()
        # Get current layer
        layer = self.iface.activeLayer()
        if layer.type() == QgsMapLayer.VectorLayer:
            checkAttributes(layer, layer.geometryType())
        iface.messageBar().pushMessage("eTraceability", "Done!", level=Qgis.Info, duration=5)