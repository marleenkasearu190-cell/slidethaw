// Copy into project/src/ and adapt where needed. Basic types only; unsupported types FAIL.
// Read current Presentations skill/API and run its operation marker BEFORE execution.
import fs from 'node:fs/promises';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {Presentation, PresentationFile} from '@oai/artifact-tool';
const project=path.resolve(process.argv[2]??'');
const skill=process.env.REBUILD_SKILL_DIR;
const python=process.env.RUNTIME_PYTHON;
if(!skill||!python) throw new Error('Set REBUILD_SKILL_DIR and bundled RUNTIME_PYTHON');
execFileSync(python,[path.join(skill,'scripts/validate_specs.py'),project],{stdio:'inherit'});
execFileSync(python,[path.join(skill,'scripts/freeze_baseline.py'),project],{stdio:'inherit'});
const read=async name=>JSON.parse(await fs.readFile(path.join(project,'spec',name+'.json'),'utf8'));
const [spec,manifest,scene,plan]=await Promise.all(['deck_spec','content_manifest','scene_graph','edit_plan'].map(read));
const baseline=JSON.parse(await fs.readFile(path.join(project,'qa/baseline/scene_graph.json'),'utf8'));
const nodes=new Map(scene.nodes.map(n=>[n.id,n]));
const removed=new Set(plan.remove_components);
let count=-1;while(count!==removed.size){count=removed.size;for(const n of baseline.nodes)if(removed.has(n.parent))removed.add(n.id);}
const boxes=new Map();
function box(id){if(boxes.has(id))return boxes.get(id);const n=nodes.get(id);let b=n.bbox;if(n.bbox_local){const p=box(n.parent);b=[p[0]+n.bbox_local[0],p[1]+n.bbox_local[1],n.bbox_local[2],n.bbox_local[3]];} boxes.set(id,b);return b;}
const position=b=>({left:b[0],top:b[1],width:b[2],height:b[3]});
const replacements=new Map(plan.replacements.map(r=>[r.content_id,r.text]));
const content=new Map();for(const item of manifest.items)for(const binding of item.bindings){if(!binding.cell)content.set(binding.node_id,replacements.get(item.id)??item.text);}
const deck=Presentation.create({slideSize:{width:spec.design_px[0],height:spec.design_px[1]}});
if(spec.slides===2){
  const reference=deck.slides.add();reference.background.fill=spec.reference_background??'#FFFFFF';
  reference.images.add({blob:await fs.readFile(path.join(project,spec.source.path)),contentType:'image/png',alt:'Complete source reference',fit:'contain',position:position(spec.reference_bbox)});
}
const rebuilt=deck.slides.add();rebuilt.background.fill=spec.background??'#FFFFFF';
for(const n of [...scene.nodes].sort((a,b)=>(a.z??0)-(b.z??0))){
  if(removed.has(n.id)||n.kind==='group')continue;
  if(n.kind==='picture'){
    const asset=scene.assets.find(a=>a.id===n.asset_id);
    rebuilt.images.add({blob:await fs.readFile(path.join(project,asset.path)),contentType:asset.content_type??'image/png',alt:'ppt-rebuild:'+n.name,fit:'contain',position:position(box(n.id))});
  }else if(n.kind==='text'||n.kind==='shape'){
    const s=rebuilt.shapes.add({geometry:n.geometry??(n.kind==='text'?'textbox':'rect'),name:n.name,position:position(box(n.id)),fill:n.fill??'none',line:n.line??{fill:'none',width:0},...(n.borderRadius!==undefined?{borderRadius:n.borderRadius}:{})});
    if(n.kind==='text'){
      if(typeof content.get(n.id)!=='string')throw new Error('Missing exact text: '+n.id);
      s.text=content.get(n.id);
      s.text.style={typeface:spec.style_tokens.font_zh??'Microsoft YaHei',fontSize:24,color:'#111111',autoFit:'none',...n.text_style};
    }
  }else throw new Error('Add verified native adapter for '+n.kind+'; do not silently rasterize '+n.id);
}
const destination=path.join(project,'tmp/candidate.pptx');
try{await fs.access(destination);throw new Error('candidate.pptx exists; use a revision project or new private filename');}catch(e){if(e.code!=='ENOENT')throw e;}
await(await PresentationFile.exportPptx(deck)).save(destination);
execFileSync(python,[path.join(skill,'scripts/bind_native.py'),'--input',destination,'--out',path.join(project,'tmp/bound.pptx'),'--project',project],{stdio:'inherit'});
console.log('Draft written. Finalize bound.pptx using current Presentations finalizer, then render and run release QA.');
