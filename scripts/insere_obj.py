# uso: insere_obj.py src.3mf obj.json dst.3mf X Y   (objeto novo id 99, filamento 3, purga no objeto, 100% zig-zag)
import zipfile,sys,json,re
src,oj,dst,X,Y=sys.argv[1],sys.argv[2],sys.argv[3],float(sys.argv[4]),float(sys.argv[5])
I=int(sys.argv[6]) if len(sys.argv)>6 else 99
o=json.load(open(oj))
vs=''.join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x,y,z in o['vertices'])
ts=''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a,b,c in o['triangulos'])
sub=('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
     'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">\n'
     f' <metadata name="BambuStudio:3mfVersion">1</metadata>\n <resources>\n  <object id="{I}" p:UUID="00{I}0000-81cb-4c03-9d28-80fed5dfa1dc" type="model">\n'
     f'   <mesh><vertices>{vs}</vertices><triangles>{ts}</triangles></mesh>\n  </object>\n </resources>\n <build/>\n</model>\n')
zi=zipfile.ZipFile(src); zo=zipfile.ZipFile(dst,'w',zipfile.ZIP_DEFLATED)
for it in zi.infolist():
    d=zi.read(it.filename)
    if it.filename=='3D/3dmodel.model':
        t=d.decode()
        t=t.replace(' </resources>',f'  <object id="{I}" p:UUID="000000{I}-61cb-4c03-9d28-80fed5dfa1dc" type="model">\n   <components>\n    <component p:path="/3D/Objects/object_{I}.model" objectid="{I}" p:UUID="00{I}0001-b206-40ff-9872-83e8017abed1" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n   </components>\n  </object>\n </resources>',1)
        t=t.replace(' </build>',f'  <item objectid="{I}" p:UUID="000000{I}-b1ec-4553-aec9-835e5b724bb4" transform="1 0 0 0 1 0 0 0 1 {X} {Y} 0" printable="1"/>\n </build>',1); d=t.encode()
    if it.filename=='3D/_rels/3dmodel.model.rels':
        t=d.decode().replace('</Relationships>',f' <Relationship Target="/3D/Objects/object_{I}.model" Id="rel-{I}" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n</Relationships>'); d=t.encode()
    if it.filename=='Metadata/model_settings.config':
        t=d.decode()
        ob=(f'  <object id="{I}">\n    <metadata key="name" value="sacrificio_purga"/>\n    <metadata key="extruder" value="3"/>\n'
            '    <metadata key="flush_into_objects" value="1"/>\n    <metadata key="sparse_infill_density" value="100%"/>\n'
            '    <metadata key="sparse_infill_pattern" value="zig-zag"/>\n'
            '    <part id="1" subtype="normal_part">\n      <metadata key="name" value="sacrificio_purga"/>\n'
            '      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>\n    </part>\n  </object>\n')
        t=t.replace('  <plate>',ob+'  <plate>',1)
        t=t.replace('  </plate>',f'    <model_instance>\n      <metadata key="object_id" value="{I}"/>\n      <metadata key="instance_id" value="0"/>\n      <metadata key="identify_id" value="9{I}"/>\n    </model_instance>\n  </plate>',1)
        t=t.replace('  </assemble>',f'   <assemble_item object_id="{I}" instance_id="0" transform="1 0 0 0 1 0 0 0 1 {X} {Y} 0" offset="0 0 0" />\n  </assemble>',1)
        d=t.encode()
    zo.writestr(it,d)
zo.writestr(f'3D/Objects/object_{I}.model',sub)
zo.close(); print('inserido em',X,Y)
