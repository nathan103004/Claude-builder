'use client';

import { useEffect, useRef, useState } from 'react';
import { useTranslations } from 'next-intl';
import { useOnboarding } from '@/context/OnboardingContext';
import ServiceTypeSelector, { RvsqServiceType } from '@/components/dashboard/ServiceTypeSelector';
import EmergencyPrompt from '@/components/dashboard/EmergencyPrompt';
import ChatPanel from '@/components/dashboard/ChatPanel';
import BookingConfirmation from '@/components/dashboard/BookingConfirmation';

interface Slot {
  date: string;
  time: string;
  slot_id: string;
}

interface ClinicCard {
  clinic_name: string;
  address: string;
  slots: Slot[];
}

export default function DashboardPage({ params: { locale } }: { params: { locale: string } }) {
  const t = useTranslations('dashboard');
  const { postalCode, ramq } = useOnboarding();

  const [serviceType, setServiceType] = useState<RvsqServiceType>('consultation_urgente');
  const [showEmergency, setShowEmergency] = useState(false);
  const [booking, setBooking] = useState<{
    confirmationNumber: string;
    clinicName: string;
    slotDate: string;
    slotTime: string;
  } | null>(null);
  const [clinics, setClinics] = useState<ClinicCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [connError, setConnError] = useState(false);
  const [paused, setPaused] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [bookingSlotId, setBookingSlotId] = useState<string | null>(null);
  const [bookError, setBookError] = useState<string | null>(null);

  const prevSlotKeysRef = useRef<Set<string>>(new Set());
  const sessionIdRef = useRef<string | null>(null);
  const rvsqSessionIdRef = useRef<string | null>(null);
  const esRef = useRef<EventSource | null>(null);

  function buildSlotKey(clinicName: string, slot: Slot) {
    return `${clinicName}|${slot.date}|${slot.time}`;
  }

  function showToast(msg: string) {
    setToast(msg);
    setTimeout(() => setToast(null), 4000);
  }

  async function ensureRvsqSession(): Promise<string | null> {
    if (rvsqSessionIdRef.current) return rvsqSessionIdRef.current;
    if (!ramq) return null;
    const res = await fetch('/api/rvsq/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prenom: ramq.prenom,
        nom: ramq.nom,
        numero_assurance_maladie: ramq.numero,
        numero_sequentiel: ramq.sequentiel,
        date_naissance_jour: ramq.dob_day,
        date_naissance_mois: ramq.dob_month,
        date_naissance_annee: ramq.dob_year,
      }),
    });
    if (!res.ok) return null;
    const { session_id } = await res.json();
    rvsqSessionIdRef.current = session_id;
    return session_id;
  }

  async function handleBook(clinic: ClinicCard, slot: Slot) {
    setBookError(null);
    setBookingSlotId(slot.slot_id);
    try {
      const rvsqSessionId = await ensureRvsqSession();
      if (!rvsqSessionId) {
        setBookError(t('book_error_no_session'));
        return;
      }
      const res = await fetch('/api/rvsq/book', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: rvsqSessionId, slot_id: slot.slot_id }),
      });
      if (res.status === 409) {
        setBookError(t('book_error_slot_taken'));
        return;
      }
      if (res.status === 401) {
        rvsqSessionIdRef.current = null;
        setBookError(t('book_error_session_expired'));
        return;
      }
      if (!res.ok) {
        setBookError(t('book_error_failed'));
        return;
      }
      const result = await res.json();
      setBooking({
        confirmationNumber: result.confirmation_number,
        clinicName: clinic.clinic_name,
        slotDate: slot.date,
        slotTime: slot.time,
      });
    } catch {
      setBookError(t('book_error_failed'));
    } finally {
      setBookingSlotId(null);
    }
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
              setPaused(false);
              detectNewSlots(payload.data);
              setClinics(payload.data);
              setLoading(false);
              setConnError(false);
            }
          } catch {}
        });

        es.addEventListener('paused', () => {
          if (!cancelled) setPaused(true);
        });

        es.addEventListener('error', () => {
          if (!cancelled) setConnError(true);
        });
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
      if (rvsqSessionIdRef.current) {
        fetch(`/api/rvsq/session/${rvsqSessionIdRef.current}`, { method: 'DELETE' }).catch(() => {});
      }
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <main id="main-content" className="min-h-screen bg-blue-50 p-6">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">{t('title')}</h1>

        {booking ? (
          <BookingConfirmation
            confirmationNumber={booking.confirmationNumber}
            serviceType={serviceType}
            clinicName={booking.clinicName}
            slotDate={booking.slotDate}
            slotTime={booking.slotTime}
            onDismiss={() => setBooking(null)}
          />
        ) : showEmergency ? (
          <EmergencyPrompt
            prefillName={ramq?.prenom ?? ''}
            prefillRamq={ramq?.numero ?? ''}
            onBack={() => setShowEmergency(false)}
          />
        ) : (
          <>
            <ServiceTypeSelector
              selectedServiceType={serviceType}
              onServiceTypeChange={setServiceType}
              onEmergencySelect={() => setShowEmergency(true)}
            />
            {/* TODO: ClinicCards component goes here (teammate #18) */}
          </>
        )}

        <ChatPanel
          locale={locale}
          onServiceTypeSelect={setServiceType}
          onEmergencySelect={() => setShowEmergency(true)}
        />

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

        {/* Paused banner */}
        {paused && (
          <div role="status" aria-live="polite"
            className="rounded-lg bg-yellow-50 border border-yellow-200 px-4 py-3 text-sm text-yellow-800 text-center mb-4">
            {t('paused')}
          </div>
        )}

        {/* Booking error */}
        {bookError && (
          <div role="alert" className="bg-red-50 border border-red-200 text-red-800 rounded-xl px-4 py-3 mb-4 text-sm flex items-center justify-between">
            <span>{bookError}</span>
            <button type="button" onClick={() => setBookError(null)} className="ml-4 text-red-600 hover:text-red-800 font-medium text-xs">✕</button>
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
          {clinics.map((clinic) => (
            <article key={clinic.clinic_name} className="bg-white rounded-2xl shadow p-5">
              <h2 className="text-lg font-semibold">{clinic.clinic_name}</h2>
              <p className="text-sm text-gray-500 mt-1">{clinic.address}</p>
              <p className="text-sm font-medium mt-3 mb-2">
                {t('slots_count', { count: clinic.slots.length })}
              </p>
              <div className="flex flex-wrap gap-2">
                {clinic.slots.map((slot) => (
                  <div key={`${slot.date}-${slot.time}`} className="flex items-center gap-2 bg-blue-50 rounded-lg px-3 py-2">
                    <span className="text-sm text-blue-800 font-medium">
                      {slot.date} · {slot.time}
                    </span>
                    <button
                      type="button"
                      aria-label={`${t('book')} — ${slot.date} ${slot.time} — ${clinic.clinic_name}`}
                      disabled={bookingSlotId !== null}
                      onClick={() => handleBook(clinic, slot)}
                      className="text-xs bg-blue-600 text-white rounded-lg px-3 py-1 hover:bg-blue-700 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {bookingSlotId === slot.slot_id ? '…' : t('book')}
                    </button>
                  </div>
                ))}
              </div>
            </article>
          ))}
        </div>
      </div>
    </main>
  );
}
