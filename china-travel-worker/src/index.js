/**
 * china-travel-counter - Cloudflare Worker
 */
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;

    // 301 redirects (v1.7 navigation restructure)
    const REDIRECTS = {
      '/guides/payment.html': '/guides/before-you-go.html',
      '/guides/transportation.html': '/guides/getting-around.html',
      '/guides/stay.html': '/guides/getting-around.html',
    };
    if (REDIRECTS[path]) {
      return Response.redirect(url.origin + REDIRECTS[path], 301);
    }

    if (path === '/api/top-pages') {
      const data = await env.PAGE_VIEWS.get('top3', 'json') || [];
      return new Response(JSON.stringify(data), {
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      });
    }

    if (path.startsWith('/articles/') && path.endsWith('.html')) {
      ctx.waitUntil((async () => {
        await countAndUpdate(path, env);
      })().catch(e => console.error('COUNT ERR:', e.message)));
      return fetch(request);
    }

    return fetch(request);
  }
};

async function countAndUpdate(path, env) {
  const today = new Date().toISOString().split('T')[0];
  const dailyKey = `daily:${path}:${today}`;
  const current = parseInt(await env.PAGE_VIEWS.get(dailyKey) || '0');
  await env.PAGE_VIEWS.put(dailyKey, String(current + 1));
  await updateTop3(env);
}

async function updateTop3(env) {
  const today = new Date();
  const dates = [];
  for (let i = 0; i < 7; i++) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    dates.push(d.toISOString().split('T')[0]);
  }

  const knownPaths = new Set();
  const list = await env.PAGE_VIEWS.list({ prefix: 'daily:' });
  for (const key of list.keys) {
    const parts = key.name.split(':');
    if (parts.length >= 3) knownPaths.add(parts[1]);
  }

  let urlMap = {};
  try { urlMap = await env.PAGE_VIEWS.get('url_map', 'json') || {}; } catch(e) {}

  const totals = [];
  for (const articlePath of knownPaths) {
    let sum = 0;
    for (const date of dates) {
      sum += parseInt(await env.PAGE_VIEWS.get(`daily:${articlePath}:${date}`) || '0');
    }
    if (sum > 0) {
      const folder = articlePath.replace('/articles/', '').replace('/en.html', '');
      const info = urlMap[folder] || {};
      totals.push({
        path: articlePath,
        count: sum,
        title: info.title || folder.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
        guide_url: info.guide_url || ''
      });
    }
  }

  totals.sort((a, b) => b.count - a.count);
  await env.PAGE_VIEWS.put('top3', JSON.stringify(totals.slice(0, 10)));
}
