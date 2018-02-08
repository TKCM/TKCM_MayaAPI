#include <maya/MPxNode.h>

class CollideDeform : public MPxNode {
	public:
						CollideDeform();
		virtual			~CollideDeform();

		virtual MStatus compute(const MPlug &plug, MDataBlock &data) override;

		virtual void 	postConstructor() override;

		static  void    *creator();

		static  MStatus initialize();
		
	public:
		static MObject origMesh;
		static MObject pos;
		static MObject collisionMesh;
		static MObject outMesh;
		static MObject ramp;
		static MObject swellLength;
		static MObject swellVal;

};