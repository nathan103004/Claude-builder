'use client';

import { useRef, useState } from 'react';
import { useTranslations } from 'next-intl';
import { useRouter } from 'next/navigation';
import { useOnboarding, RamqData } from '@/context/OnboardingContext';

const NUMERO_RE = /^[A-Za-z]{4}\d{8}$/;
const SEQ_RE = /^\d{2}$/;
const DAYS = Array.from({ length: 31 }, (_, i) => String(i + 1).padStart(2, '0'));
const MONTHS = ['01','02','03','04','05','06','07','08','09','10','11','12'];
const YEARS = Array.from({ length: 100 }, (_, i) => String(new Date().getFullYear() - i));

type View = 'choose' | 'manual' | 'scanning';

export default function RamqPage({ params: { locale } }: { params: { locale: string } }) {
  const t = useTranslations('onboarding.ramq');
  const router = useRouter();
  const { setRamq } = useOnboarding();
  const fileRef = useRef<HTMLInputElement>(null);

  const [view, setView] = useState<View>('choose');
  const [scanError, setScanError] = useState('');

  const [prenom, setPrenom] = useState('');
  const [nom, setNom] = useState('');
  const [numero, setNumero] = useState('');
  const [sequentiel, setSequentiel] = useState('');
  const [dobDay, setDobDay] = useState('');
  const [dobMonth, setDobMonth] = useState('');
  const [dobYear, setDobYear] = useState('');
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setView('scanning');
    setScanError('');
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch('/api/ocr/ramq', { method: 'POST', body: formData });
      if (!res.ok) throw new Error('ocr failed');
      const data: RamqData = await res.json();
      setRamq(data);
      router.push(`/${locale}/dashboard`);
    } catch {
      setScanError(t('scan_error'));
      setView('choose');
    }
  }

  function handleSkip() {
    setRamq(null);
    router.push(`/${locale}/dashboard`);
  }

  function validateManual(): boolean {
    const errors: Record<string, string> = {};
    if (!NUMERO_RE.test(numero)) errors.numero = t('numero_error');
    if (!SEQ_RE.test(sequentiel)) errors.sequentiel = t('sequentiel_error');
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  }

  function handleManualSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validateManual()) return;
    setRamq({ prenom, nom, numero: numero.toUpperCase(), sequentiel, dob_day: dobDay, dob_month: dobMonth, dob_year: dobYear });
    router.push(`/${locale}/dashboard`);
  }

  if (view === 'scanning') {
    return (
      <div className="flex flex-col items-center gap-4" role="status" aria-live="polite">
        <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" aria-hidden="true" />
        <p>{t('scanning')}</p>
      </div>
    );
  }

  if (view === 'manual') {
    return (
      <form onSubmit={handleManualSubmit} className="flex flex-col gap-4">
        <h1 className="text-2xl font-bold text-center">{t('title')}</h1>
        <div>
          <label htmlFor="prenom" className="block text-sm font-medium mb-1">{t('prenom')}</label>
          <input id="prenom" type="text" required value={prenom} onChange={e => setPrenom(e.target.value)}
            className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label htmlFor="nom" className="block text-sm font-medium mb-1">{t('nom')}</label>
          <input id="nom" type="text" required value={nom} onChange={e => setNom(e.target.value)}
            className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label htmlFor="numero" className="block text-sm font-medium mb-1">{t('numero')}</label>
          <input id="numero" type="text" required maxLength={12} value={numero}
            onChange={e => setNumero(e.target.value.toUpperCase())} placeholder="GUAN94012812"
            aria-describedby={formErrors.numero ? 'numero-error' : undefined}
            className="w-full border rounded-lg px-3 py-2 uppercase tracking-widest focus:outline-none focus:ring-2 focus:ring-blue-500" />
          {formErrors.numero && <p id="numero-error" role="alert" className="text-red-600 text-sm mt-1">{formErrors.numero}</p>}
        </div>
        <div>
          <label htmlFor="sequentiel" className="block text-sm font-medium mb-1">{t('sequentiel')}</label>
          <input id="sequentiel" type="text" required maxLength={2} value={sequentiel}
            onChange={e => setSequentiel(e.target.value.replace(/\D/g, ''))} placeholder="01"
            aria-describedby={formErrors.sequentiel ? 'seq-error' : undefined}
            className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
          {formErrors.sequentiel && <p id="seq-error" role="alert" className="text-red-600 text-sm mt-1">{formErrors.sequentiel}</p>}
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">{t('dob')}</label>
          <div className="flex gap-2">
            <select required value={dobDay} onChange={e => setDobDay(e.target.value)} aria-label={t('dob_day')}
              className="flex-1 border rounded-lg px-2 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option value="">{t('dob_day')}</option>
              {DAYS.map(d => <option key={d} value={d}>{d}</option>)}
            </select>
            <select required value={dobMonth} onChange={e => setDobMonth(e.target.value)} aria-label={t('dob_month')}
              className="flex-1 border rounded-lg px-2 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option value="">{t('dob_month')}</option>
              {MONTHS.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
            <select required value={dobYear} onChange={e => setDobYear(e.target.value)} aria-label={t('dob_year')}
              className="flex-1 border rounded-lg px-2 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option value="">{t('dob_year')}</option>
              {YEARS.map(y => <option key={y} value={y}>{y}</option>)}
            </select>
          </div>
        </div>
        <button type="submit"
          className="w-full py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2">
          {t('submit')}
        </button>
        <button type="button" onClick={() => setView('choose')}
          className="text-sm text-gray-500 underline text-center focus-visible:ring-2 focus-visible:ring-blue-500 rounded">
          ←
        </button>
      </form>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-bold text-center">{t('title')}</h1>
      {scanError && <p role="alert" className="text-red-600 text-sm text-center">{scanError}</p>}
      <input ref={fileRef} type="file" accept="image/*" capture="environment"
        className="hidden" onChange={handleFileChange} aria-hidden="true" />
      <button type="button" onClick={() => fileRef.current?.click()}
        className="w-full py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2">
        {t('scan')}
      </button>
      <button type="button" onClick={() => setView('manual')}
        className="w-full py-3 border-2 border-gray-300 rounded-xl font-semibold hover:border-gray-400 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2">
        {t('manual')}
      </button>
      <button type="button" onClick={handleSkip}
        className="text-sm text-gray-500 underline text-center focus-visible:ring-2 focus-visible:ring-blue-500 rounded">
        {t('skip')}
      </button>
    </div>
  );
}
