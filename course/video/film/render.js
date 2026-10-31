const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1920,height:1080}});
await p.goto('file://'+process.argv[2]+'/W01-L01.html#capture');await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(800);
const fps=25,total=await p.evaluate(()=>window.TOTAL);
for(let i=0;i<total*fps;i++){await p.evaluate(t=>window.seek(t),i/fps);await p.screenshot({path:`frames/f${String(i).padStart(5,'0')}.jpg`,type:'jpeg',quality:92});
if(i%250==0)console.log('frame',i);}
await b.close();console.log('done');})();
