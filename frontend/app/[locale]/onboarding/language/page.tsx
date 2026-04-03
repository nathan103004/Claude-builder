'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { useRouter } from 'next/navigation';
import { useOnboarding } from '@/context/OnboardingContext';

export default function LanguagePage({ params: { locale } }: { params: { locale: string } }) {
  const t = useTranslations('onboarding.language');
  const router = useRouter();
  const { setLocale } = useOnboarding();
  const [selected, setSelected] = useState<string>(locale);

  function choose(chosen: string) {
    setSelected(chosen);
    setLocale(chosen);
    router.push(`/${chosen}/onboarding/account`);
  }

  return (
    <div className="flex flex-col items-center gap-6">
      <h1 className="text-2xl font-bold text-center">{t('title')}</h1>
      <div className="flex gap-4 w-full">
        <button
          type="button"
          onClick={() => choose('fr')}
          aria-pressed={selected === 'fr'}
          className={`flex-1 py-4 rounded-xl text-lg font-semibold border-2 transition-colors
            focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2
            ${selected === 'fr' ? 'bg-blue-600 text-white border-blue-600' : 'border-gray-300 hover:border-blue-400'}`}
        >
          {t('fr')}
        </button>
        <button
          type="button"
          onClick={() => choose('en')}
          aria-pressed={selected === 'en'}
          className={`flex-1 py-4 rounded-xl text-lg font-semibold border-2 transition-colors
            focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2
            ${selected === 'en' ? 'bg-blue-600 text-white border-blue-600' : 'border-gray-300 hover:border-blue-400'}`}
        >
          {t('en')}
        </button>
      </div>
    </div>
  );
}
