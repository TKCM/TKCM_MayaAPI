# coding: UTF-8

import maya.api.OpenMaya as OM
import sys
 
def maya_useNewAPI():
  pass

kPluginNodeId = OM.MTypeId( 0x75244 )
kPluginNodeName = 'Verlet'

class Verlet( OM.MPxNode ):

    def __init__( self ):
        OM.MPxNode.__init__( self )

    def compute( self, plug, block ):
        # カスタムアトリビュートのハンドルを取得
        follow = block.inputValue( self.follow ).asDouble()
        restore = block.inputValue( self.restore ).asDouble()
        time = block.inputValue( self.time ).asDouble()
        pos = block.inputValue( self.pos ).asVector()
        origMesh = block.inputValue( self.origMesh ).asMesh()

        posResHandle = block.outputValue( self.positionRest )
        velResHandle = block.outputValue( self.velocityRest )
        outMeshHandle = block.outputValue( self.outputMesh )

        # イテレータを取得
        origVerIter = OM.MItMeshVertex( origMesh )

        # デフォームメッシュデータを準備
        meshObject = OM.MFnMeshData().create()
        resultMesh = OM.MFnMesh()
        resultMesh.copy( origMesh, meshObject )
        
        # core
        if time == 1.0 :    # reset
            velResHandle.set3Double( 0, 0, 0 )
            posResHandle.set3Double( 0, 0, 0 )
        posRest = posResHandle.asVector()
        velRest = velResHandle.asVector()
        newPos = ( pos - posRest ) * follow
        vlct = velRest + ( newPos - velRest ) * restore 
        velResHandle.set3Double( vlct.x, vlct.y, vlct.z )
        offset = posRest + velRest
        posResHandle.set3Double( offset.x, offset.y, offset.z )

        while not origVerIter.isDone():
            poiPos = origVerIter.position() + offset           
            resultMesh.setPoint( origVerIter.index(), poiPos )
            origVerIter.next()

        # メッシュを出力
        outMeshHandle.setMObject( meshObject )

        # 終了宣言
        block.setClean(plug)

    @classmethod
    def creator( cls ):
        return cls()

    @classmethod
    def initialize( cls ):
        nAttr = OM.MFnNumericAttribute()
        rAttr = OM.MRampAttribute()
        typedAttr = OM.MFnTypedAttribute()

        cls.origMesh = typedAttr.create( 'origMesh', 'oMesh', OM.MFnData.kMesh )
        typedAttr.readable = False
        typedAttr.keyable = True
        cls.outputMesh = typedAttr.create('outputMesh', 'outMesh', OM.MFnData.kMesh)
        typedAttr.writable = False
        cls.follow = nAttr.create( 'follow', 'follow', OM.MFnNumericData.kDouble, 0.3 )
        nAttr.writable = True
        cls.restore = nAttr.create( 'restore', 'restore', OM.MFnNumericData.kDouble, 0.5 )
        nAttr.writable = True
        cls.time = nAttr.create( 'time', 'time', OM.MFnNumericData.kDouble )
        nAttr.writable = True
        nAttr.keyable = True
        cls.pos = nAttr.create( 'pos', 'pos', OM.MFnNumericData.k3Double )
        nAttr.writable = True
        nAttr.keyable = True
        cls.positionRest = nAttr.create( 'positionRest', 'pR', OM.MFnNumericData.k3Double )
        nAttr.hidden = True
        cls.velocityRest = nAttr.create( 'velocityRest', 'vR', OM.MFnNumericData.k3Double )
        nAttr.hidden = True

        cls.addAttribute( cls.follow )
        cls.addAttribute( cls.restore )
        cls.addAttribute( cls.origMesh )
        cls.addAttribute( cls.outputMesh )
        cls.addAttribute( cls.positionRest )
        cls.addAttribute( cls.velocityRest )
        cls.addAttribute( cls.time )
        cls.addAttribute( cls.pos )

        cls.attributeAffects( cls.follow, cls.outputMesh )
        cls.attributeAffects( cls.origMesh, cls.outputMesh )
        cls.attributeAffects( cls.time, cls.outputMesh )
        cls.attributeAffects( cls.pos, cls.outputMesh )

def initializePlugin( obj ):
    plugin = OM.MFnPlugin( obj )
    try:
        plugin.registerNode( kPluginNodeName, kPluginNodeId, Verlet.creator, Verlet.initialize, OM.MPxNode.kDependNode )
    except:
        sys.stderr.write( 'Failed to register node: ' + kPluginNodeName )
        raise

def uninitializePlugin( obj ):
    plugin = OM.MFnPlugin( obj )
    try:
        plugin.deregisterNode( kPluginNodeId )
    except:
        sys.stderr.write( 'Failed to register node: ' + kPluginNodeName )
        raise
