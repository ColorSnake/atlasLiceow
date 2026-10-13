from pathlib import Path
import subprocess,json,shutil,tarfile
root=Path(__file__).absolute().parent
project=root/'licea';stage=root/'gui-stage-oct13'
helper=Path('C:/Users/lukasz/.codex/plugins/cache/openai-curated-remote/sites/1.0.0/skills/sites/scripts/prepare-site-build.cjs')
kind='worker' if stage.exists() else subprocess.check_output(['node',str(helper),str(project),str(stage/'dist')],text=True).strip()
source=json.loads((project/'.openai/hosting.json').read_text())
built=json.loads((project/'dist/.openai/hosting.json').read_text())
if source.get('artifact_metadata') and source['artifact_metadata']!=built.get('artifact_metadata',source['artifact_metadata']):raise RuntimeError('Attribution conflict')
if built.get('artifact_metadata'):source['artifact_metadata']=built['artifact_metadata']
(stage/'dist/.openai').mkdir(exist_ok=True,parents=True)
(stage/'dist/.openai/hosting.json').write_text(json.dumps(source,indent=2)+'\n')
shutil.copytree(project/'drizzle',stage/'dist/.openai/drizzle',dirs_exist_ok=True)
archive=root/'gui-import-site.tar.gz'
with tarfile.open(archive,'w:gz') as tar:tar.add(stage/'dist',arcname='dist')
with tarfile.open(archive) as tar:
 names=tar.getnames()
 assert 'dist/.openai/hosting.json' in names
 assert 'dist/.openai/drizzle/0000_lean_stepford_cuckoos.sql' in names
 assert 'dist/server/index.js' in names
 print(kind,'archive ready;',len(names),'entries;',archive.stat().st_size,'bytes')
