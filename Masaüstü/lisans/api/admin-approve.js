'use strict'

const { json, generateLicenseKey } = require('./_utils')
const nodemailer = require('nodemailer')

module.exports = async (req) => {
  if (req.method !== 'POST') return json({ error: 'method' }, 405)
  if (!process.env.ADMIN_PASSWORD) return json({ error: 'server_env' }, 500)

  const body = await req.json()
  const { password, id, email } = body || {}
  if (password !== process.env.ADMIN_PASSWORD) return json({ error: 'unauthorized' }, 401)
  if (!id || !email) return json({ error: 'bad_request' }, 400)

  // Generate license key (no DB write)
  const license = generateLicenseKey()

  // Send email via Yandex SMTP
  const transporter = nodemailer.createTransport({
    host: process.env.EMAIL_SMTP_HOST || 'smtp.yandex.com',
    port: Number(process.env.EMAIL_SMTP_PORT || 465),
    secure: true,
    auth: {
      user: process.env.EMAIL_SMTP_USER || 'license@planc.space',
      pass: process.env.EMAIL_SMTP_PASS,
    },
  })

  const html = `
  <div style="font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;background:#0b1220;color:#e5e7eb;padding:24px">
    <div style="max-width:560px;margin:0 auto;background:linear-gradient(180deg,rgba(255,255,255,0.06),rgba(255,255,255,0.02));border:1px solid rgba(255,255,255,0.1);border-radius:16px;padding:24px">
      <h2 style="margin:0 0 12px 0;color:#fff">PlanC License</h2>
      <p style="margin:0 0 16px 0;color:#cbd5e1">Ödemeniz onaylandı. Lisans anahtarınız aşağıdadır.</p>
      <div style="background:#0f172a;border:1px solid rgba(255,255,255,0.12);border-radius:12px;padding:16px;margin-bottom:16px">
        <div style="font-size:12px;color:#94a3b8;margin-bottom:6px">License Key</div>
        <div style="font-family:ui-monospace,Menlo,Consolas,monospace;color:#93c5fd;font-size:14px">${license}</div>
      </div>
      <div style="font-size:12px;color:#94a3b8">Bu anahtarı güvenli bir yerde saklayın. Paylaşmayın.</div>
    </div>
    <div style="max-width:560px;margin:12px auto 0;text-align:center;color:#64748b;font-size:12px">© PlanC</div>
  </div>`

  await transporter.sendMail({
    from: process.env.EMAIL_FROM || 'license@planc.space',
    to: email,
    subject: 'PlanC License Key',
    text: `Your license key: ${license}`,
    html,
  })

  return json({ ok: true, license })
}


