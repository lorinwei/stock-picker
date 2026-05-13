import{d as y,c as l,a as s,F as v,r as _,w as C,v as A,k as I,h as u,l as M,f as c,t as h,n as f,j as x,_ as T}from"./index-DmI0iGmE.js";const w={class:"page chat-view"},E={class:"quick-questions fade-in fade-in-2"},V=["onClick"],B={class:"msg-avatar"},D={key:0,class:"ai-label"},H=["innerHTML"],L={class:"chat-input-bar"},R=["disabled"],S=y({__name:"ChatView",setup($){const o=u(),n=u(""),m=["大盘今天怎么样？","推荐几只股票","看看我的持仓","茅台还能买吗"],r=u([{role:"ai",content:`您好！我是StockMind AI，您的智能炒股助手。

我可以帮您：
📊 分析个股走势
🧠 诊断持仓风险
💡 推荐优质股票
📈 解读大盘行情

有什么想聊的？`,time:""}]),b=e=>e.replace(/\n/g,"<br>").replace(/✅/g,'<span style="color:var(--success)">✅</span>').replace(/⚠️/g,'<span style="color:var(--accent)">⚠️</span>').replace(/🔴/g,'<span style="color:var(--danger)">🔴</span>').replace(/\*\*(.*?)\*\*/g,"<strong>$1</strong>"),d=()=>{M(()=>{o.value&&(o.value.scrollTop=o.value.scrollHeight)})},i=()=>{const e=n.value.trim();e&&(r.value.push({role:"user",content:e,time:""}),n.value="",d(),setTimeout(()=>{const a=g(e);r.value.push({role:"ai",content:a,time:""}),d()},800))},k=e=>{n.value=e,i()},g=e=>e.includes("大盘")||e.includes("今天怎么样")?`📊 **今日大盘分析**

沪深300当前 **3820.5**，上涨 **+0.82%** ↑
创业板指 **1568.3**，上涨 **+1.15%** ↑

✅ **市场状态：多头格局**
- 三大指数均在20日均线上方
- 成交量温和放大
- 北向资金今日净买入 **+32亿**

💡 **操作建议**：可适度加仓，但避免追高。关注新能源、白酒板块机会。`:e.includes("推荐")?`🚀 **今日AI推荐**

**贵州茅台 600519** ⭐评分92
- 买入区间：¥1840~1880
- 目标价：¥1980
- 止损价：¥1757
- AI理由：北向资金连续3日净买入，MACD金叉，ROE维持25%

**宁德时代 300750** ⭐评分88
- 买入区间：¥320~330
- 目标价：¥350
- 止损价：¥305
- AI理由：新能源政策利好，量价齐升，机构加仓`:e.includes("持仓")?`💼 **您的持仓状态**

✅ **比亚迪** 002594
浮盈 **+¥1,360** (+2.85%) 状态正常
建议持有，突破¥250考虑止盈

⚠️ **宁德时代** 300750
浮亏 **-¥3,810** (-6.41%) 接近止损
建议减仓50%，等待反弹确认

⚠️ **贵州茅台** 600519
浮盈 **+¥5,000** (+1.39%) 状态正常
建议持有，目标¥1950`:e.includes("茅台")||e.includes("600519")?`🏥 **贵州茅台 600519 诊断**

✅ **基本面**：业绩稳定，ROE 25%，毛利率维持80%以上，现金流健康
✅ **资金面**：北向资金连续3日净买入，共计 **+2.8亿**
✅ **技术面**：MACD金叉，20日均线支撑有效
⚠️ **估值面**：PE 32，处于历史中位偏上
⚠️ **风险点**：白酒消费数据近期偏弱

💡 **建议**：可轻仓（10%），首仓5%，回踩确认再加。止损设¥1750，目标¥1950。`:`收到您的问题：${e}

我正在分析，请稍候... 或者换个问法试试？

例如：「大盘怎么样」「推荐股票」「看看持仓」`;return(e,a)=>(c(),l("div",w,[a[1]||(a[1]=s("div",{class:"page-title fade-in fade-in-1"},"💬 AI智能问答",-1)),s("div",E,[(c(),l(v,null,_(m,t=>s("button",{key:t,class:"quick-btn",onClick:p=>k(t)},h(t),9,V)),64))]),s("div",{class:"chat-history",ref_key:"chatEl",ref:o},[(c(!0),l(v,null,_(r.value,(t,p)=>(c(),l("div",{key:p,class:f(["chat-msg",t.role])},[s("div",B,h(t.role==="ai"?"🤖":"👤"),1),s("div",{class:f(["msg-bubble card",t.role==="ai"?"ai-bubble":"user-bubble"])},[t.role==="ai"?(c(),l("div",D,"StockMind AI")):x("",!0),s("div",{class:"msg-content",innerHTML:b(t.content)},null,8,H)],2)],2))),128))],512),s("div",L,[C(s("input",{"onUpdate:modelValue":a[0]||(a[0]=t=>n.value=t),class:"chat-input",placeholder:"问股票、问大盘、问持仓...",onKeyup:I(i,["enter"])},null,544),[[A,n.value]]),s("button",{class:"send-btn",onClick:i,disabled:!n.value.trim()}," ➤ ",8,R)])]))}}),K=T(S,[["__scopeId","data-v-41439643"]]);export{K as default};
