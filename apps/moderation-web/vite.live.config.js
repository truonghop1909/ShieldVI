import {defineConfig} from 'vite'
import path from 'node:path'
import original from './vite.config.js'
export default defineConfig(args=>{const config=typeof original==='function'?original(args):original;return {...config,
 server:{...config.server,fs:{allow:[path.resolve(process.cwd(),'..')]}},
 build:{...config.build,outDir:'dist-live',rollupOptions:{input:{live:path.resolve(process.cwd(),'live.html'),studio:path.resolve(process.cwd(),'studio.html')}}}}})
