// Copy into project/src/. SKILL_DIR must point to the current installed Presentations skill.
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const project=path.resolve(process.argv[2]??'');
const {SKILL_DIR,RUNTIME_PYTHON,RUNTIME_NODE,RUNTIME_NODE_MODULES,RUNTIME_BIN_DIR}=process.env;
if(!SKILL_DIR||!RUNTIME_PYTHON||!RUNTIME_NODE||!RUNTIME_NODE_MODULES||!RUNTIME_BIN_DIR)throw new Error('Set current SKILL_DIR and all bundled RUNTIME_NODE, RUNTIME_PYTHON, RUNTIME_NODE_MODULES, RUNTIME_BIN_DIR paths');
const spec=JSON.parse(await fs.readFile(path.join(project,'spec/deck_spec.json'),'utf8'));
const scene=JSON.parse(await fs.readFile(path.join(project,'spec/scene_graph.json'),'utf8'));
const plan=JSON.parse(await fs.readFile(path.join(project,'spec/edit_plan.json'),'utf8'));
const baseline=JSON.parse(await fs.readFile(path.join(project,'qa/baseline/scene_graph.json'),'utf8'));
const removed=new Set(plan.remove_components);
let previous=-1;while(previous!==removed.size){previous=removed.size;for(const n of baseline.nodes)if(removed.has(n.parent))removed.add(n.id);}
const active=scene.nodes.filter(n=>!removed.has(n.id));
const {finalizePresentation}=await import(pathToFileURL(path.join(SKILL_DIR,'container_tools/artifact_tool_utils.mjs')).href);
const result=await finalizePresentation({
  workspaceDir:project,
  candidatePath:path.join(project,'tmp/bound.pptx'),
  finalPath:path.join(project,spec.output),
  pythonExecutable:RUNTIME_PYTHON,
  integrityValidatorPath:path.join(SKILL_DIR,'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath:path.join(SKILL_DIR,'container_tools/inspect_presentation_layout_geometry.py'),
  layoutArgs:['--expected-slide-size-emu',spec.design_px.map(v=>Math.round(v*9525)).join(','),'--validate-bullet-geometry','--validate-heading-fit'],
  explicitTotalSlideCount:spec.slides,
  requiredNativeTableOwnerSlides:active.some(n=>n.kind==='table')?[spec.editable_slide]:[],
  requiredNativeChartOwnerSlides:active.some(n=>n.kind==='chart')?[spec.editable_slide]:[],
  fontPolicy:spec.font_policy??{basis:'design',families:[spec.style_tokens.font_zh??'Microsoft YaHei']},
  verifyArtifactToolImport:true,
  receiptPath:path.join(project,'qa/finalizer.json'),
});
console.log(JSON.stringify(result));
