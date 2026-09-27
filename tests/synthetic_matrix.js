// Synthetic boundary test matrix for the All Threads Status Board.
// Loads the board's REAL <script> (extracted verbatim from index.html) in a
// Node vm sandbox with minimal DOM stubs, then exercises daysBetween,
// compute(), isNextDue(), matches() and cardHTML() against synthetic tasks
// at date boundaries: 7/14/30-day windows, month/year transitions, today,
// tomorrow, overdue, and terminal-status (agreed/rejected) exclusions.
//
// Run: node tests/synthetic_matrix.js   (exit 0 = all pass)
const fs = require('fs');
const vm = require('vm');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
const scriptSrc = html.match(/<script>([\s\S]*)<\/script>/)[1]
  + '\n;globalThis.__board={state,STATUS,TERMINAL,daysBetween,compute,isNextDue,matches,cardHTML,sortTasks,esc};';

const stubEl = () => ({
  addEventListener(){}, appendChild(){},
  classList:{add(){},remove(){}}, style:{}, dataset:{},
  _h:'', set innerHTML(v){this._h=v;}, get innerHTML(){return this._h;},
  textContent:'', value:'', checked:false,
  querySelector(){return null;}, querySelectorAll(){return [];}, closest(){return null;},
});
const sandbox = {
  document:{
    getElementById:()=>stubEl(), createElement:()=>stubEl(),
    addEventListener:()=>{}, querySelectorAll:()=>[], body:stubEl(),
  },
  navigator:{}, localStorage:{getItem:()=>null,setItem:()=>{}},
  console, setTimeout:()=>{}, clearTimeout:()=>{},
};
vm.createContext(sandbox);
vm.runInContext(scriptSrc, sandbox, {filename:'board.js'});
const B = sandbox.__board;
const {daysBetween, compute, isNextDue, matches, cardHTML, state} = B;

let pass=0, fail=0;
const ok=(name,cond,extra='')=>{
  if(cond){pass++;console.log('  PASS '+name);}
  else{fail++;console.log('  FAIL '+name+(extra?' — '+extra:''));}
};
const T=(over)=>Object.assign(
  {id:'t.x',thread:'sv',title:'X',status:'in_progress',
   created:'2026-09-27',updated:'2026-09-27',due:null,detail:'d',where:'w'}, over);
const runCompute=(tasks,today)=>{const byId={};tasks.forEach(t=>byId[t.id]=t);compute(byId,today);return byId;};
const THREADS={sv:{name:'Short Video',tracker:'Short Video — task tracker'}};

console.log('== daysBetween ==');
ok('same day = 0', daysBetween('2026-09-27','2026-09-27')===0);
ok('next day = 1', daysBetween('2026-09-27','2026-09-28')===1);
ok('month transition 09-30 -> 10-01 = 1', daysBetween('2026-09-30','2026-10-01')===1);
ok('month transition reverse = -1', daysBetween('2026-10-01','2026-09-30')===-1);
ok('year transition = 1', daysBetween('2025-12-31','2026-01-01')===1);
ok('leap day 2024-02-28 -> 2024-03-01 = 2', daysBetween('2024-02-28','2024-03-01')===2);
ok('30-day span', daysBetween('2026-09-27','2026-10-27')===30);

