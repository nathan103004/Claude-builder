'use client';

import { useTranslations } from 'next-intl';
import { useRouter } from 'next/navigation';
import { useOnboarding } from '@/context/OnboardingContext';

export default function LanguagePage({ params: { locale } }: { params: { locale: string } }) {
  const t = useTranslations('onboarding.language');
  const router = useRouter();
  const { setLocale } = useOnboarding();

  function choose(chosen: string) {
    setLocale(chosen);
    router.push(`/${chosen}/onboarding/account`);
  }

  return (
    <div className="flex flex-col items-center gap-6">
      <h1 className="text-2xl font-bold text-center">{t('title')}</h1>
      <div className="flex gap-4 w-full">
        <button
          onClick={() => choose('fr')}
          className={`flex-1 py-4 rounded-xl text-lg font-semibold border-2 transition-colors
            ${locale === 'fr' ? 'bg-blue-600 text-white border-blue-600' : 'border-gray-300 hover:border-blue-400'}`}
        >
          {t('fr')}
        </button>
        <button
          onClick={() => choose('en')}
          className={`flex-1 py-4 rounded-xl text-lg font-semibold border-2 transition-colors
            ${locale === 'en' ? 'bg-blue-600 text-white border-blue-600' : 'border-gray-300 hover:border-blue-400'}`}
        >
          {t('en')}
        </button>
      </div>
    </div>
  );
}
