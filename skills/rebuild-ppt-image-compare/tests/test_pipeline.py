"""Synthetic negative/positive regression tests, not a benchmark of visual reconstruction."""
import copy
import io
import json
import shutil
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from contracts import load_project, validate, effective_state, absolute_box, safe_name, inside, sha256, baseline_scene
from init_compare_project import initialize
from qa_compare_pptx import check
from crop_asset import crop
from visual_diff import compare
from bind_native import bind
from freeze_baseline import freeze
from pptx_inspect import NS, inspect


def save(path,value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False),encoding="utf-8")


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="ppt-rebuild-tests-")
        self.base=Path(self.temp.name)
        self.source=self.base/"source.png"
        Image.new("RGB",(800,450),(7,30,70)).save(self.source)
        self.project=initialize(self.source,self.base,"sample",output_mode="comparison")
        _,self.spec,self.manifest,self.scene,self.plan=load_project(self.project)
        self.spec.update(ready=True,design_px=[800,450],reference_bbox=[0,0,800,450])
        self.spec["template"]["reference_match_verified"]=True
        self.scene["nodes"]=[{"id":"title","name":"title","kind":"text","parent":None,"bbox":[50,50,600,70],"z":1,"qa_region":True},{"id":"count","name":"count","kind":"text","parent":None,"bbox":[50,150,600,50],"z":2}]
        self.manifest["items"]=[{"id":"title","text":"湖泊温深曲线","confirmed":True,"must_be_native":True,"source":{"path":"source/reference.png"},"bindings":[{"node_id":"title"}]},{"id":"count","text":"观测点：57,329；偏差 −2.30°C","confirmed":True,"must_be_native":True,"source":{"path":"source/reference.png"},"bindings":[{"node_id":"count"}]}]
        self.commit()

    def tearDown(self):
        self.temp.cleanup()

    def commit(self):
        for name,data in (("deck_spec",self.spec),("content_manifest",self.manifest),("scene_graph",self.scene),("edit_plan",self.plan)):
            save(self.project/f"spec/{name}.json",data)

    def deck(self, mutate=None, reference_mutate=None, reversed_order=False, order_override=None):
        if not (self.project/'qa/baseline/lock.json').exists():freeze(self.project)
        p,a,r=NS["p"],NS["a"],NS["r"]
        def base_slide():
            root=ET.Element(f"{{{p}}}sld")
            tree=ET.SubElement(ET.SubElement(root,f"{{{p}}}cSld"),f"{{{p}}}spTree")
            return root,tree
        ref,tree=base_slide()
        pic=ET.SubElement(tree,f"{{{p}}}pic")
        nv=ET.SubElement(pic,f"{{{p}}}nvPicPr")
        ET.SubElement(nv,f"{{{p}}}cNvPr",id="1",name="reference")
        blip=ET.SubElement(ET.SubElement(pic,f"{{{p}}}blipFill"),f"{{{a}}}blip")
        blip.set(f"{{{r}}}embed","rImg")
        xf=ET.SubElement(ET.SubElement(pic,f"{{{p}}}spPr"),f"{{{a}}}xfrm")
        ET.SubElement(xf,f"{{{a}}}off",x="0",y="0")
        ET.SubElement(xf,f"{{{a}}}ext",cx=str(800*9525),cy=str(450*9525))
        edit,tree=base_slide()
        for index,item in enumerate(self.manifest["items"]):
            node=self.scene["nodes"][index]
            shape=ET.SubElement(tree,f"{{{p}}}sp")
            nv=ET.SubElement(shape,f"{{{p}}}nvSpPr")
            ET.SubElement(nv,f"{{{p}}}cNvPr",id=str(index+2),name=node["name"])
            xf=ET.SubElement(ET.SubElement(shape,f"{{{p}}}spPr"),f"{{{a}}}xfrm")
            x,y,w,h=node.get("bbox",[50,50,600,70])
            ET.SubElement(xf,f"{{{a}}}off",x=str(round(x*9525)),y=str(round(y*9525)))
            ET.SubElement(xf,f"{{{a}}}ext",cx=str(round(w*9525)),cy=str(round(h*9525)))
            para=ET.SubElement(ET.SubElement(shape,f"{{{p}}}txBody"),f"{{{a}}}p")
            run=ET.SubElement(para,f"{{{a}}}r")
            ET.SubElement(run,f"{{{a}}}rPr",sz="2400")
            ET.SubElement(run,f"{{{a}}}t").text=item["text"]
        if mutate:
            mutate(edit)
        if reference_mutate:
            reference_mutate(ref)
        pres=ET.Element(f"{{{p}}}presentation")
        lst=ET.SubElement(pres,f"{{{p}}}sldIdLst")
        order = order_override if order_override is not None else ((2,1) if reversed_order else ((1,2) if self.spec['slides']==2 else (2,)))
        for i in order:
            el=ET.SubElement(lst,f"{{{p}}}sldId",id=str(255+i));el.set(f"{{{r}}}id",f"r{i}")
        ET.SubElement(pres,f"{{{p}}}sldSz",cx=str(800*9525),cy=str(450*9525))
        path=self.base/("test-"+str(len(list(self.base.glob('test-*.pptx'))))+".pptx")
        with zipfile.ZipFile(path,"w") as z:
            z.writestr("ppt/presentation.xml",ET.tostring(pres))
            z.writestr("ppt/_rels/presentation.xml.rels",'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="r1" Target="slides/slide9.xml"/><Relationship Id="r2" Target="slides/slide3.xml"/></Relationships>')
            z.writestr("ppt/slides/slide9.xml",ET.tostring(ref));z.writestr("ppt/slides/slide3.xml",ET.tostring(edit))
            z.writestr("ppt/slides/_rels/slide9.xml.rels",'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rImg" Target="../media/reference.png"/></Relationships>')
            z.write(self.project/"source/reference.png","ppt/media/reference.png")
        return path

    def test_valid_contract_and_pptx(self):
        self.assertEqual(validate(*load_project(self.project)),[])
        self.assertEqual(check(self.deck(),self.project)["status"],"PASS")

    def test_existing_project_not_overwritten(self):
        original=sha256(self.project/"spec/deck_spec.json")
        with self.assertRaises(ValueError):initialize(self.source,self.base,"sample")
        self.assertEqual(original,sha256(self.project/"spec/deck_spec.json"))

    def test_path_traversal_and_reserved_names(self):
        for name in ("../oops","..","C:\\escape","CON","COM1"):
            with self.assertRaises(ValueError):safe_name(name)
        with self.assertRaises(ValueError):inside(self.project,"../escape")

    def test_scaffold_is_not_production(self):
        project=initialize(self.source,self.base,"empty")
        self.assertTrue(validate(*load_project(project)))

    def test_source_hash_detected(self):
        (self.project/"source/reference.png").write_bytes(b"changed")
        self.assertTrue(validate(*load_project(self.project)))

    def test_style_reuse_mismatch(self):
        self.spec["template"].update(reuse_from="old",reuse_family_id="different",reuse_evidence="compared")
        self.commit();self.assertTrue(validate(*load_project(self.project)))

    def test_missing_bound_content_even_if_elsewhere(self):
        def mutate(root):root.findall(".//a:t",NS)[0].text="观测点：57,329；偏差 −2.30°C"
        self.assertEqual(check(self.deck(mutate),self.project)["status"],"FAIL")

    def test_changed_minus_and_number(self):
        for replacement in ("观测点：57,329；偏差 -2.30°C","观测点：57,328；偏差 −2.30°C"):
            def mutate(root):root.findall(".//a:t",NS)[1].text=replacement
            self.assertEqual(check(self.deck(mutate),self.project)["status"],"FAIL")

    def test_duplicate_shape_name(self):
        def mutate(root):root.findall(".//p:cNvPr",NS)[1].set("name","title")
        self.assertEqual(check(self.deck(mutate),self.project)["status"],"FAIL")

    def test_hidden_text(self):
        def mutate(root):root.findall(".//p:cNvPr",NS)[0].set("hidden","1")
        self.assertEqual(check(self.deck(mutate),self.project)["status"],"FAIL")

    def test_transparent_text(self):
        def mutate(root):
            for prop in root.findall(".//a:rPr",NS):ET.SubElement(ET.SubElement(ET.SubElement(prop,f"{{{NS['a']}}}solidFill"),f"{{{NS['a']}}}srgbClr",val="FFFFFF"),f"{{{NS['a']}}}alpha",val="0")
        self.assertEqual(check(self.deck(mutate),self.project)["status"],"FAIL")

    def test_wrong_slide_order(self):
        self.assertEqual(check(self.deck(reversed_order=True),self.project)["status"],"FAIL")

    def test_reference_crop_rejected(self):
        def mutate(root):ET.SubElement(root.find(".//p:blipFill",NS),f"{{{NS['a']}}}srcRect",l="100")
        self.assertEqual(check(self.deck(reference_mutate=mutate),self.project)["status"],"FAIL")

    def test_slide1_text_cannot_satisfy_slide2(self):
        def mutate(root):root.find("p:cSld/p:spTree",NS).remove(root.find(".//p:sp",NS))
        self.assertEqual(check(self.deck(mutate),self.project)["status"],"FAIL")

    def test_unauthorized_delete(self):
        self.plan["remove_components"]=["count"];self.commit()
        self.assertTrue(validate(*load_project(self.project)))

    def test_authorized_delete_preserves_baseline(self):
        self.plan.update(remove_components=["count"],authorized=True,user_request="删除观测点模块")
        self.spec["mode"]="authorized_reflow";self.commit()
        before=copy.deepcopy(self.manifest)
        def mutate(root):
            tree=root.find("p:cSld/p:spTree",NS);tree.remove(tree.findall("p:sp",NS)[1])
        self.assertEqual(check(self.deck(mutate),self.project)["status"],"PASS")
        self.assertEqual(self.manifest,before)
        self.assertEqual(check(self.deck(),self.project)["status"],"FAIL")

    def test_protected_deletion_rejected(self):
        self.plan.update(remove_components=["count"],authorized=True,user_request="删除",protected_nodes=["count"])
        self.spec["mode"]="authorized_reflow";self.commit();self.assertTrue(validate(*load_project(self.project)))

    def test_parent_cycle(self):
        self.scene["nodes"][0].update(parent="count",bbox_local=[1,1,2,2])
        self.scene["nodes"][1].update(parent="title",bbox_local=[1,1,2,2])
        self.commit();self.assertTrue(validate(*load_project(self.project)))

    def test_group_binding_and_transform(self):
        self.scene["nodes"].append({"id":"card","name":"card","kind":"group","bbox":[40,40,620,180],"parent":None,"native_group":True})
        for node in self.scene["nodes"][:2]:node["parent"]="card"
        self.commit()
        source=self.deck()
        grouped=self.base/"grouped.pptx";bind(source,grouped,self.project)
        self.assertEqual(check(grouped,self.project)["status"],"PASS")
        objects=inspect(grouped)["slides"][self.spec['editable_slide']-1]["objects"]
        self.assertEqual([r for r in objects if r["name"]=="title"][0]["parent"],"card")

    def test_release_requires_real_evidence(self):
        self.assertEqual(check(self.deck(),self.project,release=True)["status"],"FAIL")

    def test_baseline_drift_rejected(self):
        deck=self.deck()
        self.manifest['items'][0]['text']='悄悄改掉标题';self.commit()
        with self.assertRaises(ValueError):check(deck,self.project)

    def release_fixture(self):
        final=self.project/self.spec['output'];shutil.copy2(self.deck(),final)
        fingerprint=sha256(final)
        save(self.project/'qa/finalizer.json',{'finalSha256':fingerprint})
        evidence={'path':'source/reference.png','sha256':sha256(self.project/'source/reference.png')}
        review={'pptx_sha256':fingerprint,'checks':{key:{'status':'PASS','notes':'Synthetic unit-test fixture only','evidence':[evidence]} for key in ('content_visual','science_assets','layout_visual','reference_visual','editability','non_target_preservation')}}
        receipt={'status':'PASS','operation':'render','pptx_sha256':fingerprint,'rendered_pptx_sha256':fingerprint,'application':'WPS','slide_count':self.spec['slides'],'outputs':[{'slide':i,'path':str(self.project/'source/reference.png'),'sha256':evidence['sha256']} for i in range(1,self.spec['slides']+1)],'edits':[]}
        reviewfile=self.project/'qa/unit-review.json';receiptfile=self.project/'qa/unit-receipt.json'
        save(reviewfile,review);save(receiptfile,receipt)
        return final,receiptfile,reviewfile

    def test_release_evidence_schema_positive(self):
        final,receipt,review=self.release_fixture()
        self.assertEqual(check(final,self.project,True,receipt,review)['status'],'PASS')

    def test_edit_copy_receipt_not_accepted_for_release(self):
        final,receipt,review=self.release_fixture()
        data=json.loads(receipt.read_text());data['operation']='edit_test';save(receipt,data)
        self.assertEqual(check(final,self.project,True,receipt,review)['status'],'FAIL')

    def test_stale_review_hash(self):
        final,receipt,review=self.release_fixture()
        data=json.loads(review.read_text());data['pptx_sha256']='wrong';save(review,data)
        self.assertEqual(check(final,self.project,True,receipt,review)['status'],'FAIL')

    def test_unrun_visual_review_rejected(self):
        final,receipt,review=self.release_fixture()
        data=json.loads(review.read_text());data['checks']['layout_visual']['status']='NOT_RUN';save(review,data)
        self.assertEqual(check(final,self.project,True,receipt,review)['status'],'FAIL')

    def test_nan_geometry_rejected(self):
        self.scene['nodes'][0]['bbox'][0]=float('nan');self.commit()
        self.assertTrue(validate(*load_project(self.project)))

    def test_group_deletion_expands_descendants(self):
        self.scene['nodes'].append({'id':'card','name':'card','kind':'group','parent':None,'bbox':[40,40,620,180]})
        self.scene['nodes'][1]['parent']='card'
        self.plan.update(remove_components=['card'],authorized=True,user_request='删除卡片')
        removed,items=effective_state(self.manifest,self.scene,self.plan)
        self.assertEqual(removed,{'card','count'})
        self.assertEqual(items[1]['bindings'],[])
        self.assertEqual(items[0]['bindings'],[{'node_id':'title'}])

    def test_reparent_cannot_escape_frozen_deletion(self):
        self.scene['nodes'].append({'id':'card','name':'card','kind':'group','parent':None,'bbox':[40,40,620,180]})
        self.scene['nodes'][1]['parent']='card';self.commit();freeze(self.project)
        self.scene['nodes'][1]['parent']=None
        self.spec['mode']='authorized_reflow'
        self.plan.update(remove_components=['card'],authorized=True,user_request='删除 card，其他不变');self.commit()
        removed,_=effective_state(self.manifest,self.scene,self.plan,baseline_scene(self.project,self.scene))
        self.assertIn('count',removed)
        self.assertTrue(any('membership' in e for e in validate(*load_project(self.project))))

    def test_horizontal_line_box_supported(self):
        self.scene['nodes'].append({'id':'line','name':'line','kind':'shape','geometry':'line','parent':None,'bbox':[50,300,500,0]})
        self.commit();self.assertEqual(validate(*load_project(self.project)),[])

    def test_crop_original_size_and_bounds(self):
        record=crop(self.project,"asset",[10,20,100,70])
        with Image.open(self.project/record["path"]) as im:self.assertEqual(im.size,(100,70))
        with self.assertRaises(ValueError):crop(self.project,"outside",[790,440,100,70])

    def test_diff_is_diagnostic_not_pass(self):
        result=compare(self.project,self.source,"qa/diff")
        self.assertEqual(result["kind"],"diagnostic_only")
        self.assertEqual(result["regions"][0]["mean_absolute_channel_difference"],0)
        self.assertEqual(result["regions"][0]["status"],"NOT_RUN")
        with self.assertRaises(ValueError):compare(self.project,self.source,"qa/diff")

    def single_slide(self):
        self.spec.update(output_mode='editable_only',slides=1,editable_slide=1)
        self.scene['slide']=1
        self.commit()

    def test_default_initialization_is_single_editable(self):
        project=initialize(self.source,self.base,'single-default')
        _,spec,_,scene,_=load_project(project)
        self.assertEqual((spec['output_mode'],spec['slides'],spec['editable_slide'],scene['slide']),('editable_only',1,1,1))
        self.assertTrue(spec['output'].endswith('_editable.pptx'))
        self.assertEqual(sha256(self.source),sha256(project/spec['source']['original_copy']))

    def test_single_slide_exact_native_content(self):
        self.single_slide()
        deck=self.deck()
        self.assertEqual(len(inspect(deck)['slides']),1)
        self.assertEqual(check(deck,self.project)['status'],'PASS')
        self.test_changed_minus_and_number()

    def test_single_slide_rejects_reference_only(self):
        self.single_slide()
        self.assertEqual(check(self.deck(order_override=(1,)),self.project)['status'],'FAIL')

    def test_single_slide_rejects_extra_reference_page(self):
        self.single_slide()
        self.assertEqual(check(self.deck(order_override=(1,2)),self.project)['status'],'FAIL')

    def test_single_slide_native_group(self):
        self.single_slide()
        self.test_group_binding_and_transform()

    def test_single_slide_authorized_delete(self):
        self.single_slide()
        self.test_authorized_delete_preserves_baseline()

    def test_single_slide_deletion_cannot_escape_baseline(self):
        self.single_slide()
        self.test_reparent_cannot_escape_frozen_deletion()

    def test_single_slide_release_requires_source_comparison(self):
        self.single_slide()
        final,receipt,review=self.release_fixture()
        self.assertEqual(check(final,self.project,True,receipt,review)['status'],'PASS')
        data=json.loads(review.read_text());data['checks']['reference_visual']['status']='NOT_APPLICABLE';save(review,data)
        self.assertEqual(check(final,self.project,True,receipt,review)['status'],'FAIL')

    def test_single_slide_rejects_two_slide_receipt(self):
        self.single_slide()
        final,receipt,review=self.release_fixture()
        data=json.loads(receipt.read_text());data['slide_count']=2;data['outputs'].append({**data['outputs'][0],'slide':2});save(receipt,data)
        self.assertEqual(check(final,self.project,True,receipt,review)['status'],'FAIL')

    def test_mode_and_slide_mapping_must_agree(self):
        for mode,count,editable,scene_slide in [('editable_only',2,2,2),('comparison',1,1,1),('editable_only',1,2,1),('editable_only',1,1,2),('unknown',1,1,1)]:
            with self.subTest(mode=mode,count=count,editable=editable,scene_slide=scene_slide):
                self.spec.update(output_mode=mode,slides=count,editable_slide=editable);self.scene['slide']=scene_slide;self.commit()
                self.assertTrue(validate(*load_project(self.project)))
        self.spec.pop('output_mode');self.commit()
        self.assertTrue(validate(*load_project(self.project)))

    def test_legacy_21_comparison_project_still_valid(self):
        for data in (self.spec,self.manifest,self.scene,self.plan):data['schema_version']='2.1'
        self.spec.pop('output_mode');self.commit()
        self.assertEqual(validate(*load_project(self.project)),[])
        self.assertEqual(check(self.deck(),self.project)['status'],'PASS')


if __name__=="__main__":unittest.main(verbosity=2)
