import {useEffect,useState} from 'react'
import FilesPage from './pages/FilesPage'
import CalculatorPage from './pages/CalculatorPage'
import SettingsPage from './pages/SettingsPage'
import {api} from './api/client'

export default function App(){
 const [page,setPage]=useState<'files'|'calc'|'settings'>('files'),[calcProject,setCalcProject]=useState<any>(null),[dark,setDark]=useState(true)
 useEffect(()=>{document.body.dataset.theme=dark?'dark':'light'},[dark])
 const openCalc=(p:any)=>{setCalcProject(p);setPage('calc')}
 return <div className="app">
  <aside><div className="brand"><span className="cube">◇</span><div><b>3D PRINT</b><small>MANAGER</small></div></div>
   <nav><button className={page==='files'?'active':''} onClick={()=>setPage('files')}>▦ <span>Файлы</span></button><button className={page==='calc'?'active':''} onClick={()=>setPage('calc')}>₽ <span>Калькулятор</span></button></nav>
   <div className="sidebottom"><button onClick={()=>setDark(!dark)}>◐ <span>{dark?'Светлая тема':'Тёмная тема'}</span></button><button onClick={()=>setPage('settings')}>⚙ <span>Настройки</span></button></div>
  </aside>
  <main><header><div><h1>{page==='files'?'Библиотека':page==='calc'?'Калькулятор':'Настройки'}</h1><p>Локально · без облака</p></div><div className="status">● Готово</div></header>
   {page==='files'&&<FilesPage onCalc={openCalc}/>}
   {page==='calc'&&<CalculatorPage project={calcProject}/>}
   {page==='settings'&&<SettingsPage/>}
  </main>
 </div>
}
