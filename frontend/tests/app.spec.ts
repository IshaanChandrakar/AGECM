import {test,expect} from '@playwright/test';
import {Client} from '@stomp/stompjs';
const base=process.env.E2E_BASE_URL||'http://127.0.0.1:5183';
const keys=['temperature','humidity','coMax','ch4Max','distanceNow','devMax','statusWorst','faultAny'];
test('all eight measurements match the same stored channel entries in monitoring cards',async({page,request})=>{
 const response=await request.get('/api/system/status');expect(response.ok()).toBeTruthy();const status=await response.json();expect(status.mode).toBe('LIVE');
 await page.route('**/api/system/status',route=>route.fulfill({json:status}));await page.goto('/monitoring');
 for(const node of status.nodes){expect(node.latest).not.toBeNull();const card=page.locator(`[data-node-id="${node.id}"]`);await expect(card).toHaveAttribute('data-entry-id',String(node.latest.entryId));for(const key of keys){await expect(card.locator(`[data-metric="${key}"] strong`)).toContainText(Number(node.latest[key]).toLocaleString(undefined,{maximumFractionDigits:4}));}await expect(card).toContainText('Channel '+node.latest.channelId+' / entry '+node.latest.entryId);await expect(card).toContainText('ThingSpeak cloud timestamp');}
 await expect(page.locator('.central-card .badge')).toHaveText('Unverified');
});
test('eight time charts, comparison, selection, export and identifiable tooltips',async({page,request})=>{
 await page.goto('/analytics');await expect(page.locator('.chart-panel')).toHaveCount(8);await expect(page.locator('.recharts-line-curve')).toHaveCount(16);await expect(page.locator('.chart-panel').nth(6)).not.toContainText('Unmapped code 3');await expect(page.locator('.chart-panel').nth(7)).not.toContainText('Unmapped code 2');
 await page.getByRole('button',{name:'Node 01',exact:true}).click();await expect(page).toHaveURL(/node=node_01/);await expect(page.locator('.recharts-line-curve')).toHaveCount(8);
 const chart=page.locator('.chart-panel').first();await chart.scrollIntoViewIfNeeded();const box=await chart.locator('.recharts-wrapper').boundingBox();expect(box).not.toBeNull();await page.mouse.move(box!.x+box!.width*.7,box!.y+box!.height*.4);await expect(chart.locator('.sample-tooltip')).toBeVisible();
 const text=await chart.locator('.sample-tooltip').innerText();const match=text.match(/channel (\d+) \/ entry (\d+)/);expect(match).not.toBeNull();const history=await (await request.get('/api/nodes/node_01/history?size=2000')).json();const sample=history.content.find((r:any)=>String(r.channelId)===match![1]&&String(r.entryId)===match![2]);expect(sample).toBeTruthy();expect(text).toContain(Number(sample.temperature).toLocaleString(undefined,{maximumFractionDigits:4}));expect(text).toContain('cloud time');
 await page.getByLabel('Time range').selectOption('6');const download=page.waitForEvent('download');await page.getByRole('button',{name:'Export CSV'}).click();expect((await download).suggestedFilename()).toMatch(/^agecm-.*\.csv$/);
});
test('unknown binary meanings are never labeled healthy and partial data preserves other values',async({page,request})=>{
 const status=await (await request.get('/api/system/status')).json();status.contract.semanticsConfirmed=false;status.contract.faultValues={};status.contract.statusCodes={};status.nodes[0].latest.humidity=null;status.nodes[0].latest.coMax=0;status.nodes[0].latest.faultAny=0;status.nodes[0].health='PARTIAL_DATA';
 await page.route('**/api/system/status',route=>route.fulfill({json:status}));await page.goto('/monitoring');const card=page.locator('[data-node-id="node_01"]');await expect(card.locator('[data-metric="humidity"] strong')).toContainText('—');await expect(card.locator('[data-metric="coMax"] strong')).toContainText('0');await expect(card.locator('[data-metric="faultAny"]')).toContainText('Code 0 · meaning unconfirmed');await expect(card.locator('.node-card-top .badge')).toHaveText('Partial Data');
});
test('backend outage stays visible and cannot claim available data',async({page})=>{
 await page.route('**/api/**',r=>r.abort());await page.goto('/monitoring');await expect(page.getByRole('alert')).toContainText('backend is unavailable');await expect(page.locator('.node-card-top .badge').first()).toHaveText('Backend Unavailable');
});
test('alert details reflect firmware provenance rather than obsolete rules',async({page})=>{
 await page.route('**/api/alerts',route=>route.fulfill({json:{content:[{id:1,nodeId:'node_01',source:'cloud_hardware',condition:'FAULT_REPORTED',severity:'DATA',triggerText:'Local UI fixture: confirmed firmware fault',firstOccurredAt:new Date().toISOString(),lastOccurredAt:new Date().toISOString(),resolvedAt:null,recordId:1,ruleVersion:'sensor-v2'}]}}));await page.goto('/alerts');await page.getByRole('button',{name:'View alert 1'}).click();await expect(page.getByRole('dialog')).toContainText('sensor-v2');await expect(page.getByRole('dialog')).not.toContainText('Tilt');await page.getByRole('button',{name:'Close alert details'}).click();
});
test('all routes and images work on desktop and mobile without overflow',async({page})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));for(const width of [1440,390]){await page.setViewportSize({width,height:1000});for(const path of ['/','/monitoring','/analytics','/alerts','/architecture']){await page.goto(path);await expect(page.locator('main h1')).toBeVisible();expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),path+' '+width).toBeTruthy();}await page.goto('/');for(const image of await page.locator('img').all()){await image.scrollIntoViewIfNeeded();await expect.poll(()=>image.evaluate(i=>(i as HTMLImageElement).naturalWidth)).toBeGreaterThan(0);}}
 expect(errors).toEqual([]);
});
test('real STOMP update from the mock cloud is committed and source-isolated',async({request})=>{
 const client=new Client({brokerURL:base.replace('http','ws')+'/ws',reconnectDelay:0});
 try{const event=await new Promise<any>((resolve,reject)=>{const timer=setTimeout(()=>reject(new Error('No cloud telemetry event')),15000);client.onConnect=()=>client.subscribe('/topic/telemetry',m=>{clearTimeout(timer);resolve(JSON.parse(m.body));});client.onWebSocketError=()=>reject(new Error('WebSocket unavailable'));client.activate();});expect(event.source).toBe('cloud_hardware');expect(['100','200']).toContain(event.channelId);const history=await (await request.get('/api/nodes/'+event.nodeId+'/history?size=2000')).json();const row=history.content.find((r:any)=>r.entryId===event.entryId&&r.channelId===event.channelId);expect(row.temperature).toBe(event.temperature);expect(row.sampleAt).toBe(event.sampleAt);
 }finally{await client.deactivate();}
});
test('ingestion rejects a bad token',async({request})=>{
 const status=await (await request.get('/api/system/status')).json();const row=status.nodes[0].latest;const result=await request.post('/api/telemetry',{headers:{'X-Ingestion-Token':'wrong-test-token'},data:row});expect(result.status()).toBe(401);
});