console.log('== compute: overdue & priority ==');
{
  const today='2026-09-27';
  const t1=T({id:'t1',due:'2026-09-26',status:'in_progress'});
  const byId=runCompute([t1],today);
  ok('overdue flagged', byId.t1.isOverdue===true);
  ok('overdue -> Highest(4)', byId.t1.pri.level===4);
  ok('overdue reason', /overdue/.test(byId.t1.pri.reason), byId.t1.pri.reason);
}
{
  const today='2026-09-27';
  const a=T({id:'a',due:'2026-09-26',status:'agreed'});
  const r=T({id:'r',due:'2026-09-26',status:'rejected'});
  const byId=runCompute([a,r],today);
  ok('agreed excluded from overdue', byId.a.isOverdue===false);
  ok('rejected excluded from overdue', byId.r.isOverdue===false);
}
{
  const today='2026-09-27';
  const cases=[
    ['due today',      '2026-09-27',4,/due today/],
    ['due tomorrow',   '2026-09-28',4,/due tomorrow/],
    ['d=2',            '2026-09-29',4,/due tomorrow/],
    ['d=3',            '2026-09-30',3,/within 7 days/],
    ['d=7',            '2026-10-04',3,/within 7 days/],
    ['d=8',            '2026-10-05',2,/within 14 days/],
    ['d=14',           '2026-10-11',2,/within 14 days/],
    ['d=15',           '2026-10-12',0,/no due date or dependents/],
    ['d=30',           '2026-10-27',0,/no due date or dependents/],
  ];
  cases.forEach(([name,due,lvl,rx],i)=>{
    const t=T({id:'c'+i,due}); const byId=runCompute([t],today);
    ok('priority '+name+' -> level '+lvl, byId['c'+i].pri.level===lvl,
       'got '+byId['c'+i].pri.level);
    ok('priority '+name+' reason', rx.test(byId['c'+i].pri.reason), byId['c'+i].pri.reason);
  });
}
{
  // month-transition due date: 2026-09-30 today, due 2026-10-01 -> due tomorrow
  const t=T({id:'m',due:'2026-10-01'});
  const byId=runCompute([t],'2026-09-30');
  ok('month transition: due tomorrow across boundary', byId.m.pri.level===4 && /due tomorrow/.test(byId.m.pri.reason), byId.m.pri.reason);
}
{
  const today='2026-09-27';
  // "dependents" = downstream tasks blocked BY the task (they list it in blockedBy)
  const up=T({id:'up'});
  const mid1=T({id:'mid1',due:'2026-09-30',blockedBy:[{kind:'task',id:'up'}]});
  const mid2=T({id:'mid2',due:'2026-10-20',blockedBy:[{kind:'task',id:'up'}]});
  const midT=T({id:'midT',due:'2026-09-28',status:'agreed',blockedBy:[{kind:'task',id:'up'}]});
  const byId=runCompute([up,mid1,mid2,midT],today);
  ok('blocking back-link lists all dependents', (byId.up.blocking||[]).sort().join(',')==='mid1,mid2,midT');
  ok('dependent due this week -> Highest(4)', byId.up.pri.level===4, byId.up.pri.reason);
  ok('dependent reason mentions this week', /dependent due this week/.test(byId.up.pri.reason), byId.up.pri.reason);
  ok('reason counts only non-terminal dependents', /2 dependent tasks/.test(byId.up.pri.reason), byId.up.pri.reason);
}
{
  const today='2026-09-20';
  const up2=T({id:'up2'});
  const d1=T({id:'d1',due:'2026-09-30',blockedBy:[{kind:'task',id:'up2'}]});
  const byId=runCompute([up2,d1],today);
  ok('dependent due this month (not week) -> Higher(2)', byId.up2.pri.level===2, byId.up2.pri.reason);
}
{
  const today='2026-09-27';
  const dep=T({id:'dep',due:'2026-09-30'});
  const main2=T({id:'main2'});
  const byId=runCompute([dep,main2],today); // no blockedBy link -> no deps
  ok('no dependents -> Low(0)', byId.main2.pri.level===0);
}
{
  const today='2026-09-27';
  const r1=T({id:'r1',updated:'2026-09-20'}); // 7 days ago
  const r2=T({id:'r2',updated:'2026-09-19'}); // 8 days ago
  const r3=T({id:'r3',updated:'2026-09-27'}); // today
  const byId=runCompute([r1,r2,r3],today);
  ok('updated 7d ago = recent', byId.r1.recentlyUpdated===true);
  ok('updated 8d ago = not recent', byId.r2.recentlyUpdated===false);
  ok('updated today = recent', byId.r3.recentlyUpdated===true);
}

