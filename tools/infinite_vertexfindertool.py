# -*- coding: latin1 -*-


from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

# Vertex Finder Tool class
class infinite_VertexFinderTool(QgsMapTool):

  vertexFound = pyqtSignal(object)

  def __init__(self, canvas):
    QgsMapTool.__init__(self,canvas)
    self.canvas=canvas
    # number of marked vertex
    self.count = 0
    # List markers and vertex points
    self.vertexset = []
    #our own fancy cursor
    self.cursor = QCursor(QPixmap(["16 16 3 1",
                                  "      c None",
                                  ".     c #FF0000",
                                  "+     c #FFFFFF",
                                  "                ",
                                  "       +.+      ",
                                  "      ++.++     ",
                                  "     +.....+    ",
                                  "    +.     .+   ",
                                  "   +.   .   .+  ",
                                  "  +.    .    .+ ",
                                  " ++.    .    .++",
                                  " ... ...+... ...",
                                  " ++.    .    .++",
                                  "  +.    .    .+ ",
                                  "   +.   .   .+  ",
                                  "   ++.     .+   ",
                                  "    ++.....+    ",
                                  "      ++.++     ",
                                  "       +.+      "]))
                                  
 
    
 
  def canvasPressEvent(self,event):
    pass
  
  def canvasMoveEvent(self,event):
    pass
  
  def canvasReleaseEvent(self,event):
    #Get the click
    x = event.pos().x()
    y = event.pos().y()
    
    layer = self.canvas.currentLayer()
    
    if layer <> None:
      #the clicked point is our starting point
      startingPoint = QPoint(x,y)
      
      #we need a snapper, so we use the MapCanvas snapper   
      snapper = QgsMapCanvasSnapper(self.canvas)
      
      #we snap to the current layer (we don't have exclude points and use the tolerances from the qgis properties)
      (retval,result) = snapper.snapToCurrentLayer (startingPoint,QgsSnapper.SnapToVertex)
                       
      #so if we don't have found a vertex we try to find one on the backgroundlayer
      if result == []:
          (retval,result) = snapper.snapToBackgroundLayers(startingPoint)
          
      if result <> []:
        for vertex in list(self.vertexset):
            if vertex['p'].snappedVertex.x() == result[0].snappedVertex.x() and vertex['p'].snappedVertex.y() == result[0].snappedVertex.y():
                #marker selected a second time--> delete the maker
                self.canvas.scene().removeItem(vertex['m'])
                self.vertexset.remove(vertex)
                return         
           
      if result <> []: 
        self.vertexset.append(dict(m=None, p=None))

        self.vertexset[-1]['m'] = QgsVertexMarker(self.canvas)
        self.vertexset[-1]['p'] = result[0]

        self.vertexset[-1]['m'].setIconType(1)
        self.vertexset[-1]['m'].setColor(QColor(255,0,0))
        self.vertexset[-1]['m'].setIconSize(12)
        self.vertexset[-1]['m'].setPenWidth (3)
        self.vertexset[-1]['m'].setCenter(self.vertexset[-1]['p'].snappedVertex)

        self.emit(SIGNAL("vertexFound(PyQt_PyObject)"), [self.vertexset])
        
        self.count = self.count + 1
      else:
        #warn about missing snapping tolerance if appropriate
        self.showSettingsWarning()
            
  def showSettingsWarning(self):
    #get the setting for displaySnapWarning
    settings = QSettings()
    settingsLabel = "/UI/displaySnapWarning"
    displaySnapWarning = bool(settings.value(settingsLabel))
    
    #only show the warning if the setting is true
    if displaySnapWarning:    
      m = QgsMessageViewer()
      m.setWindowTitle("Snap tolerance")
      m.setCheckBoxText("Don't show this message again")
      m.setCheckBoxVisible(True)
      m.setCheckBoxQSettingsLabel(settingsLabel)
      m.setMessageAsHtml( "<p>Could not snap vertex.</p><p>Have you set the tolerance in Settings > Project Properties > General?</p>")
      m.showMessage()
    
  def activate(self):
    self.canvas.setCursor(self.cursor)

  def emptyarray(self):
      self.vertexset = []
  
  def deactivate(self):
    for vertex in self.vertexset:
        self.canvas.scene().removeItem(vertex['m'])
        vertex = None
    self.vertexset = []
    self.count = 0 
    pass

  def isZoomTool(self):
    return False
  
  def isTransient(self):
    return False
    
  def isEditTool(self):
    return True
