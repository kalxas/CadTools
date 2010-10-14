from cadtools import CadTools

def name():
    return "CadTools"

def description():
    return "Some tools to perform cad like functions."

def version():
    return "0.4.9"

def qgisMinimumVersion():
    return "1.3"

def authorName():
    return "Stefan Ziegler"

def classFactory(iface):
    return CadTools(iface)