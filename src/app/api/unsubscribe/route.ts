import { NextRequest, NextResponse } from 'next/server';
import { createServiceClient } from '@/lib/supabase';

export async function GET(request: NextRequest) {
  const token = request.nextUrl.searchParams.get('token');

  if (!token) {
    return new NextResponse('Missing unsubscribe token', { status: 400 });
  }

  const supabase = createServiceClient();
  if (!supabase) {
    return new NextResponse('Service unavailable', { status: 503 });
  }

  const { data, error } = await supabase
    .from('subscribers')
    .update({ active: false, unsubscribed_at: new Date().toISOString() })
    .eq('unsubscribe_token', token)
    .select('email');

  if (error || !data?.length) {
    return new NextResponse(unsubPage('Invalid or expired unsubscribe link.', false), {
      headers: { 'Content-Type': 'text/html' },
    });
  }

  return new NextResponse(unsubPage(`${data[0].email} has been unsubscribed.`, true), {
    headers: { 'Content-Type': 'text/html' },
  });
}

function unsubPage(message: string, success: boolean) {
  return `<!DOCTYPE html>
<html><head><title>Unsubscribe</title>
<style>body{font-family:Aptos,Calibri,-apple-system,sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;background:#f8fafc;color:#1e293b;}
.card{text-align:center;padding:48px;border-radius:16px;background:white;box-shadow:0 4px 24px rgba(0,0,0,0.08);max-width:420px;}
h1{font-size:24px;margin:0 0 12px;}
p{font-size:16px;color:#64748b;margin:0 0 24px;}
a{color:#2563eb;text-decoration:none;font-weight:600;}</style></head>
<body><div class="card">
<h1>${success ? 'Unsubscribed' : 'Error'}</h1>
<p>${message}</p>
<a href="https://healthcareaibrief.com">Back to Healthcare AI Weekly</a>
</div></body></html>`;
}
