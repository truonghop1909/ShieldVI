import test from 'node:test'
import assert from 'node:assert/strict'
import {acceptEvent,subscribeLive,liveRequest} from './live-transport.mjs'
const event=(id=1,revision=1,decision=0)=>({schema_version:'live-1.0',event_id:id,thread_id:'thread',content_id:'content',content_revision:revision,decision_version:decision})
const state=()=>({cursor:0,threadId:'thread',versions:new Map()})
test('cursor deduplication and stale revision do not rewind UI',()=>{const s=state();assert(acceptEvent(event(1,2,2),s));assert(!acceptEvent(event(1,2,2),s));assert(!acceptEvent(event(2,1,3),s));assert(!acceptEvent(event(3,2,1),s));assert(acceptEvent(event(4,2,3),s));assert.equal(s.cursor,4)})
test('wrong thread and malformed versions are rejected before cursor advances',()=>{const s=state();assert.throws(()=>acceptEvent({...event(),thread_id:'other'},s));assert.throws(()=>acceptEvent({...event(),content_revision:0},s));assert.equal(s.cursor,0)})
test('SSE chunked CRLF, bearer header and replay callback',async()=>{
 const original=globalThis.fetch;let urlSeen,headersSeen,stop;const received=[]
 const frame=`id: 1\r\nevent: conversation.message.created\r\ndata: ${JSON.stringify(event())}\r\n\r\n`,encoded=new TextEncoder().encode(frame)
 globalThis.fetch=async(url,options)=>{urlSeen=url;headersSeen=options.headers;return new Response(new ReadableStream({start(controller){for(let i=0;i<encoded.length;i+=3)controller.enqueue(encoded.slice(i,i+3));controller.close()}}),{status:200})}
 try{await new Promise((resolve,reject)=>{const timeout=setTimeout(()=>{stop?.();reject(new Error('SSE callback timed out'))},2000);stop=subscribeLive('/threads/thread/events','unit-token',{threadId:'thread',onEvent:value=>{received.push(value);stop();clearTimeout(timeout);resolve()}})});assert.equal(received.length,1);assert(!urlSeen.includes('unit-token'));assert.equal(headersSeen.Authorization,'Bearer unit-token')}
 finally{globalThis.fetch=original;stop?.()}
})
test('write retry keeps explicit idempotency key and excludes cookies',async()=>{const original=globalThis.fetch;const calls=[];globalThis.fetch=async(url,options)=>{calls.push({url,options});return new Response('{}',{status:200})};try{for(let i=0;i<2;i++)await liveRequest('/threads/thread/messages','unit-token',{method:'POST',body:{body:'hi'},key:'same-key'});assert.equal(calls[0].options.headers['Idempotency-Key'],calls[1].options.headers['Idempotency-Key']);assert.equal(calls[0].options.credentials,'omit');assert(!calls[0].url.includes('unit-token'))}finally{globalThis.fetch=original}})
