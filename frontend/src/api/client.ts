export async function api<T=any>(url:string, options:RequestInit={}) : Promise<T> {
  const headers = options.body instanceof FormData ? (options.headers || {}) : {'Content-Type':'application/json',...(options.headers||{})}
  const r=await fetch(url,{...options,headers})
  const data=await r.json().catch(()=>({}))
  if(!r.ok) throw new Error(data.detail||'Ошибка запроса')
  return data
}
export const fmt=(n:number|undefined|null)=>n==null?'Не определено':new Intl.NumberFormat('ru-RU',{maximumFractionDigits:2}).format(n)
export const money=(n:number|undefined|null)=>n==null?'—':new Intl.NumberFormat('ru-RU',{style:'currency',currency:'RUB',maximumFractionDigits:2}).format(n)
