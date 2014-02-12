# -*- coding: latin1 -*-
"""
/***************************************************************************
    Align nodes, based on ArcIntersectionTool (Stefan Ziegler)
    and Numerical Vertex Edit plugin (Cédric Moeri).
                              -------------------
        begin                : February 2014
        copyright            : (C) 2014 by Christian Grossegger
        email                : chr.grossegger@gmail.com
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
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *

# Initialize Qt resources from file resources.py
from cadtools import resources

#Import own classes and tools
from infinite_vertexfindertool import infinite_VertexFinderTool
import cadutils

class alignNodeTool:
    
        def __init__(self, iface,  toolBar):
            # Save reference to the QGIS interface
            self.iface = iface
            self.canvas = self.iface.mapCanvas()
            
            # Points and Markers
            self.vertexU = None
            
            # Create actions 
            self.act_alignnode_left = QAction(QIcon(":/plugins/cadtools/icons/alignnode_left.png"), QCoreApplication.translate("ctools", "Align Nodes left"),  self.iface.mainWindow())
            self.act_alignnode_right = QAction(QIcon(":/plugins/cadtools/icons/alignnode_right.png"), QCoreApplication.translate("ctools", "Align Nodes right"),  self.iface.mainWindow())
            self.act_alignnode_top = QAction(QIcon(":/plugins/cadtools/icons/alignnode_top.png"), QCoreApplication.translate("ctools", "Align Nodes top"),  self.iface.mainWindow())
            self.act_alignnode_bottom = QAction(QIcon(":/plugins/cadtools/icons/alignnode_bottom.png"), QCoreApplication.translate("ctools", "Align Nodes bottom"),  self.iface.mainWindow())
            
            self.act_sXv= QAction(QIcon(":/plugins/cadtools/icons/selectXpoints.png"), QCoreApplication.translate("ctools", "Select X Vertex Points"),  self.iface.mainWindow())
            self.act_sXv.setCheckable(True)  
            self.act_sXv.setEnabled(False)
            self.act_alignnode_left.setEnabled(False)
            self.act_alignnode_right.setEnabled(False)
            self.act_alignnode_top.setEnabled(False)
            self.act_alignnode_bottom.setEnabled(False)
            
            # Connect to signals for button behaviour      
            self.act_alignnode_left.triggered.connect(lambda: self.align('left'))
            self.act_alignnode_right.triggered.connect(lambda: self.align('right'))
            self.act_alignnode_top.triggered.connect(lambda: self.align('top'))
            self.act_alignnode_bottom.triggered.connect(lambda: self.align('bottom'))
            self.iface.currentLayerChanged.connect(self.toggle)
            self.act_sXv.triggered.connect(self.sXv)
            self.canvas.mapToolSet.connect(self.deactivate)

            toolBar.addSeparator()
            toolBar.addAction(self.act_sXv)
            toolBar.addAction(self.act_alignnode_left)
            toolBar.addAction(self.act_alignnode_right)
            toolBar.addAction(self.act_alignnode_top)
            toolBar.addAction(self.act_alignnode_bottom)
                        
            # Get the tool
            self.tool = infinite_VertexFinderTool(self.canvas)           
            
        def sXv(self):
            mc = self.canvas
            layer = mc.currentLayer()

            # Set VertexFinderTool as current tool
            mc.setMapTool(self.tool)
            self.act_sXv.setChecked(True)                    
            
            #Connect to the VertexFinderTool
            self.tool.vertexFound.connect(self.storeVertexPointsAndMarkers)

        def storeVertexPointsAndMarkers(self, result):
            self.vertexU = result
    
        def align(self, option):
            self.moveVertex(self.vertexU, option)
            
        def moveVertex(self, result, option):
                coords = []
                snappingResult = None
                for vertex in result[0]:
                    snappingResult = vertex['p']
                    coords.append([snappingResult.snappedVertex.x(),snappingResult.snappedVertex.y()])

                if option == 'left':
                    seq = min(coords, key=lambda x: x[0])
                elif option == 'right':
                    seq = max(coords, key=lambda x: x[0])
                elif option == 'top':
                    seq = max(coords, key=lambda x: x[1])
                elif option == 'bottom':
                    seq = min(coords, key=lambda x: x[1])
  
                for vertex in result[0]:
                    marker = vertex['m']
                    snappingResult = vertex['p']                
                    #The vertex that is found by the tool:
                    vertexCoords = snappingResult.snappedVertex #vertexCoord are given in crs of the project
                    vertexNr = snappingResult.snappedVertexNr
                    geometry = snappingResult.snappedAtGeometry
                    layer = snappingResult.layer
                    try:
                      layerSrs = layer.srs() #find out the srs of the layer
                    except AttributeError: #API version >1.8
                      layerSrs = layer.crs() #find out the srs of the layer
                    
                    #find out which is the current crs of the project
                    projectSrsEntry = QgsProject.instance().readEntry("SpatialRefSys","/ProjectCRSProj4String")
                    projectSrs = QgsCoordinateReferenceSystem()
                    projectSrs.createFromProj4(projectSrsEntry[0])
                    
                    #set up a coordinate transformation to transform the vertex coord into the srs of his layer
                    transformer= QgsCoordinateTransform (projectSrs, layerSrs)
                    
                    if option == 'left' or option == 'right':
                        transformedPoint = transformer.transform(float(seq[0]),float(vertexCoords.y()))
                    else:
                        transformedPoint = transformer.transform(float(vertexCoords.x()),float(seq[1]))
                        
                     
                    #if the transformation is successful, we move the vertex to his new place else we inform the user that there is something wrong
                    if (type(transformedPoint.x()).__name__=='double' and type(transformedPoint.y()).__name__=='double') or (type(transformedPoint.x()).__name__=='float' and type(transformedPoint.y()).__name__=='float'):
                      layer.moveVertex(transformedPoint.x(), transformedPoint.y(),geometry,vertexNr)
                    else:
                      QMessageBox.critical(self.iface.mainWindow(), "Error while transforming the vertex", "Please Report this error message to the developer.")
                  
                    #Now refresh the map canvas 
                    self.canvas.refresh()
                    
                    #At last we have to delete the marker
                    self.canvas.scene().removeItem(marker)
                    del marker
                result = []
                self.vertexU = []
                self.tool.emptyarray()
        

        def toggle(self):
            mc = self.canvas
            layer = mc.currentLayer()
            #Decide whether the plugin button/menu is enabled or disabled.
            if layer <> None:
                # Only for vector layers.
                type = layer.type()
                if type == 0:
                    gtype = layer.geometryType()
                    if layer.isEditable():
                        self.act_sXv.setEnabled(True)
                        self.act_alignnode_left.setEnabled(True)
                        self.act_alignnode_right.setEnabled(True)
                        self.act_alignnode_top.setEnabled(True)
                        self.act_alignnode_bottom.setEnabled(True)
                        layer.editingStopped.connect(self.toggle)
                        try:
                            layer.editingStarted.disconnect(self.toggle)
                        except TypeError:
                            pass
                    else:
                        self.act_sXv.setEnabled(False)
                        self.act_alignnode_left.setEnabled(False)
                        self.act_alignnode_right.setEnabled(False)
                        self.act_alignnode_top.setEnabled(False)
                        self.act_alignnode_bottom.setEnabled(False)
                        layer.editingStarted.connect(self.toggle)
                        try:
                            layer.editingStopped.disconnect(self.toggle)
                        except TypeError:
                            pass
                            
        def unsetTool(self):
          mc = self.canvas
          mc.unsetMapTool(self.tool)             
            
        def deactivate(self):
            vertexU = None
            #uncheck the button/menu and get rid off the SFtool signal
            self.act_sXv.setChecked(False)
            

