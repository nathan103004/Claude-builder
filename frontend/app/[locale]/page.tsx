import { useTranslations } from 'next-intl';
import Link from 'next/link';

export default function Home({ params: { locale } }: { params: { locale: string } }) {
  const t = useTranslations('home');
  const otherLocale = locale === 'fr' ? 'en' : 'fr';

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 gap-6 bg-white">
      {/* Quebec fleur-de-lis accent bar */}
      <div className="flex flex-col items-center gap-3 text-center">
        <div className="w-16 h-1 bg-blue-600 rounded-full mb-2" />
        <h1 className="text-5xl font-bold text-blue-600 tracking-tight">{t('title')}</h1>
        <p className="text-lg text-gray-500 max-w-sm">{t('subtitle')}</p>
      </div>
      <Link
        href={`/${locale}/onboarding/language`}
        className="mt-2 px-10 py-4 bg-blue-600 text-white text-lg font-semibold rounded-xl hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-300 shadow-md transition-colors"
      >
        {t('get_started')}
      </Link>
      <Link
        href={`/${locale}/dashboard?demo=true`}
        className="text-sm text-blue-600 hover:text-blue-800 underline"
      >
        {t('try_demo')}
      </Link>
      <Link href={`/${otherLocale}`} className="text-sm underline text-blue-600 hover:text-blue-800">
        {t('language_toggle')}
      </Link>
      <p className="absolute bottom-6 text-xs text-gray-400">
        Gouvernement du Québec
      </p>
    </main>
  );
}
