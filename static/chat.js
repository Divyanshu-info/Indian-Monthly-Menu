// ---------- AI Chat widget (EN + HI) — shared across pages ----------
(function () {
  const messages = []; // {role, content}

  // ISO week helper (matches app.js) for grounding the chat on the current week.
  function isoWeek(dt) {
    const d = new Date(Date.UTC(dt.getFullYear(), dt.getMonth(), dt.getDate()));
    const dayNum = (d.getUTCDay() + 6) % 7;
    d.setUTCDate(d.getUTCDate() - dayNum + 3);
    const firstThursday = new Date(Date.UTC(d.getUTCFullYear(), 0, 4));
    const week = 1 + Math.round(((d - firstThursday) / 86400000 - 3 + ((firstThursday.getUTCDay() + 6) % 7)) / 7);
    return { week, year: d.getUTCFullYear() };
  }

  // ---- inject styles ----
  const css = `
  #chatFab{position:fixed;right:20px;bottom:20px;z-index:70;width:56px;height:56px;border-radius:9999px;
    background:var(--accent,#F97316);color:#fff;border:none;box-shadow:0 6px 20px rgba(0,0,0,.25);
    display:flex;align-items:center;justify-content:center;cursor:pointer;}
  #chatFab:hover{opacity:.92;}
  #chatPanel{position:fixed;right:20px;bottom:88px;z-index:70;width:min(380px,calc(100vw - 40px));
    height:min(560px,calc(100vh - 130px));background:var(--surface,#fff);color:var(--text,#000);
    border:1px solid var(--border,#ddd);border-radius:16px;box-shadow:0 12px 40px rgba(0,0,0,.3);
    display:none;flex-direction:column;overflow:hidden;}
  #chatPanel.open{display:flex;}
  #chatHead{padding:12px 14px;background:var(--panel,#FEF3C7);border-bottom:1px solid var(--border,#ddd);
    display:flex;align-items:center;gap:8px;font-weight:700;}
  #chatMsgs{flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:10px;}
  .cmsg{max-width:85%;padding:8px 11px;border-radius:12px;font-size:14px;line-height:1.4;white-space:pre-wrap;word-wrap:break-word;}
  .cmsg.user{align-self:flex-end;background:var(--accent,#F97316);color:#fff;border-bottom-right-radius:3px;}
  .cmsg.bot{align-self:flex-start;background:var(--panel,#f3f3f3);color:var(--text,#000);border-bottom-left-radius:3px;}
  #chatForm{display:flex;gap:6px;padding:10px;border-top:1px solid var(--border,#ddd);}
  #chatInput{flex:1;padding:9px 11px;border-radius:10px;border:1px solid var(--border,#ddd);
    background:var(--bg,#fff);color:var(--text,#000);outline:none;font-size:14px;}
  #chatSend{padding:0 14px;border-radius:10px;border:none;background:var(--accent,#F97316);color:#fff;cursor:pointer;}
  #chatSend:disabled{opacity:.5;cursor:not-allowed;}
  .chat-hint{font-size:12px;color:var(--muted,#777);padding:0 12px 8px;}
  `;
  const style = document.createElement('style');
  style.textContent = css;
  document.head.appendChild(style);

  // ---- inject markup ----
  const wrap = document.createElement('div');
  wrap.innerHTML = `
    <button id="chatFab" aria-label="Open recipe assistant" title="Recipe Assistant">
      <i data-lucide="message-circle" class="w-6 h-6" aria-hidden="true"></i>
    </button>
    <div id="chatPanel" role="dialog" aria-modal="false" aria-labelledby="chatTitle">
      <div id="chatHead">
        <i data-lucide="sparkles" class="w-5 h-5" aria-hidden="true"></i>
        <span id="chatTitle">Recipe Assistant</span>
        <button id="chatClose" aria-label="Close chat" style="margin-left:auto;background:none;border:none;cursor:pointer;color:inherit;">
          <i data-lucide="x" class="w-5 h-5" aria-hidden="true"></i></button>
      </div>
      <div id="chatMsgs" aria-live="polite"></div>
      <p class="chat-hint">Ask about recipes, ingredients or your shopping list — in English or हिंदी.</p>
      <form id="chatForm">
        <input id="chatInput" autocomplete="off" placeholder="Type your question…" aria-label="Message">
        <button id="chatSend" type="submit" aria-label="Send"><i data-lucide="send" class="w-4 h-4" aria-hidden="true"></i></button>
      </form>
    </div>`;
  document.body.appendChild(wrap);
  if (window.lucide) lucide.createIcons();

  const $ = (id) => document.getElementById(id);
  const panel = $('chatPanel');
  let greeted = false;

  function addMsg(role, text) {
    const el = document.createElement('div');
    el.className = `cmsg ${role === 'user' ? 'user' : 'bot'}`;
    el.textContent = text;
    $('chatMsgs').appendChild(el);
    $('chatMsgs').scrollTop = $('chatMsgs').scrollHeight;
    return el;
  }

  function togglePanel(open) {
    panel.classList.toggle('open', open);
    if (open) {
      if (!greeted) {
        addMsg('bot', 'Namaste! 🍛 Ask me about any recipe, ingredient substitutions, or your weekly shopping list. आप हिंदी में भी पूछ सकते हैं।');
        greeted = true;
      }
      $('chatInput').focus();
    }
  }

  $('chatFab').onclick = () => togglePanel(!panel.classList.contains('open'));
  $('chatClose').onclick = () => togglePanel(false);

  async function send(text) {
    addMsg('user', text);
    messages.push({ role: 'user', content: text });
    $('chatSend').disabled = true;
    const botEl = addMsg('bot', '…');
    let acc = '';
    const { week, year } = isoWeek(new Date());
    try {
      const resp = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages, year, week }),
      });
      if (!resp.ok || !resp.body) throw new Error('Chat request failed');
      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split('\n\n');
        buffer = events.pop() || '';
        for (const ev of events) {
          if (ev.startsWith('event: done')) continue;
          const line = ev.split('\n').find(l => l.startsWith('data: '));
          if (!line) continue;
          const chunk = line.slice(6).replace(/\\n/g, '\n');
          acc += chunk;
          botEl.textContent = acc;
          $('chatMsgs').scrollTop = $('chatMsgs').scrollHeight;
        }
      }
      if (!acc) acc = '(no response)';
      botEl.textContent = acc;
      messages.push({ role: 'assistant', content: acc });
    } catch (e) {
      botEl.textContent = '⚠️ Could not reach the assistant. Please try again.';
    } finally {
      $('chatSend').disabled = false;
      $('chatInput').focus();
    }
  }

  $('chatForm').addEventListener('submit', (e) => {
    e.preventDefault();
    const text = $('chatInput').value.trim();
    if (!text) return;
    $('chatInput').value = '';
    send(text);
  });
})();