console.log('== isNextDue boundaries ==');
{
  const today='2026-09-27';
  const nd=(t,n)=>isNextDue(t,today,n);
  ok('due today in 7d window', nd(T({due:'2026-09-27'}),7)===true);
  ok('d=7 in 7d window', nd(T({due:'2026-10-04'}),7)===true);
  ok('d=7 NOT in 6d window', nd(T({due:'2026-10-04'}),6)===false);
  ok('d=14 in 14d window', nd(T({due:'2026-10-11'}),14)===true);
  ok('d=15 NOT in 14d window', nd(T({due:'2026-10-12'}),14)===false);
  ok('d=30 in 30d window', nd(T({due:'2026-10-27'}),30)===true);
  ok('d=31 NOT in 30d window', nd(T({due:'2026-10-28'}),30)===false);
  ok('overdue (d=-1) excluded', nd(T({due:'2026-09-26'}),30)===false);
  ok('agreed with due date excluded', nd(T({due:'2026-09-28',status:'agreed'}),30)===false);
  ok('rejected with due date excluded', nd(T({due:'2026-09-28',status:'rejected'}),30)===false);
  ok('pending_review undated included', nd(T({status:'pending_review'}),14)===true);
  ok('pending_me undated included', nd(T({status:'pending_me'}),14)===true);
  ok('todo unblocked included', nd(T({status:'todo'}),14)===true);
  ok('todo blocked excluded', nd(T({status:'todo',blockedBy:[{kind:'task',id:'x'}]}),14)===false);
  ok('in_progress undated excluded', nd(T({status:'in_progress'}),14)===false);
  ok('blocked undated excluded', nd(T({status:'blocked'}),14)===false);
  ok('parked undated excluded', nd(T({status:'parked'}),14)===false);
}

console.log('== matches filters ==');
{
  const today='2026-09-27';
  const od=T({id:'od',due:'2026-09-20',status:'in_progress'});
  const fut=T({id:'fut',due:'2026-10-05',status:'in_progress'});
  const okd=T({id:'okd',due:'2026-09-20',status:'agreed'});
  runCompute([od,fut,okd],today);
  state.q=''; state.thread=''; state.nDays=14;
  state.status='overdue';
  ok('overdue filter keeps overdue', matches(od,today)===true);
  ok('overdue filter drops future-dated', matches(fut,today)===false);
  ok('overdue filter drops terminal', matches(okd,today)===false);
  state.status='next_dues';
  ok('next_dues keeps future-dated in window', matches(fut,today)===true);
  ok('next_dues drops overdue', matches(od,today)===false);
  state.status='';
}

console.log('== cardHTML date lines ==');
{
  const today='2026-09-27';
  const undated=T({id:'u1'}); runCompute([undated],today);
  state.byId={u1:undated}; state.showDates=false;
  const h1=cardHTML(undated,THREADS,today);
  ok('undated card shows "No due date"', />No due date</.test(h1));
  const dated=T({id:'d1',due:'2026-09-28'}); runCompute([dated],today);
  state.byId={d1:dated};
  const h2=cardHTML(dated,THREADS,today);
  ok('dated card shows Due line', /Due <b>2026-09-28<\/b>/.test(h2));
  ok('dated card has no "No due date"', !/No due date/.test(h2));
  state.showDates=true;
  const nod=T({id:'n1',created:null,updated:null}); runCompute([nod],today);
  state.byId={n1:nod};
  const h3=cardHTML(nod,THREADS,today);
  ok('null created/updated render as unrecorded', /Created unrecorded · Updated unrecorded/.test(h3));
  state.showDates=false;
}

console.log('\nRESULT: '+pass+' passed, '+fail+' failed');
process.exit(fail?1:0);
