// Vercel Serverless Function: Manual refresh trigger
// Writes a flag file to GitHub, picked up by Hermes cron job within 5 min

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  if (req.method === 'OPTIONS') return res.status(200).end();

  // GET: status check
  if (req.method === 'GET') {
    return res.status(200).json({
      ok: true,
      status: 'ready',
      message: 'Data di-refresh otomatis setiap hari jam 06:00 WIB.',
      nextRefresh: '06:00 WIB'
    });
  }

  // POST: manual refresh trigger via Hermes cron
  if (req.method === 'POST') {
    const HERMES_URL = process.env.HERMES_URL;
    const HERMES_KEY = process.env.HERMES_KEY;
    
    if (HERMES_URL && HERMES_KEY) {
      try {
        const r = await fetch(HERMES_URL, {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${HERMES_KEY}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: 'run', job_id: '3438baacd2b7' }),
          signal: AbortSignal.timeout(10000)
        });
        if (r.ok) {
          return res.status(200).json({ ok: true, message: 'Refresh triggered! Dashboard akan update ~3 menit.' });
        }
      } catch (e) {}
    }
    
    return res.status(200).json({
      ok: true,
      message: 'Refresh terjadwal: setiap hari jam 06:00 WIB. Untuk refresh manual, hubungi admin.',
      scheduled: true
    });
  }

  return res.status(405).json({ error: 'Method not allowed' });
}
