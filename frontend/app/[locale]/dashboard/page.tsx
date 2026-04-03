'use client';

import { useEffect, useRef, useState } from 'react';
import { useTranslations } from 'next-intl';
import { useOnboarding } from '@/context/OnboardingContext';

interface Slot {
  date: string;
  time: string;
}

interface ClinicCard {
  clinic_name: string;
  address: string;
  slots: Slot[];
}

export default function DashboardPage({ params: { locale } }: { params: { locale: string } }) {
  const t = useTranslations('dashboard');
  const { postalCode } = useOnboarding();

  const [clinics, setClinics] = useState<ClinicCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [connError, setConnError] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  const prevSlotKeysRef = useRef<Set<string>>(new Set());
  const sessionIdRef = useRef<string | null>(null);
  const esRef = useRef<EventSource | null>(null);

  function buildSlotKey(clinicName: string, slot: Slot) {
    return `${clinicName}|${slot.date}|${slot.time}`;
  }

  function showToast(msg: string) {
    setToast(msg);
    setTimeout(() => setToast(null), 4000);
  }

  function detectNewSlots(next: ClinicCard[]) {
    const nextKeys = new Set(next.flatMap(c => c.slots.map(s => buildSlotKey(c.clinic_name, s))));
    const prev = prevSlotKeysRef.current;
    const hasNew = prev.size > 0 && Array.from(nextKeys).some(k => !prev.has(k));
    prevSlotKeysRef.current = nextKeys;
    if (hasNew) showToast(t('new_slot'));
  }

  useEffect(() => {
    let cancelled = false;

    async function startSession() {
      try {
        const res = await fetch('/api/sessions', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            postal_code: postalCode || 'H9K 1P9',
            service_type: 'Consultation urgente',
          }),
        });
        if (!res.ok || cancelled) return;
        const { session_id } = await res.json();
        sessionIdRef.current = session_id;

        const es = new EventSource(`/api/sessions/${session_id}/stream`);
        esRef.current = es;

        es.addEventListener('clinics', (e: MessageEvent) => {
          if (cancelled) return;
          try {
            const payload = JSON.parse(e.data);
            if (Array.isArray(payload.data)) {
              detectNewSlots(payload.data);
              setClinics(payload.data);
              setLoading(false);
              setConnError(false);
            }
          } catch {}
        });

        es.addEventListener('error', () => {
          if (!cancelled) setConnError(true);
        });

        es.onerror = () => {
          if (!cancelled) setConnError(true);
        };
      } catch {
        if (!cancelled) {
          setLoading(false);
          setConnError(true);
        }
      }
    }

    startSession();

    return () => {
      cancelled = true;
      esRef.current?.close();
      if (sessionIdRef.current) {
        fetch(`/api/sessions/${sessionIdRef.current}`, { method: 'DELETE' }).catch(() => {});
      }
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <main className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">{t('title')}</h1>

        {/* Toast */}
        {toast && (
          <div
            role="status"
            aria-live="polite"
            className="fixed top-4 right-4 bg-green-600 text-white px-4 py-3 rounded-xl shadow-lg text-sm font-medium z-50"
          >
            {toast}
          </div>
        )}

        {/* Connection error */}
        {connError && (
          <div role="alert" className="bg-yellow-50 border border-yellow-200 text-yellow-800 rounded-xl px-4 py-3 mb-4 text-sm">
            {t('connection_lost')}
          </div>
        )}

        {/* Loading */}
        {loading && !connError && (
          <div className="flex flex-col items-center gap-3 py-16 text-gray-500">
            <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" aria-hidden="true" />
            <p>{t('loading')}</p>
          </div>
        )}

        {/* No results */}
        {!loading && clinics.length === 0 && !connError && (
          <p className="text-center text-gray-500 py-12">{t('no_results')}</p>
        )}

        {/* Clinic cards */}
        <div className="flex flex-col gap-4">
          {clinics.map((clinic, ci) => (
            <div key={ci} className="bg-white rounded-2xl shadow p-5">
              <h2 className="text-lg font-semibold">{clinic.clinic_name}</h2>
              <p className="text-sm text-gray-500 mt-1">{clinic.address}</p>
              <p className="text-sm font-medium mt-3 mb-2">
                {clinic.slots.length} {t('slots_count')}
              </p>
              <div className="flex flex-wrap gap-2">
                {clinic.slots.map((slot, si) => (
                  <div key={si} className="flex items-center gap-2 bg-blue-50 rounded-lg px-3 py-2">
                    <span className="text-sm text-blue-800 font-medium">
                      {slot.date} · {slot.time}
                    </span>
                    <button
                      type="button"
                      disabled
                      title={t('book_soon')}
                      aria-label={`${t('book')} — ${slot.date} ${slot.time} — ${clinic.clinic_name}`}
                      className="text-xs bg-blue-600 text-white rounded-lg px-3 py-1 disabled:opacity-40 cursor-not-allowed focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-1"
                    >
                      {t('book')}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
