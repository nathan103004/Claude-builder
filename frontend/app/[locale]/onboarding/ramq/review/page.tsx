'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { useRouter } from 'next/navigation';
import { useOnboarding, RamqData } from '@/context/OnboardingContext';

const NUMERO_RE = /^[A-Za-z]{4}\d{8}$/;
const SEQ_RE = /^\d{2}$/;
const DAYS = Array.from({ length: 31 }, (_, i) => String(i + 1).padStart(2, '0'));
const MONTHS = ['01','02','03','04','05','06','07','08','09','10','11','12'];
const YEARS = Array.from({ length: 100 }, (_, i) => String(new Date().getFullYear() - i));

export default function RamqReviewPage({ params: { locale } }: { params: { locale: string } }) {
  const t = useTranslations('onboarding.ramq');
  const router = useRouter();
  const { ramq, setRamq } = useOnboarding();

  const [prenom, setPrenom] = useState(ramq?.prenom ?? '');
  const [nom, setNom] = useState(ramq?.nom ?? '');
  const [numero, setNumero] = useState(ramq?.numero ?? '');
  const [sequentiel, setSequentiel] = useState(ramq?.sequentiel ?? '');
  const [dobDay, setDobDay] = useState(ramq?.dob_day ?? '');
  const [dobMonth, setDobMonth] = useState(ramq?.dob_month ?? '');
  const [dobYear, setDobYear] = useState(ramq?.dob_year ?? '');
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  function validate(): boolean {
    const errors: Record<string, string> = {};
    if (!NUMERO_RE.test(numero)) errors.numero = t('numero_error');
    if (!SEQ_RE.test(sequentiel)) errors.sequentiel = t('sequentiel_error');
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  }

  function handleConfirm(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;
    const confirmed: RamqData = {
      prenom, nom,
      numero: numero.toUpperCase(),
      sequentiel,
      dob_day: dobDay,
      dob_month: dobMonth,
      dob_year: dobYear,
    };
    setRamq(confirmed);
    router.push(`/${locale}/dashboard`);
  }

  return (
    <form onSubmit={handleConfirm} className="flex flex-col gap-4">
      <h1 className="text-2xl font-bold text-center">{t('review_title')}</h1>
      <div>
        <label htmlFor="r-prenom" className="block text-sm font-medium mb-1">{t('prenom')}</label>
        <input id="r-prenom" type="text" required value={prenom} onChange={e => setPrenom(e.target.value)}
          className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>
      <div>
        <label htmlFor="r-nom" className="block text-sm font-medium mb-1">{t('nom')}</label>
        <input id="r-nom" type="text" required value={nom} onChange={e => setNom(e.target.value)}
          className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>
      <div>
        <label htmlFor="r-numero" className="block text-sm font-medium mb-1">{t('numero')}</label>
        <input id="r-numero" type="text" required maxLength={12} value={numero}
          onChange={e => setNumero(e.target.value.toUpperCase())} placeholder="GUAN94012812"
          aria-describedby={formErrors.numero ? 'r-numero-error' : undefined}
          className="w-full border rounded-lg px-3 py-2 uppercase tracking-widest focus:outline-none focus:ring-2 focus:ring-blue-500" />
        {formErrors.numero && <p id="r-numero-error" role="alert" className="text-red-600 text-sm mt-1">{formErrors.numero}</p>}
      </div>
      <div>
        <label htmlFor="r-seq" className="block text-sm font-medium mb-1">{t('sequentiel')}</label>
        <input id="r-seq" type="text" required maxLength={2} value={sequentiel}
          onChange={e => setSequentiel(e.target.value.replace(/\D/g, ''))} placeholder="01"
          aria-describedby={formErrors.sequentiel ? 'r-seq-error' : undefined}
          className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
        {formErrors.sequentiel && <p id="r-seq-error" role="alert" className="text-red-600 text-sm mt-1">{formErrors.sequentiel}</p>}
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
      <button type="button" onClick={() => router.push(`/${locale}/onboarding/ramq`)}
        aria-label={t('back_aria')}
        className="text-sm text-gray-500 underline text-center focus-visible:ring-2 focus-visible:ring-blue-500 rounded">
        <span aria-hidden="true">←</span>
      </button>
    </form>
  );
}
