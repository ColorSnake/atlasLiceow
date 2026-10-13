from pathlib import Path
import shutil,json
root=Path(__file__).parent
source=root/'gui-server-starter'
target=root/'licea'
# Preserve the static application as the public atlas; dist becomes build output.
shutil.copytree(target/'dist',target/'public/atlas',dirs_exist_ok=True)
for item in source.iterdir():
    if item.name in ('.git','.openai','.gitignore','README.md','node_modules','.sites-runtime'):continue
    dest=target/item.name
    if item.is_dir():shutil.copytree(item,dest,dirs_exist_ok=True)
    else:shutil.copy2(item,dest)
manifest=json.loads((target/'.openai/hosting.json').read_text())
manifest.pop('static',None);manifest['d1']={'binding':'DB'}
(target/'.openai/hosting.json').write_text(json.dumps(manifest,indent=2)+'\n')
with (target/'.gitignore').open('a') as f:f.write('\nnode_modules/\n.vinext/\n.wrangler/\ndist/\n.env*\n')
p=target/'scripts/datasets.py'
p.write_text(p.read_text(encoding='utf-8').replace("DIST = ROOT / 'dist'","DIST = ROOT / 'public' / 'atlas'"),encoding='utf-8')
