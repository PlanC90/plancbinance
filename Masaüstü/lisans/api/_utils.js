'use strict'

const crypto = require('crypto')

function json(body, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

function generateLicenseKey() {
  // Format: PlanC.Space-XXXXXXXX-XXXXXXXX-XXXXXX (random hex upper)
  const seg = (n) => crypto.randomBytes(n).toString('hex').slice(0, n * 2).toUpperCase()
  return `PlanC.Space-${seg(4)}-${seg(4)}-${seg(3)}`
}

async function sbUpdateLicense({ id, license_key, status }) {
  const url = new URL(`${process.env.SUPABASE_URL}/rest/v1/license_forms`)
  url.searchParams.set('id', `eq.${id}`)
  const r = await fetch(url, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'apikey': process.env.SUPABASE_SERVICE_ROLE_KEY,
      'Authorization': `Bearer ${process.env.SUPABASE_SERVICE_ROLE_KEY}`,
      'Prefer': 'return=representation'
    },
    body: JSON.stringify({ license_key, status })
  })
  if (!r.ok) throw new Error('supabase_update_failed')
  return r.json()
}

module.exports = { json, generateLicenseKey, sbUpdateLicense }






