# -*- coding: latin1 -*-

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

# Initialize Qt resources from file resources.py
from cadtools import resources

#Import own classes and tools
from singlesegmentfindertool import SingleSegmentFinderTool
from singlevertexfindertool import SingleVertexFinderTool
from parallellinegui import ParallelLineGui
from parallelline import ParallelLine
import cadutils

class ParallelLineTool:
    
        def __init__(self, iface,  toolBar):
            # Save reference to the QGIS interface
            self.iface = iface
            self.canvas = self.iface.mapCanvas()
            
            # the 2 points of the segment
            # p1 is always the left point
            self.p1 = None
            self.p2 = None
            self.m1 = None
            self.rb1 = QgsRubberBand(self.canvas)
            
            self.pv = None
            self.dummy = False
            
            # Create actions 
            self.action_selectline = QAction(QIcon(":/plugins/cadtools/icons/select1line_v2.png"), QCoreApplication.translate("ctools", "Select one linesegment"),  self.iface.mainWindow())
            self.action_parallelline = QAction(QIcon(":/plugins/cadtools/icons/parallel.png"), QCoreApplication.translate("ctools", "Create parallel line"),  self.iface.mainWindow())
            self.action_selectline.setCheckable(True)      
      
            # Connect to signals for button behaviour      
            self.action_selectline.triggered.connect(self.selectLineSegment)
            self.action_parallelline.triggered.connect(self.showDialog)
            self.canvas.mapToolSet.connect(self.deactivate)

            toolBar.addSeparator()
            toolBar.addAction(self.action_selectline)
            toolBar.addAction(self.action_parallelline)

        def selectLineSegment(self):
            
            mc = self.canvas
            layer = mc.currentLayer()

            # Set SingleSegmentFinder as current tool
            self.tool = SingleSegmentFinderTool(self.canvas)                 
            mc.setMapTool(self.tool)
            self.action_selectline.setChecked(True)      

            # Connect to the SingleSegmentFinderTool
            self.tool.segmentFound.connect(self.storeSegmentPoints)

        def storeSegmentPoints(self,  result):
            if result[0].x() < result[1].x():
                self.p1 = result[0]
                self.p2 = result[1]
            elif result[0].x() == result[1].x():
                self.p1 = result[0]
                self.p2 = result[1]
            else:
                self.p1 = result[1]
                self.p2 = result[0]      
              
            self.dummy = True


        def showDialog(self):
            if self.p1 == None or self.p2 == None or self.dummy == False:
                self.p1 = None
                self.p2 = None
                self.m1 = None                   
                QMessageBox.information(None, QCoreApplication.translate("ctools", "Cancel"), QCoreApplication.translate("ctools", "No linesegment selected."))
            else:
                flags = Qt.WindowTitleHint | Qt.WindowSystemMenuHint | Qt.WindowMaximizeButtonHint  # QgisGui.ModalDialogFlags
                self.ctrl = ParallelLineGui(self.iface.mainWindow(),  flags)
                self.ctrl.initGui()
                self.ctrl.show()
                
                self.ctrl.okClicked.connect(self.createParallelLine)
                self.ctrl.btnSelectVertex_clicked.connect(self.selectVertex)
                self.ctrl.unsetTool.connect(self.unsetTool)
                
                
        def selectVertex(self):            
            p1 = QgsPoint()
            p2 = QgsPoint()
            
            p1.setX(self.p1.x()) 
            p1.setY(self.p1.y()) 
            p2.setX(self.p2.x()) 
            p2.setY( self.p2.y())   
            
            mc = self.canvas
            mc.unsetMapTool(self.tool)  
            self.tool = SingleVertexFinderTool(mc)   
            mc.setMapTool(self.tool)
            
            self.tool.singleVertexFound.connect(self.storeVertexPoint)
            
            self.p1 = p1
            self.p2 = p2            
            
            self.rb1.reset()
            color = QColor(255,0,0)
            self.rb1.setColor(color)
            self.rb1.setWidth(2)

            self.rb1.addPoint(p1)
            self.rb1.addPoint(p2)
            self.rb1.show()            
            
            
        def storeVertexPoint(self,  result):
            self.pv = result[0]
        
        
        def createParallelLine(self, method,  distance):
            # We need this because adding a layer to the mapcanvas deletes everything....
            # Is this true? Why? What happens?
            p1 = QgsPoint()
            p2 = QgsPoint()
            
            p1.setX(self.p1.x()) 
            p1.setY(self.p1.y()) 
            p2.setX(self.p2.x()) 
            p2.setY( self.p2.y())             

            QgsMessageLog.logMessage(str(method), tag="CadTools", level=QgsMessageLog.INFO)
            QgsMessageLog.logMessage(str(distance), tag="CadTools", level=QgsMessageLog.INFO)
            
            if method == "fixed":
                g = ParallelLine.calculateLine(self.p1,  self.p2,  distance)
                cadutils.addGeometryToCadLayer(g)     
                self.canvas.refresh()

            elif method == "vertex":
                QgsMessageLog.logMessage("************************888", tag="CadTools", level=QgsMessageLog.INFO)
                points =  [self.p1,  self.p2]
                g = QgsGeometry.fromPolyline(points)
                g.translate( self.pv.x() - self.p1.x(),  self.pv.y() - self.p1.y() )
#                print str(g)
                cadutils.addGeometryToCadLayer(g)     
                self.canvas.refresh()                
                
#                del self.m1
                
            self.p1 = p1
            self.p2 = p2        
        
        def unsetTool(self):
            QgsMessageLog.logMessage("***************** unset tool", tag="CadTools", level=QgsMessageLog.INFO)
            mc = self.canvas
            mc.unsetMapTool(self.tool)      
            self.action_selectline.setChecked(False)       
            
            
        def deactivate(self):
            QgsMessageLog.logMessage("***************** deactivate parallellinetool", tag="CadTools", level=QgsMessageLog.INFO)
            self.dummy = False
            self.rb1.reset()
            self.action_selectline.setChecked(False)       
            

