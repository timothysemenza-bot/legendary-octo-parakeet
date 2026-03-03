const fs=require('fs');
const zlib=require('zlib');
const input='C:/Users/timot/Downloads/TIMMY SEMENZA_Proposal.pdf';
const out='C:/Users/timot/Documents/Proposal-Microsite/workspace/scratch/text/timmy_proposal_extracted.txt';
const buf=fs.readFileSync(input);
const s=buf.toString('latin1');
const streamRe=/stream\r?\n([\s\S]*?)\r?\nendstream/g;
let m; const streams=[];
while((m=streamRe.exec(s))){
  const raw=Buffer.from(m[1],'latin1');
  let dec=null; try{dec=zlib.inflateSync(raw);}catch{}
  if(!dec){try{dec=zlib.inflateRawSync(raw);}catch{}}
  streams.push((dec||raw).toString('latin1'));
}
const cmap=new Map();
function hexToStr(h){
  let out='';
  for(let i=0;i<h.length;i+=4){
    const cp=parseInt(h.slice(i,i+4),16);
    if(!Number.isNaN(cp)) out += String.fromCodePoint(cp);
  }
  return out;
}
for(const st of streams){
  const bfr=[...st.matchAll(/beginbfrange([\s\S]*?)endbfrange/g)];
  for(const blk of bfr){
    const lines=blk[1].split(/\r?\n/).map(x=>x.trim()).filter(Boolean);
    for(const ln of lines){
      let mm=ln.match(/^<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>$/);
      if(mm){
        let a=parseInt(mm[1],16), b=parseInt(mm[2],16), u=parseInt(mm[3],16);
        for(let c=a;c<=b;c++) cmap.set(c, String.fromCodePoint(u + (c-a)));
        continue;
      }
      mm=ln.match(/^<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*\[(.+)\]$/);
      if(mm){
        let a=parseInt(mm[1],16), b=parseInt(mm[2],16);
        const vals=[...mm[3].matchAll(/<([0-9A-Fa-f]+)>/g)].map(x=>hexToStr(x[1]));
        for(let c=a, i=0;c<=b && i<vals.length;c++,i++) cmap.set(c, vals[i]);
      }
    }
  }
}
function decodeHexGlyphs(hex){
  let out='';
  for(let i=0;i+4<=hex.length;i+=4){
    const code=parseInt(hex.slice(i,i+4),16);
    out += cmap.get(code) || '';
  }
  return out;
}
let text=[];
for(const st of streams){
  for(const mm of st.matchAll(/<([0-9A-Fa-f]{4,})>\s*Tj/g)){
    const d=decodeHexGlyphs(mm[1]); if(d.trim()) text.push(d);
  }
  for(const mm of st.matchAll(/\[(.*?)\]\s*TJ/gs)){
    let line='';
    for(const hm of mm[1].matchAll(/<([0-9A-Fa-f]{4,})>/g)) line += decodeHexGlyphs(hm[1]);
    if(line.trim()) text.push(line);
  }
}
const cleaned=text.join('\n')
  .replace(/\r/g,'')
  .replace(/[\t ]{2,}/g,' ')
  .replace(/\n{3,}/g,'\n\n');
fs.writeFileSync(out, cleaned, 'utf8');
console.log('cmap', cmap.size, 'chars', cleaned.length);
