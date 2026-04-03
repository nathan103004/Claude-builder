'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { useRouter } from 'next/navigation';
import { useOnboarding } from '@/context/OnboardingContext';

const POSTAL_CODE_RE = /^[A-Za-z]\d[A-Za-z] \d[A-Za-z]\d$/;

function formatPostalCode(raw: string): string {
  const clean = raw.replace(/\s/g, '').toUpperCase();
  if (clean.length <= 3) return clean;
  return clean.slice(0, 3) + ' ' + clean.slice(3, 6);
}

export default function PostalCodePage({ params: { locale } }: { params: { locale: string } }) {
  const t = useTranslations('onboarding.postalCode');
  const router = useRouter();
  const { postalCode, setPostalCode } = useOnboarding();

  const [value, setValue] = useState(postalCode);
  const [error, setError] = useState('');

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const formatted = formatPostalCode(e.target.value);
    setValue(formatted);
    setError('');
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!POSTAL_CODE_RE.test(value)) {
      setError(t('error'));
      return;
    }
    setPostalCode(value.toUpperCase());
    router.push(`/${locale}/onboarding/ramq`);
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold text-center">{t('title')}</h1>
      <div>
        <label htmlFor="postal-code" className="block text-sm font-medium mb-1">{t('label')}</label>
        <input
          id="postal-code"
          type="text"
          maxLength={7}
          value={value}
          onChange={handleChange}
          placeholder="H9K 1P9"
          autoComplete="postal-code"
          className="w-full border rounded-lg px-3 py-2 text-lg uppercase tracking-widest focus:outline-none focus:ring-2 focus:ring-blue-500"
          aria-describedby={error ? 'postal-error' : undefined}
        />
        {error && <p id="postal-error" role="alert" className="text-red-600 text-sm mt-1">{error}</p>}
      </div>
      <button
        type="submit"
        className="w-full py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
      >
        {t('next')}
      </button>
    </form>
  );
}
