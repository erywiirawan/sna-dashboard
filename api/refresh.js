// Vercel Serverless Function: Proxy to trigger GitHub Action for data refresh
// Token is stored securely in Vercel environment variables (GH_TOKEN)

const GH_REPO = 'erywiirawan/sna-dashboard';
const GH_WORKFLOW = 'refresh-data.yml';

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();

  const token = process.env.GH_TOKEN;
  if (!token) return res.status(500).json({ error: 'GH_TOKEN not configured in Vercel env' });

  const headers = {
    'Authorization': `token ${token}`,
    'Accept': 'application/vnd.github.v3+json',
    'Content-Type': 'application/json',
    'User-Agent': 'SNA-Dashboard'
  };

  // POST /api/refresh — trigger workflow
  if (req.method === 'POST') {
    try {
      const r = await fetch(`https://api.github.com/repos/${GH_REPO}/actions/workflows/${GH_WORKFLOW}/dispatches`, {
        method: 'POST', headers,
        body: JSON.stringify({ ref: 'main', inputs: { force: 'true' } })
      });
      if (r.status === 204) return res.status(200).json({ ok: true });
      return res.status(r.status).json({ error: await r.text() });
    } catch (e) { return res.status(500).json({ error: e.message }); }
  }

  // GET /api/refresh — check latest run status
  if (req.method === 'GET') {
    try {
      const r = await fetch(`https://api.github.com/repos/${GH_REPO}/actions/workflows/${GH_WORKFLOW}/runs?per_page=1`, { headers });
      const d = await r.json();
      const run = d.workflow_runs?.[0];
      if (!run) return res.status(200).json({ status: 'no_runs' });
      return res.status(200).json({
        status: run.status, conclusion: run.conclusion,
        created_at: run.created_at, html_url: run.html_url
      });
    } catch (e) { return res.status(500).json({ error: e.message }); }
  }

  return res.status(405).json({ error: 'Method not allowed' });
}
