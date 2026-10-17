import { createContext, useContext, useEffect, useRef, useState, useCallback } from 'react';
import { Client } from '@stomp/stompjs';
import type { SystemStatus, Alert, Page, Reading } from './types';

export async function get<T>(path:string, signal?:AbortSignal):Promise<T>{
 const response=await fetch('/api'+path,{signal:signal || AbortSignal.timeout(10000)});
 if(!response.ok)throw new Error(`Monitoring API returned ${response.status}`);
 return response.json();
}
type Data={status:SystemStatus|null;alerts:Alert[];error:string|null;loading:boolean;lastUpdate:Date|null;socket:boolean;revision:number;refresh:()=>void};
const Context=createContext<Data>(null!);
export function DataProvider({children}:{children:React.ReactNode}){
 const [status,setStatus]=useState<SystemStatus|null>(null),[alerts,setAlerts]=useState<Alert[]>([]),[error,setError]=useState<string|null>(null);
 const [lastUpdate,setUpdate]=useState<Date|null>(null),[socket,setSocket]=useState(false),[revision,setRevision]=useState(0);
 const busy=useRef(false),alive=useRef(true);
 const refresh=useCallback(async()=>{if(busy.current)return;busy.current=true;try{
   const [s,a]=await Promise.all([get<SystemStatus>('/system/status'),get<Page<Alert>>('/alerts')]);
   if(alive.current){setStatus(s);setAlerts(a.content);setUpdate(new Date());setError(null);setRevision(n=>n+1);}
 }catch{if(alive.current)setError('The backend is unavailable. Displayed measurements may be out of date.');}finally{busy.current=false;}},[]);
 useEffect(()=>{alive.current=true;refresh();const timer=setInterval(refresh,5000);let pending:ReturnType<typeof setTimeout>|null=null;
 const client=new Client({brokerURL:`${location.protocol==='https:'?'wss':'ws'}://${location.host}/ws`,reconnectDelay:5000,heartbeatIncoming:10000,heartbeatOutgoing:10000,
   onConnect:()=>{setSocket(true);for(const topic of ['telemetry','alerts','health'])client.subscribe('/topic/'+topic,()=>{if(!pending)pending=setTimeout(()=>{pending=null;refresh();},350);});},
   onWebSocketClose:()=>setSocket(false),onStompError:()=>setSocket(false)});
 client.activate();return()=>{alive.current=false;clearInterval(timer);if(pending)clearTimeout(pending);void client.deactivate();};},[refresh]);
 return <Context.Provider value={{status,alerts,error,loading:!status&&!error,lastUpdate,socket,revision,refresh}}>{children}</Context.Provider>;
}
export const useData=()=>useContext(Context);
export function useHistory(hours:number){
 const {revision}=useData();const [rows,setRows]=useState<Reading[]>([]),[error,setError]=useState<string|null>(null),[loading,setLoading]=useState(true),[total,setTotal]=useState(0);
 useEffect(()=>{const controller=new AbortController();let active=true;setLoading(true);
 const query=`?size=1000&start=${encodeURIComponent(new Date(Date.now()-hours*3600000).toISOString())}`;
 Promise.all(['node_01','node_02'].map(node=>get<Page<Reading>>('/nodes/'+node+'/history'+query,controller.signal))).then(pages=>{if(active){setRows(pages.flatMap(p=>p.content).sort((a,b)=>Date.parse(a.acquiredAt)-Date.parse(b.acquiredAt)));setTotal(pages.reduce((n,p)=>n+p.totalElements,0));setError(null);}}).catch(()=>{if(active)setError('Trend history could not be loaded.');}).finally(()=>{if(active)setLoading(false);});
 return()=>{active=false;controller.abort();};},[hours,Math.floor(revision/2)]);
 return {rows,error,loading,total};
}
export const dateTime=(value:string|null|undefined)=>value?new Date(value).toLocaleString(undefined,{month:'short',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit'}):'Awaiting data';
export const shortTime=(value:string|number)=>new Date(value).toLocaleTimeString(undefined,{hour:'2-digit',minute:'2-digit',second:'2-digit'});
export const label=(value:string)=>value.toLowerCase().replaceAll('_',' ').replace(/\b\w/g,c=>c.toUpperCase());
export const nodeName=(id:string)=>id==='node_01'?'Node 01':'Node 02';
