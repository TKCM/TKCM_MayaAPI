# coding: UTF-8

import maya.api.OpenMaya as OM
import sys

# API2.0を使用していることを宣言 
def maya_useNewAPI():
  pass

kPluginNodeId = OM.MTypeId( 0x75242 )
kPluginNodeName = 'SquashAndStretch'

class SquashAndStretch( OM.MPxNode ):

    def __init__( self ):
        OM.MPxNode.__init__( self )

    def compute( self, plug, block ):
        # カスタムアトリビュートのハンドルを取得
        sVal = block.inputValue( self.sVal ).asDouble()
        origMesh = block.inputValue( self.origMesh ).asMesh()
        targetMesh = block.inputValue( self.targetMesh ).asMesh()

        cacheOriEdgeLenHandle = block.outputArrayValue( self.cacheOriEdgeLen )
        outMeshHandle = block.outputValue( self.outputMesh )

        # イテレータを取得
        origEdgeIter = OM.MItMeshEdge( origMesh )
        targetEdgeIter = OM.MItMeshEdge( targetMesh )
        tarVerIter = OM.MItMeshVertex( targetMesh )

        # デフォームメッシュデータを準備
        meshObject = OM.MFnMeshData().create()
        resultMesh = OM.MFnMesh()
        resultMesh.copy( targetMesh, meshObject )

        # core
        if origEdgeIter.count() == targetEdgeIter.count():
          # 各エッジの長さをリストにしておく
          oEdgeLenArray = []
          while not origEdgeIter.isDone():
            oEdgeLenArray.append( origEdgeIter.length() )
            origEdgeIter.next()
          tEdgeLenArray = []
          while not targetEdgeIter.isDone():
            tEdgeLenArray.append( targetEdgeIter.length() )
            targetEdgeIter.next()

          # デフォーム
          while not tarVerIter.isDone():
            edgePack = tarVerIter.getConnectedEdges()
            val = 0.0
            oVal = 0.0
            tVal = 0.0
            for edge in edgePack:
              oVal += oEdgeLenArray[ edge ]
              tVal += tEdgeLenArray[ edge ]
            val = 1.0 - tVal/oVal

            offset = tarVerIter.getNormal() * val

            resultMesh.setPoint( tarVerIter.index(), tarVerIter.position() + offset )
            tarVerIter.next()

        # メッシュを出力
        outMeshHandle.setMObject( meshObject )

        # 終了宣言
        block.setClean(plug)

    @classmethod
    def creator(cls ):
        return cls()

    @classmethod
    def initialize( cls ):
        nAttr = OM.MFnNumericAttribute()
        rAttr = OM.MRampAttribute()
        typedAttr = OM.MFnTypedAttribute()

        cls.origMesh = typedAttr.create( 'origMesh', 'oMesh', OM.MFnData.kMesh )
        typedAttr.readable = False
        typedAttr.keyable = True
        cls.targetMesh = typedAttr.create( 'targetMesh', 'tMesh', OM.MFnData.kMesh )
        typedAttr.readable = False
        typedAttr.keyable = True
        cls.outputMesh = typedAttr.create('outputMesh', 'outMesh', OM.MFnData.kMesh)
        typedAttr.writable = False
        cls.sVal = nAttr.create( 'sVal', 'sv', OM.MFnNumericData.kDouble )
        nAttr.writable = True
        cls.cacheOriEdgeLen = nAttr.create( 'cacheOriEdgeLen', 'rv', OM.MFnNumericData.kDouble )
        nAttr.array = True
        nAttr.hidden = True

        cls.addAttribute( cls.sVal )
        cls.addAttribute( cls.origMesh )
        cls.addAttribute( cls.targetMesh )
        cls.addAttribute( cls.outputMesh )
        cls.addAttribute( cls.cacheOriEdgeLen )

        cls.attributeAffects( cls.sVal, cls.cacheOriEdgeLen )
        cls.attributeAffects( cls.sVal, cls.outputMesh )
        cls.attributeAffects( cls.origMesh, cls.outputMesh )
        cls.attributeAffects( cls.origMesh, cls.cacheOriEdgeLen )
        cls.attributeAffects( cls.targetMesh, cls.outputMesh )

def initializePlugin( obj ):
    plugin = OM.MFnPlugin( obj )
    try:
        plugin.registerNode( kPluginNodeName, kPluginNodeId, SquashAndStretch.creator, SquashAndStretch.initialize, OM.MPxNode.kDependNode )
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
