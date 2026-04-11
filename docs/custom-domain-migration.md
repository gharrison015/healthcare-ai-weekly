# Custom Domain Migration — healthcareaibrief.com

**Status:** 2026-04-10 — domain purchased, ready to point at Vercel.

## Goal

Serve `https://healthcareaibrief.com` as the primary URL for the site while keeping `https://healthcare-ai-weekly.vercel.app` alive as a 308 redirect, so existing bookmarks and past email `?issue=YYYY-MM-DD` deep links continue to work with zero disruption.

## Why no disruption

- Vercel's default behavior when you add a custom domain: **both URLs serve the same site**.
- When you mark the custom domain as "primary" in the Vercel dashboard, the `.vercel.app` subdomain starts returning HTTP 308 redirects to the custom domain.
- Existing URLs like `https://healthcare-ai-weekly.vercel.app/?issue=2026-04-10` redirect to `https://healthcareaibrief.com/?issue=2026-04-10` — **query params and paths are preserved**.
- Search engines treat 308 as permanent and transfer rankings.
- TLS certificates are auto-provisioned by Vercel (via Let's Encrypt) once DNS is verified.

## Step-by-step

### 1. Add the domain in Vercel

1. Open https://vercel.com/gharrison015s-projects/healthcare-ai-weekly/settings/domains
2. Click **Add Domain**
3. Type `healthcareaibrief.com` and click Add
4. Vercel will also offer to add `www.healthcareaibrief.com` — add it too (both root and www should resolve)
5. Vercel will show you the DNS records you need to configure at your registrar

You'll see something like:

| Type | Name | Value |
|---|---|---|
| `A` | `@` (root) | `76.76.21.21` |
| `CNAME` | `www` | `cname.vercel-dns.com` |

(Exact values will be shown in the Vercel UI — use whatever Vercel tells you, not what's written here.)

### 2. Set the DNS records at your registrar

Where did you buy the domain? Common ones:

**Porkbun / Namecheap / Cloudflare Registrar / Squarespace / GoDaddy**
1. Log into the registrar dashboard
2. Find the DNS settings for `healthcareaibrief.com`
3. If there are any existing records pointing elsewhere (parked page, holding page), DELETE them
4. Add the records exactly as Vercel specified

**If the domain is at Cloudflare:** set the proxy to "DNS only" (grey cloud), not "proxied" (orange cloud). Vercel needs to see the real traffic to provision TLS and handle routing.

### 3. Wait for DNS propagation

- Usually 1–10 minutes
- Can take up to 24 hours in worst case
- You can watch progress in the Vercel dashboard — the domain will show a loading state, then "Valid Configuration" with a green check

### 4. Set `healthcareaibrief.com` as the "Primary Domain"

In Vercel:
1. Go back to the Domains settings
2. Next to `healthcareaibrief.com`, open the "..." menu
3. Click **Set as Primary Domain**
4. This makes the `.vercel.app` subdomain start returning 308 redirects to the custom domain

### 5. Verify

Once Vercel shows "Valid Configuration":

```bash
curl -sIL https://healthcareaibrief.com/ | grep -iE "^(HTTP|location)"
# Expect: HTTP/2 200

curl -sIL https://healthcare-ai-weekly.vercel.app/ | grep -iE "^(HTTP|location)"
# Expect: HTTP/2 308 followed by location: https://healthcareaibrief.com/

curl -sIL "https://healthcare-ai-weekly.vercel.app/?issue=2026-04-10" | grep -iE "^(HTTP|location)"
# Expect: 308 with location preserving the ?issue=2026-04-10 param
```

All three should succeed.

### 6. Confirm the site still works

- Open https://healthcareaibrief.com/
- Click the "Let's Talk AI" CTA — should open mailto
- Search for something via the inline hero search
- Click an issue card — should highlight
- Open https://healthcare-ai-weekly.vercel.app/ in an incognito window — should auto-redirect to the new domain with the path preserved

## Already updated in this commit

- `pipeline/generator/email_generator.py` — `LANDING_PAGE_URL` now points to `https://healthcareaibrief.com`, so **next Friday's newsletter email will use the new domain** for all its issue deep links. Links in already-sent emails continue to work via the 308 redirect.
- `src/app/layout.tsx` — `metadataBase` set to `https://healthcareaibrief.com` plus `openGraph` block, so social previews and canonical URLs point to the new domain
- `PROJECT_MAP.md`, `pipeline/HANDOFF.md`, `docs/PRD.md` — documentation updated to reference both URLs
- Memory updated

## Friday newsletter trigger — one more thing

The cloud trigger at https://claude.ai/code/scheduled/trig_01JqnHVGb3gfV1judxMohq12 has its own prompt that the cloud agent executes. **If that prompt hardcodes a URL anywhere**, it needs to be updated via `RemoteTrigger` API. I should audit it once the domain is live — add to the "verify Monday" checklist.

## What to tell existing subscribers (optional)

If you want to be proactive with the couple of people already using the `.vercel.app` URL:

> Heads up — the newsletter has a proper home now at **healthcareaibrief.com**. Your existing bookmarks and any links in past emails keep working (they redirect automatically), so there's nothing you need to do. Just wanted to flag the new URL in case you want to share it with anyone.

Or say nothing — the redirect is transparent.
