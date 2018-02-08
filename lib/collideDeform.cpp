#include "collideDeform.h"

#include <maya/MIOStream.h>
#include <maya/MFnPlugin.h>
#include <maya/MFnTypedAttribute.h>
#include <maya/MFnNumericAttribute.h>
#include <maya/MFnData.h>
#include <maya/MItMeshVertex.h>
#include <maya/MPlug.h>
#include <maya/MFnMesh.h>
#include <maya/MFnMeshData.h>
#include <maya/MFloatPointArray.h>
#include <maya/MMeshIntersector.h>
#include <maya/MFloatVector.h>
#include <maya/MRampAttribute.h>

#include <maya/MThreadUtils.h>

// ノードID
#define kPluginNodeId 0x75245
// ノード名
#define kPluginNodeName "CollideDeform"
// クラス名
#define kPluginClassName CollideDeform

// メンバ変数
MObject CollideDeform::origMesh;
MObject CollideDeform::pos;
MObject CollideDeform::collisionMesh;
MObject CollideDeform::outMesh;
MObject CollideDeform::ramp;
MObject CollideDeform::swellLength;
MObject CollideDeform::swellVal;

// コンストラクタ・デストラクタ
kPluginClassName::kPluginClassName() {}
kPluginClassName::~kPluginClassName() {}
// ノードクリエーター　(initializePlugin()で使用)
void *kPluginClassName::creator(){	return new kPluginClassName(); }

////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Plug-in
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

MStatus kPluginClassName::compute( const MPlug &plug, MDataBlock &data ){
	
	MStatus stat;

	// カスタムアトリビュートのハンドルを取得
	MObject origMeshObj = data.inputValue(origMesh).asMesh();
	MObject collisionMeshObj = data.inputValue(collisionMesh).asMesh();
	MDataHandle inputData = data.inputValue(pos);
	MPoint posPoi = inputData.asVector();
	inputData = data.inputValue(swellLength);
	float swellLength = inputData.asFloat();
	inputData = data.inputValue(swellVal);
	float swellVal = inputData.asFloat();
	MRampAttribute rampAttribute(thisMObject(), ramp);

	MDataHandle outMeshHandle = data.outputValue(outMesh);

	if (origMeshObj.isNull() || collisionMeshObj.isNull()) {
		return stat;
	}

	// デフォームメッシュを準備
	MObject meshObject = MFnMeshData().create();
	MFnMesh	resultMesh;
	resultMesh.copy(origMeshObj, meshObject);

	// デフォーム計算の結果の格納先を準備 （オリジナルのポイント位置の配列をコピー）
	MFloatPointArray newPoints;
	resultMesh.getPoints(newPoints);

	// spatial queries
	MMeshIntersector sq;
	sq.create(collisionMeshObj);

	MFnMesh origMesh(origMeshObj);
	MFloatVectorArray origNmls;
	origMesh.getNormals(origNmls);

	// core
	#pragma omp parallel for schedule(guided) if(1000<newPoints.length()) num_threads(8)
		for (int i = 0; i < int(newPoints.length()); i++) {
			newPoints[i] += posPoi;
			MPointOnMesh loc;
			stat = sq.getClosestPoint(newPoints[i], loc, 1000);
			if (stat) {
				MFloatVector locNml = loc.getNormal();
				MFloatPoint locPoi = loc.getPoint();
				MFloatVector dirNml = locPoi - newPoints[i];
				float dot = locNml.operator*(dirNml.normal());
				if (0 < dot) {
					newPoints[i] = locPoi;
				}else {
					float dist = newPoints[i].distanceTo(locPoi);
					if (dist < swellLength) {
						float rampVal;
						float ratio = dist * 1.0 / swellLength;
						rampAttribute.getValueAtPosition(ratio, rampVal);
						newPoints[i] += origNmls[i] * rampVal * swellVal * 0.1;
					}
				}
			}
		}
	resultMesh.setPoints(newPoints);

	// メッシュを出力
	outMeshHandle.setMObject(meshObject);

	// 終了
	data.setClean(plug);
	return MS::kSuccess;
}

void kPluginClassName::postConstructor() {
	MPlug rampPlug(kPluginClassName::thisMObject(), ramp);
	MPlug elementPlug;
	elementPlug = rampPlug.elementByLogicalIndex(0);
	elementPlug.child(0).setFloat(0);
	elementPlug.child(1).setFloat(0);
	elementPlug.child(2).setInt(2);
	elementPlug = rampPlug.elementByLogicalIndex(1);
	elementPlug.child(0).setFloat(0.3);
	elementPlug.child(1).setFloat(1);
	elementPlug.child(2).setInt(2);
	elementPlug = rampPlug.elementByLogicalIndex(2);
	elementPlug.child(0).setFloat(1);
	elementPlug.child(1).setFloat(0);
	elementPlug.child(2).setInt(2);
}

// アトリビュート作成　(initializePlugin()で使用)
MStatus kPluginClassName::initialize()
{
	MFnTypedAttribute gAttr;
	MFnNumericAttribute nAttr;
	MRampAttribute rAttr;
	
	origMesh = gAttr.create("origMesh", "oMesh", MFnData::kMesh);
	gAttr.setReadable(false);
	gAttr.setKeyable(true);
	collisionMesh = gAttr.create("collisionMesh", "colMesh", MFnData::kMesh);
	gAttr.setReadable(false);
	gAttr.setKeyable(true);
	outMesh = gAttr.create("outMesh", "outMesh", MFnData::kMesh);
	gAttr.setWritable(false);
	pos = nAttr.create("pos", "pos", MFnNumericData::k3Double);
	nAttr.setKeyable(true);
	ramp = rAttr.createCurveRamp("ramp", "ramp");
	swellLength = nAttr.create("swellLength", "swellLength", MFnNumericData::kFloat, 0.5);
	swellVal = nAttr.create("swellVal", "swellVal", MFnNumericData::kFloat, 1.0);

	addAttribute(origMesh);
	addAttribute(collisionMesh);
	addAttribute(outMesh);
	addAttribute(pos);
	addAttribute(ramp);
	addAttribute(swellLength);
	addAttribute(swellVal);

	attributeAffects(origMesh, outMesh);
	attributeAffects(collisionMesh, outMesh);
	attributeAffects(pos, outMesh);
	attributeAffects(ramp, outMesh);
	attributeAffects(swellLength, outMesh);
	attributeAffects(swellVal, outMesh);

	return MS::kSuccess;
}

////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Plug-in initialization
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

MStatus initializePlugin( MObject obj )
{
	MStatus   status;
	MFnPlugin plugin( obj, PLUGIN_COMPANY, "3.0", "Any" );

	status = plugin.registerNode( kPluginNodeName, kPluginNodeId, kPluginClassName::creator, kPluginClassName::initialize );
	if (!status) {
		status.perror( "registerNode" );
		return status;
	}

	return status;
}

MStatus uninitializePlugin (MObject obj )
{
	MStatus   status;
	MFnPlugin plugin( obj );

	status = plugin.deregisterNode(kPluginNodeId);
	if (!status) {
		status.perror( "deregisterNode" );
		return status;
	}

	return status;
}
