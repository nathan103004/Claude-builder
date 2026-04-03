'use client';

import { useTranslations } from 'next-intl';
import { useRouter } from 'next/navigation';
import { useOnboarding, TextSize } from '@/context/OnboardingContext';

const SIZES: { key: TextSize; labelKey: string }[] = [
  { key: 'sm', labelKey: 'sm' },
  { key: 'md', labelKey: 'md' },
  { key: 'lg', labelKey: 'lg' },
  { key: 'xl', labelKey: 'xl' },
];

export default function TextSizePage({ params: { locale } }: { params: { locale: string } }) {
  const t = useTranslations('onboarding.textSize');
  const router = useRouter();
  const { textSize, setTextSize } = useOnboarding();

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold text-center">{t('title')}</h1>
      <div className="flex flex-col gap-3" role="group" aria-labelledby="text-size-heading">
        <span id="text-size-heading" className="sr-only">{t('title')}</span>
        {SIZES.map(({ key, labelKey }) => (
          <button
            key={key}
            type="button"
            onClick={() => setTextSize(key)}
            aria-pressed={textSize === key}
            className={`w-full py-3 rounded-xl border-2 font-medium transition-colors
              focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2
              ${textSize === key ? 'bg-blue-600 text-white border-blue-600' : 'border-gray-300 hover:border-blue-400'}`}
          >
            {t(labelKey)}
          </button>
        ))}
      </div>
      <button
        type="button"
        onClick={() => router.push(`/${locale}/onboarding/postal-code`)}
        className="w-full py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
      >
        {t('next')}
      </button>
    </div>
  );
}
