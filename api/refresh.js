// Vercel Serverless Function: Trigger data refresh on VPS
export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Authorization, Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();

  // GET: status check
  if (req.method === 'GET') {
    return res.status(200).json({
      ok: true,
      status: 'ready',
      message: 'Klik Refresh Data untuk update data dari Google Sheets.',
    });
  }

  // POST: trigger refresh via VPS webhook
  if (req.method === 'POST') {
    const WEBHOOK_URL = process.env.WEBHOOK_URL || 'http://43.134.103.128:20128/sna-refresh';
    const WEBHOOK_KEY = process.env.WEBHOOK_KEY || 'sna-refresh-2026';

    try {
      const r = await fetch(WEBHOOK_URL, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${WEBHOOK_KEY}`,
          'Content-Type': 'application/json',
        },
        signal: AbortSignal.timeout(15000),
      });

      const data = await r.json();

      if (r.ok && data.ok) {
        return res.status(200).json({
          ok: true,
          message: 'Refresh dimulai! Data akan update dalam ~2 menit. Halaman akan otomatis refresh.',
        });
      }

      return res.status(r.status).json({
        ok: false,
        message: data.error || 'Refresh gagal',
      });
    } catch (e) {
      return res.status(502).json({
        ok: false,
        message: 'Gagal menghubungi server refresh: ' + e.message,
      });
    }
  }

  return res.status(405).json({ error: 'Method not allowed' });
}
