#Author-
#Description-
#Fusion360API Python script

import adsk.core, adsk.fusion, traceback

_app = adsk.core.Application.cast(None)
_ui = adsk.core.UserInterface.cast(None)

def run(context):
    try:
        global _app, _ui
        _app = adsk.core.Application.get()
        _ui = _app.userInterface
        des  :adsk.fusion.Design = _app.activeProduct
        root :adsk.fusion.Component = des.rootComponent

        skt :adsk.fusion.Sketch = root.sketches.item(0)
        dim :adsk.fusion.SketchLinearDimension = skt.sketchDimensions.item(0)

        msg :str = 'Enter the value to change (a number other than 0)'
        resValue, cancelled= _ui.inputBox(msg)
        if cancelled: return

        if not isfloat(resValue):
            _ui.messageBox(msg)
            return
    
        msg = ChangeSketchDimensionValue(dim, float(resValue))
        if len(msg) > 0:
            _ui.messageBox(msg)

    except:
        if _ui:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def isfloat(string):
    try:
        float(string) 
        return True
    except ValueError:
        return False

def ChangeSketchDimensionValue(
    dim :adsk.fusion.SketchLinearDimension,
    value :float
    ) -> str:

    def getFix_FreePoint(
        dim :adsk.fusion.SketchLinearDimension):

        pnt1 :adsk.fusion.SketchPoint = dim.entityOne
        pnt2 :adsk.fusion.SketchPoint = dim.entityTwo

        return (pnt1, pnt2) if pnt1.isFixed else (pnt2, pnt1)

    def getTempVec(
        dim :adsk.fusion.SketchLinearDimension,
        fixPnt :adsk.fusion.SketchPoint,
        freePnt :adsk.fusion.SketchPoint
        ) -> adsk.core.Vector3D:

        dimOpes = adsk.fusion.DimensionOrientations
        vec3D = adsk.core.Vector3D

        ori :dimOpes = dim.orientation
        vec :adsk.core.Vector3D = fixPnt.geometry.vectorTo(freePnt.geometry)
        if ori == dimOpes.HorizontalDimensionOrientation:
            vecH :adsk.core.Vector3D = vec3D.create(1, 0, 0)
            if vecH.dotProduct(vec) < 0:
                vec  = vec3D.create(-1, 0, 0)
        elif ori == dimOpes.VerticalDimensionOrientation:
            vecV :adsk.core.Vector3D = vec3D.create(0, 1, 0)
            if vecV.dotProduct(vec) < 0:
                vec  = vec3D.create(0,-1, 0)
        else:
            vec = fixPnt.geometry.vectorTo(freePnt.geometry)
            vec.normalize
        return vec
    
    def initPnt(
        refPnt :adsk.fusion.SketchPoint,
        vec :adsk.core.Vector3D
        ) -> adsk.fusion.SketchPoint:

        skt :adsk.fusion.Sketch = refPnt.parentSketch

        geo :adsk.core.Point3D = refPnt.worldGeometry
        geo.translateBy(vec)

        pnt :adsk.core.SketchPoint = skt.sketchPoints.add(geo)
        return pnt

    def initDimension(
        refDim :adsk.fusion.SketchLinearDimension,
        fixPnt :adsk.fusion.SketchPoint,
        tgtPnt :adsk.fusion.SketchPoint
        ) -> adsk.fusion.SketchLinearDimension:

        skt :adsk.fusion.Sketch = fixPnt.parentSketch

        dimOpes = adsk.fusion.DimensionOrientations
        ori :dimOpes = refDim.orientation

        sktDims :adsk.fusion.SketchDimensions = skt.sketchDimensions
        return sktDims.addDistanceDimension(fixPnt, tgtPnt, ori, tgtPnt.geometry)


    # -Unsupported type-
    dimType :str = dim.objectType.split('::')[-1]
    if dimType != 'SketchLinearDimension':
        return 'SketchLinearDimension Only!'

    # -Unsupported value-
    if value == 0:
        return '"0" is not possible!'

    # -New Value Plus-
    if value > 0:
        dim.parameter.value = value
        return ''

    # -New Value Minus-
    # get free point
    fixPnt = freePnt = adsk.fusion.SketchPoint.cast(None)
    fixPnt, freePnt = getFix_FreePoint(dim)

    # get temp vac
    tmpVec :adsk.core.Vector3D = getTempVec(dim, fixPnt, freePnt)

    # init temp point
    tmpPnt :adsk.fusion.SketchPoint = initPnt(freePnt, tmpVec)

    # lock temp point
    tmpDim :adsk.fusion.SketchLinearDimension = initDimension(
        dim, fixPnt, tmpPnt)

    # unlock dimension
    dim.isDriving = False

    # init temp dimension
    moveDim :adsk.fusion.SketchLinearDimension = initDimension(
        dim, tmpPnt, freePnt)

    # move free point
    moveValue :float = tmpDim.parameter.value + abs(value)
    moveDim.parameter.value = moveValue

    # remove temp
    moveDim.deleteMe()
    tmpDim.deleteMe()
    tmpPnt.deleteMe()

    # dimension lock
    dim.isDriving = True

    return ''