import { Activity, ArrowUpRight, Clock3, Radio, Monitor, RefreshCw } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Badge, DataNotice, Mode, PageHeading } from './components';
import { dateTime, label, nodeName, useData } from './data';
import type { SensingNode } from './types';

function Metric({title,value,unit}:{title:string;value:number|null|undefined;unit:string}){return <div className="metric"><span>{title}</span><strong>{value==null?'—':value.toFixed(3)}<small>{unit}</small></strong></div>;}
function NodeCard({node,offline}:{node:SensingNode;offline:boolean}){
 const r=node.latest;const health=offline?'BACKEND_UNAVAILABLE':node.health;
 const state=offline?'UNAVAILABLE':node.state;
 return <article className="node-card"><div className="node-card-top"><span className="node-icon"><Radio size={22}/></span><div><span className="tiny-label">{node.position}</span><h2>{nodeName(node.id)}</h2></div><Badge value={state}/></div>
 <div className={'metrics '+(health!=='HEALTHY'?'aged-values':'')}><Metric title="Tilt angle" value={r?.tilt} unit="°"/><Metric title="Relative displacement" value={r?.displacement} unit="mm"/><Metric title="Vibration proxy" value={r?.vibration} unit="g"/></div>
 <div className="rates"><div><span>Tilt rate</span><strong>{r?.tiltRate==null?'Calculating':r.tiltRate.toFixed(4)+' °/s'}</strong></div><div><span>Displacement velocity</span><strong>{r?.displacementVelocity==null?'Calculating':r.displacementVelocity.toFixed(4)+' mm/s'}</strong></div></div>
 <dl className="node-details"><div><dt>Data health</dt><dd><Badge value={health}/></dd></div><div><dt>Sensor validity</dt><dd>{!r?'Awaiting data':r.qualityFlags!==0?'Invalid · flags '+r.qualityFlags:r.calibrated?'Calibrated':'Not ready'}</dd></div><div><dt>Acquired</dt><dd>{dateTime(r?.acquiredAt)}</dd></div><div><dt>Received</dt><dd>{dateTime(r?.receivedAt)}</dd></div><div><dt>Cloud read status</dt><dd>{r?.source==='demo'?'Not used in simulation':node.cloud?.status||'Awaiting configuration'}</dd></div><div><dt>Data age</dt><dd>{node.ageSeconds==null?'—':node.ageSeconds+' seconds'}</dd></div><div><dt>Source</dt><dd>{r?.source==='demo'?'Simulation':r?.source==='cloud_hardware'?'ThingSpeak · entry '+r.entryId:'Awaiting hardware data'}</dd></div></dl>
 {health!=='HEALTHY'&&<p className="node-note">{r?'Last received measurements are shown for context. Movement classification is unavailable.':'No measurements are available for this sensing position.'}</p>}
 <Link className="node-link" to={'/analytics?node='+node.id}>View sensor trends <ArrowUpRight size={17}/></Link></article>;
}
export default function Monitoring(){const {status,error,lastUpdate,socket,refresh,alerts}=useData();return <div className="workspace light"><div className="shell">
 <PageHeading eyebrow="THE MONITORING DESK / 01" title="Live geotechnical monitoring" description="Telemetry and movement indicators from two sensing positions." image="field-sensing"/>
 <div className="workspace-toolbar"><Mode/><span><Clock3 size={15}/> Updated {lastUpdate?lastUpdate.toLocaleTimeString():'—'}</span><span><Activity size={15}/>{socket?'WebSocket connected':'REST polling · 5 s'}</span><button className="text-button" onClick={refresh}><RefreshCw size={15}/>Refresh</button></div>
 <DataNotice/>
 <div className="node-grid">{(status?.nodes||['node_01','node_02'].map((id,i)=>({id,role:'SENSING',position:'Monitoring position '+(i+1),latest:null,health:'NO_DATA',state:'UNAVAILABLE',ageSeconds:null,channelConfigured:false,expectedReportSeconds:30,cloud:null!}))).map(node=><NodeCard key={node.id} node={node} offline={!!error}/>)}</div>
 <div className="monitor-lower"><article className="central-card"><div className="central-icon"><Monitor size={32}/></div><div><span className="tiny-label">NODE 03 / CENTRAL MONITOR</span><h3>An independent perspective.</h3><p>Independent ThingSpeak reader and local display. This board has no sensing role and reads both channels directly.</p><Badge value="UNVERIFIED"/><p className="small muted">No central-device heartbeat is integrated. Backend connectivity does not verify this hardware.</p></div></article>
 <article className="activity-card"><div className="card-head"><h3>Recent monitoring activity</h3><Link to="/alerts">All alerts <ArrowUpRight size={15}/></Link></div>{alerts.length?alerts.slice(0,3).map(a=><div className="activity-row" key={a.id}><span className={'activity-dot '+a.severity.toLowerCase()}/><div><strong>{nodeName(a.nodeId)} · {label(a.condition)}</strong><span>{dateTime(a.firstOccurredAt)} · {a.source==='demo'?'Simulation':'Cloud hardware'}</span></div><Badge value={a.resolvedAt?'RESOLVED':'ACTIVE'}/></div>):<p className="empty-inline">No alert episodes recorded.</p>}
 {status?.nodes.some(n=>n.latest)&&<p className="small muted activity-last">Latest telemetry: {dateTime(status.nodes.map(n=>n.latest?.receivedAt).filter(Boolean).sort().at(-1))}</p>}</article></div>
 <div className="workspace-footnote"><span>Only tilt, relative displacement and an acceleration-derived vibration proxy are measured.</span><span>Cloud reports: {status?.expectedReportSeconds||30} s · UI polling: 5 s{status?.mode==='DEMO'?' · Demo source: 2 s':''}</span></div>
 </div></div>;}
