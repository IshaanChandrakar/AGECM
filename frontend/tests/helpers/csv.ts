export function parseCsv(input:string):Record<string,string>[] {
 const rows:string[][]=[];let row:string[]=[],value='',quoted=false;const text=input.replace(/^\uFEFF/,'');
 for(let i=0;i<text.length;i++){const c=text[i];if(quoted){if(c==='"'&&text[i+1]==='"'){value+='"';i++;}else if(c==='"')quoted=false;else value+=c;}else if(c==='"')quoted=true;else if(c===','){row.push(value);value='';}else if(c==='\r'&&text[i+1]==='\n'){row.push(value);rows.push(row);row=[];value='';i++;}else if(c==='\n'){row.push(value);rows.push(row);row=[];value='';}else value+=c;}
 if(value||row.length){row.push(value);rows.push(row);}const header=rows.shift()||[];return rows.filter(r=>r.length>1).map(r=>Object.fromEntries(header.map((h,i)=>[h,r[i]??''])));
}
