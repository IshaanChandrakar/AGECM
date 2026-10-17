import { Link } from 'react-router-dom';
import { ArrowDown, ArrowUpRight, ArrowRight } from 'lucide-react';
import { ArrowLink, ArchitectureDiagram, Cross, Image, Mode, Slash } from './components';

const capabilities=[
 {n:'01',title:'Distributed sensing',text:'Two sensing positions. A clearer view of movement. ESP32 nodes observe tilt, relative displacement and acceleration-derived vibration.',image:'field-sensing',alt:'Mine technician examining a wall-mounted sensor and a separate reference target',to:'/monitoring',link:'Explore the sensing nodes'},
 {n:'02',title:'Cloud connectivity',text:'Separate ThingSpeak channels connect the sensing nodes to two independent readers: the laptop pipeline and a central ESP32 display.',image:'central-display',alt:'Illustrative ESP32 and local display on a laboratory bench',to:'/architecture',link:'Follow the data'},
 {n:'03',title:'Movement analysis',text:'From measurements to context. The laptop pipeline checks data quality, tracks changes and evaluates configurable laboratory rules.',image:'laboratory-rig',alt:'University laboratory tilt rig with microcontrollers and a separate distance target',to:'/analytics',link:'Examine the trends'}
];
export default function Home(){return <>
 <section className="home-hero dark"><div className="shell">
   <div className="hero-topline"><span className="eyebrow">OBSERVE THE GROUND. UNDERSTAND THE CHANGE.</span><span className="project-tag">VIT VELLORE / COMPUTER NETWORKS</span></div>
   <div className="hero-title"><h1>Monitoring ground.<br/>Building safer futures.</h1><Cross/></div>
   <div className="hero-image-wrap"><Image name="mine-workers" alt="Mine workers in protective equipment inspecting a monitoring point inside a supported underground tunnel" priority/>
     <div className="hero-image-shade"/><div className="hero-caption"><span className="eyebrow">A MORE INFORMED PERSPECTIVE</span><p>Small movements.<br/>Meaningful observations.</p><div className="hero-caption-copy">A geotechnical monitoring prototype connecting two sensing positions, cloud telemetry and movement analysis.</div><ArrowLink to="/monitoring">Explore live monitoring</ArrowLink></div>
     <span className="image-credit">ILLUSTRATIVE MINE ENVIRONMENT · AI-GENERATED</span><a className="scroll-cue" href="#capabilities" aria-label="Scroll to core capabilities"><ArrowDown size={20}/></a>
   </div>
   <div className="hero-bottom"><Mode/><span>Adaptive Geotechnical Edge-Consensus Mesh</span><Link to="/architecture">Understand the architecture <ArrowUpRight size={17}/></Link></div>
 </div></section>
 <section id="capabilities" className="capabilities dark"><div className="shell"><div className="section-heading centered"><span className="eyebrow">01 / WHAT WE OBSERVE</span><h2>Grounded in data<Slash/></h2><p>From the rock face to the screen. A focused approach<br className="desktop-break"/> to observing structural movement.</p></div>
   <div className="capability-grid">{capabilities.map(c=><article className="capability" key={c.n}><span className="card-index">{c.n} / {c.title.toUpperCase()}</span><p>{c.text}</p><div className="capability-photo"><Image name={c.image} alt={c.alt}/></div><ArrowLink to={c.to}>{c.link}</ArrowLink></article>)}</div>
 </div></section>
 <section className="architecture-preview light"><div className="shell"><div className="section-heading split"><div><span className="eyebrow">02 / THE CONNECTED PICTURE</span><h2>Three boards.<br/>One shared view<Slash/></h2></div><div><p>Two boards sense. One board displays. The laptop and central monitor read the same cloud channels independently.</p><ArrowLink to="/architecture">Explore the architecture</ArrowLink></div></div><ArchitectureDiagram compact/>
 <div className="section-footnote"><span>CURRENT DESIGN / WI-FI + HTTPS + THINGSPEAK</span><span>Cloud-mediated monitoring · Laboratory prototype</span></div></div></section>
 <section className="project-vision dark"><div className="shell vision-grid"><div className="vision-image"><Image name="laboratory-rig" alt="Illustrative laboratory rig used to explore tilt and relative displacement"/><span className="image-credit">LABORATORY CONCEPT · AI-GENERATED</span></div><div className="vision-copy"><span className="eyebrow">03 / BUILT TO LEARN. DESIGNED TO EVOLVE.</span><h2>A measured step<br/>toward resilience.</h2><p>Start with a traceable path from sensor to screen. Understand the signal, its age and its limitations before drawing a conclusion.</p><div className="vision-scope"><div><span className="tiny-label">CURRENT PROTOTYPE DESIGN</span><p>Wi-Fi uploads, ThingSpeak collection, laptop analysis and an independent central display.</p></div><div><span className="tiny-label orange">FUTURE SCOPE</span><p>Local central analysis and direct LoRa fallback. Planned, with hardware and field validation still ahead.</p></div></div><ArrowLink to="/architecture#future">Where the project goes next</ArrowLink></div></div></section>
 <section className="home-cta light"><div className="shell"><div><span className="eyebrow">LOOK CLOSER</span><h2>See the signals.<br/>Understand the story.</h2></div><Link className="round-cta" to="/monitoring" aria-label="Open monitoring dashboard"><ArrowUpRight size={54}/></Link><p>Explore node measurements, movement trends<br/>and the health behind every reading.</p></div></section>
 </>;}
