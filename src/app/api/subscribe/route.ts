import { NextRequest, NextResponse } from 'next/server';
import { createServiceClient } from '@/lib/supabase';

export async function POST(request: NextRequest) {
  const { email } = await request.json();

  if (!email || typeof email !== 'string' || !email.includes('@')) {
    return NextResponse.json({ error: 'Valid email required' }, { status: 400 });
  }

  const normalized = email.trim().toLowerCase();
  const supabase = createServiceClient();
  if (!supabase) {
    return NextResponse.json({ error: 'Service unavailable' }, { status: 503 });
  }

  // Upsert: if they previously unsubscribed, reactivate
  const { error } = await supabase
    .from('subscribers')
    .upsert(
      { email: normalized, active: true, unsubscribed_at: null },
      { onConflict: 'email' }
    );

  if (error) {
    if (error.code === '23505') {
      // Already subscribed, that's fine
      return NextResponse.json({ message: 'Already subscribed' });
    }
    console.error('Subscribe error:', error);
    return NextResponse.json({ error: 'Failed to subscribe' }, { status: 500 });
  }

  return NextResponse.json({ message: 'Subscribed' });
}
