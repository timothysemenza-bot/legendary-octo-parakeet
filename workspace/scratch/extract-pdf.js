const fs=require('fs');
const zlib=require('zlib');
const input='C:/Users/timot/Downloads/TIMMY SEMENZA_Proposal.pdf';
const out='C:/Users/timot/Documents/Proposal-Microsite/workspace/scratch/text/timmy_proposal_extracted.txt';
const buf=fs.readFileSync(input);
const s=buf.toString('latin1');
let chunks=[];
const streamRe=/stream\r?\n([\s\S]*?)\r?\nendstream/g;
let m;
while((m=streamRe.exec(s))){
  const data=Buffer.from(m[1],'latin1');
  let dec=null;
  try{dec=zlib.inflateSync(data);}catch{}
  if(!dec){try{dec=zlib.inflateRawSync(data);}catch{}}
  if(!dec) dec=data;
  chunks.push(dec.toString('latin1'));
}
function decodePdfString(str){
  return str
    .replace(/\\([\\()])/g,'$1')
    .replace(/\\n/g,'\n')
    .replace(/\\r/g,'\r')
    .replace(/\\t/g,'\t')
    .replace(/\\b/g,'\b')
    .replace(/\\f/g,'\f')
    .replace(/\\(\d{1,3})/g,(_,o)=>String.fromCharCode(parseInt(o,8)));
}
let outParts=[];
for(const c of chunks){
  const textOps=[...c.matchAll(/\(([^)]{1,500})\)\s*Tj/g), ...c.matchAll(/\[(.*?)\]\s*TJ/gs)];
  for(const t of textOps){
    if(t[1]) outParts.push(decodePdfString(t[1]));
  }
  // fallback: keep readable lines if operator parsing misses
  const readable=c.split(/\r?\n/).filter(l=>/[A-Za-z]{3,}/.test(l) && l.length<300);
  outParts.push(...readable);
}
const cleaned=outParts.join('\n')
  .replace(/[^\x09\x0A\x0D\x20-\x7E]/g,' ')
  .replace(/[ ]{2,}/g,' ')
  .replace(/\n{3,}/g,'\n\n');
fs.writeFileSync(out, cleaned, 'utf8');
console.log('WROTE', out, 'chars', cleaned.length);
