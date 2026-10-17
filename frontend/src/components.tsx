import { ArrowUpRight, ArrowRight, Radio, Cloud, Cpu, Database, Monitor, Wifi, AlertTriangle } from 'lucide-react';
import { Link } from 'react-router-dom';
import { label, useData } from './data';

export function Cross({small=false}:{small?:boolean}){return <span aria-hidden="true" className={`cross ${small?'small':''}`}><i/><i/></span>;}
export function Slash(){return <span className="slashes" aria-hidden="true"><i/><i/></span>;}
export function ArrowLink({to,children,className=''}:{to:string;children:React.ReactNode;className?:string}){return <Link className={'arrow-link '+className} to={to}>{children}<ArrowUpRight size={20}/></Link>;}
export function Image({name,alt,className='',priority=false}:{name:string;alt:string;className?:string;priority?:boolean}){
 return <img className={className} src={'/images/'+name+'.jpg'} alt={alt} loading={priority?'eager':'lazy'} decoding="async" onError={e=>{e.currentTarget.style.visibility='hidden';e.currentTarget.parentElement?.classList.add('image-unavailable');}}/>;
}
export function Badge({value}:{value:string}){return <span className={'badge '+value.toLowerCase()}><span/>{label(value)}</span>;}
export function Mode(){const {status}=useData();return <span className="mode"><span/>{status?.mode==='LIVE'?'LIVE · THINGSPEAK':status?'DEMONSTRATION MODE':'CONNECTING TO BACKEND'}</span>;}
export function DataNotice(){const {error,loading,status}=useData();return <>{error&&<div className="notice error" role="alert"><AlertTriangle size={18}/>{error}</div>}{loading&&<div className="notice" role="status">Connecting to the monitoring backend…</div>}{status&&<div className="notice"><span className="notice-dot"/>{status.mode==='DEMO'?'Simulated laboratory measurements. No physical hardware connection is implied.':'Physical channel data only. Missing or stale values are unavailable.'}</div>}</>;}
export function PageHeading({eyebrow,title,description,image}:{eyebrow:string;title:string;description:string;image:string}){return <header className="page-heading"><div><div className="eyebrow">{eyebrow}</div><h1>{title}<span className="orange">.</span></h1><p>{description}</p></div><div className="page-heading-image"><Image name={image} alt={image==='laboratory-rig'?'Illustrative laboratory tilt and displacement test rig':'Illustrative geotechnical monitoring equipment'}/></div></header>;}
const Box=({icon:Icon,title,sub}:{icon:typeof Cpu;title:string;sub:string})=><div className="flow-box"><Icon size={24}/><strong>{title}</strong><span>{sub}</span></div>;
export function ArchitectureDiagram({compact=false}:{compact?:boolean}){return <div className={'architecture-diagram '+(compact?'compact':'')} role="img" aria-label="Two sensing ESP32 nodes write to separate ThingSpeak channels. The Python adapter and central monitoring ESP32 independently read the cloud. Python sends to Spring Boot, PostgreSQL and React. The central board drives its display.">
 <div className="flow-producers"><Box icon={Radio} title="ESP32 · Node 01" sub="MPU6050 + VL53L0X"/><Box icon={Radio} title="ESP32 · Node 02" sub="MPU6050 + VL53L0X"/></div>
 <div className="flow-line"><span>Wi-Fi / HTTPS Write API</span><ArrowRight/></div><Box icon={Cloud} title="ThingSpeak" sub="Two independent private channels"/>
 <div className="flow-line"><span>Independent HTTPS reads</span><ArrowRight/></div>
 <div className="flow-consumers"><div className="flow-main"><Box icon={Cpu} title="Python adapter" sub="Validate · derive · classify"/><span className="flow-down">↓</span><Box icon={Database} title="Spring Boot + PostgreSQL" sub="REST · history · alerts · STOMP"/><span className="flow-down">↓</span><Box icon={Monitor} title="React dashboard" sub="Laptop monitoring & analytics"/></div><div className="flow-central"><Box icon={Wifi} title="ESP32 · Node 03" sub="Independent cloud reader"/><span className="flow-down">↓</span><Box icon={Monitor} title="Local display" sub="Measurements + data age"/><span className="flow-note">Display hardware integration unverified</span></div></div>
 </div>;}
