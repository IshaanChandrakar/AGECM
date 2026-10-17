import { test, expect } from '@playwright/test';
import { Client } from '@stomp/stompjs';

test('homepage imagery, navigation and mobile layout',async({page})=>{
 await page.goto('/');await expect(page.getByRole('heading',{name:/Monitoring ground/})).toBeVisible();
 const images=page.locator('img');for(const image of await images.all()){await image.scrollIntoViewIfNeeded();await expect.poll(()=>image.evaluate(i=>(i as HTMLImageElement).naturalWidth)).toBeGreaterThan(0);}
 expect(await images.evaluateAll(elements=>elements.every(i=>(i as HTMLImageElement).naturalWidth>0))).toBeTruthy();
 await page.getByRole('link',{name:'Open dashboard',exact:true}).click();await expect(page.getByRole('heading',{name:/Live geotechnical monitoring/})).toBeVisible();
 await expect(page.getByRole('heading',{name:'Node 01',exact:true})).toBeVisible();await expect(page.getByRole('heading',{name:'Node 02',exact:true})).toBeVisible();
 await page.setViewportSize({width:390,height:844});await page.goto('/');await page.getByRole('button',{name:'Open navigation'}).click();await page.getByRole('navigation').getByRole('link',{name:'Architecture',exact:true}).click();await expect(page.getByRole('heading',{name:/A clear path/})).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1)).toBeTruthy();
});
test('API-backed telemetry, charts, alert details and export',async({page})=>{
 await page.goto('/monitoring');await expect(page.getByText('DEMONSTRATION MODE',{exact:true})).toBeVisible();
 await expect(page.locator('.node-card').first().locator('.metric strong').first()).not.toHaveText('—°');
 await page.goto('/analytics');await expect(page.locator('.chart-panel')).toHaveCount(5);await expect(page.locator('.recharts-wrapper').first()).toBeVisible();
 await page.getByRole('button',{name:'Node 01',exact:true}).click();await expect(page).toHaveURL(/node=node_01/);
 await page.getByLabel('Time range').selectOption('6');const download=page.waitForEvent('download');await page.getByRole('button',{name:'Export CSV'}).click();expect((await download).suggestedFilename()).toBe('agecm-telemetry.csv');
 await page.goto('/alerts');await expect(page.locator('.alert-table tbody tr').first()).toBeVisible();await page.getByRole('button',{name:/View alert/}).first().click();await expect(page.getByRole('dialog')).toBeVisible();await page.getByRole('button',{name:'Close alert details'}).click();await expect(page.getByRole('dialog')).toHaveCount(0);
});
test('backend failure suppresses current condition claims',async({page})=>{
 await page.route('**/api/**',route=>route.abort());await page.goto('/monitoring');await expect(page.getByRole('alert')).toContainText('backend is unavailable');await expect(page.locator('.node-card-top .badge').first()).toHaveText('Unavailable');
});
test('missing live hardware stays empty and central remains unverified',async({page})=>{
 await page.route('**/api/system/status',route=>route.fulfill({json:{mode:'LIVE',source:'cloud_hardware',serverTime:new Date().toISOString(),database:'HEALTHY',expectedReportSeconds:30,staleSeconds:95,nodes:['node_01','node_02'].map((id,i)=>({id,role:'SENSING',position:'Monitoring position '+(i+1),latest:null,health:'NOT_CONFIGURED',state:'UNAVAILABLE',ageSeconds:null,channelConfigured:false,expectedReportSeconds:30,cloud:{nodeId:id,status:'NOT_CONFIGURED',lastEntryId:0}})),central:{id:'node_03',status:'UNVERIFIED'}}}));
 await page.goto('/monitoring');await expect(page.getByText('LIVE · THINGSPEAK',{exact:true})).toBeVisible();await expect(page.locator('.metrics .metric strong')).toHaveCount(6);expect(await page.locator('.metrics .metric strong').allTextContents()).toEqual(['—°','—mm','—g','—°','—mm','—g']);await expect(page.locator('.central-card .badge')).toHaveText('Unverified');
});
test('all routes render without runtime errors at desktop and mobile widths',async({page})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 for(const width of [1440,390]){await page.setViewportSize({width,height:1000});for(const path of ['/','/monitoring','/analytics','/alerts','/architecture']){await page.goto(path);await expect(page.locator('main h1')).toBeVisible();expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1),path+' '+width).toBeTruthy();}}
 expect(errors).toEqual([]);
});
test('STOMP broadcasts committed telemetry and PostgreSQL history returns it',async({request})=>{
 const client=new Client({brokerURL:'ws://127.0.0.1:8080/ws',reconnectDelay:0});
 const boot='e2e-'+Date.now();let onMessage:(data:string)=>void=()=>{};
 const event=new Promise<string>(resolve=>{onMessage=resolve;});
 try{await new Promise<void>((resolve,reject)=>{client.onConnect=()=>{client.subscribe('/topic/telemetry',m=>{if(JSON.parse(m.body).bootId===boot)onMessage(m.body);});resolve();};client.onWebSocketError=()=>reject(new Error('WebSocket unavailable'));client.activate();});
 const result=await request.post('http://127.0.0.1:8080/api/telemetry',{headers:{'X-Ingestion-Token':'local-development-token'},data:{nodeId:'node_01',source:'demo',schemaVersion:'1.0',bootId:boot,sequence:1,acquiredAt:new Date().toISOString(),tilt:1,displacement:2,vibration:.02,tiltRate:.001,displacementVelocity:.001,qualityFlags:0,calibrated:true,featureReady:true,ruleVersion:'lab-rule-v1',state:'NORMAL',health:'HEALTHY'}});expect(result.ok()).toBeTruthy();
 const received=await Promise.race([event,new Promise<string>((_,reject)=>setTimeout(()=>reject(new Error('No STOMP telemetry')),5000))]);expect(JSON.parse(received).source).toBe('demo');const history=await request.get('http://127.0.0.1:8080/api/nodes/node_01/history?size=1');expect((await history.json()).content[0].bootId).toBe(boot);
 }finally{await client.deactivate();}
});
