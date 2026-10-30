import {useEffect,useRef} from 'react'
import * as THREE from 'three'
import {OrbitControls} from 'three/examples/jsm/controls/OrbitControls.js'
import {STLLoader} from 'three/examples/jsm/loaders/STLLoader.js'
import {ThreeMFLoader} from 'three/examples/jsm/loaders/3MFLoader.js'

export default function ThreeViewer({url,ext}:{url:string,ext:string}){
 const ref=useRef<HTMLDivElement>(null)
 useEffect(()=>{
  if(!ref.current)return
  const el=ref.current; const scene=new THREE.Scene(); scene.background=new THREE.Color(0x151922)
  const camera=new THREE.PerspectiveCamera(45,el.clientWidth/el.clientHeight,.1,100000);camera.position.set(120,100,140)
  const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(devicePixelRatio);renderer.setSize(el.clientWidth,el.clientHeight);el.appendChild(renderer.domElement)
  scene.add(new THREE.HemisphereLight(0xffffff,0x303040,2))
  const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true
  const loader=ext==='.3mf'?new ThreeMFLoader():new STLLoader()
  loader.load(url,(obj:any)=>{
   let model:any=obj
   if(ext!=='.3mf'){const mat=new THREE.MeshStandardMaterial({color:0x8ca9c4,metalness:.1,roughness:.7});model=new THREE.Mesh(obj,mat)}
   scene.add(model)
   const box=new THREE.Box3().setFromObject(model), size=box.getSize(new THREE.Vector3()), center=box.getCenter(new THREE.Vector3())
   model.position.sub(center); const max=Math.max(size.x,size.y,size.z)||100
   camera.position.set(max*1.6,max*1.3,max*1.6);camera.near=max/1000;camera.far=max*100;camera.updateProjectionMatrix();controls.target.set(0,0,0)
  })
  const ro=new ResizeObserver(()=>{camera.aspect=el.clientWidth/el.clientHeight;camera.updateProjectionMatrix();renderer.setSize(el.clientWidth,el.clientHeight)})
  ro.observe(el); let id=0; const loop=()=>{id=requestAnimationFrame(loop);controls.update();renderer.render(scene,camera)};loop()
  return()=>{cancelAnimationFrame(id);ro.disconnect();renderer.dispose();el.removeChild(renderer.domElement)}
 },[url,ext])
 return <div className="viewer" ref={ref}/>
}
