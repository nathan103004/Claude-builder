import { useTranslations } from 'next-intl';
import Link from 'next/link';

export default function Home({ params: { locale } }: { params: { locale: string } }) {
  const t = useTranslations('home');
  const otherLocale = locale === 'fr' ? 'en' : 'fr';

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <h1 className="text-4xl font-bold">{t('title')}</h1>
      <p className="mt-4 text-lg text-gray-600">{t('subtitle')}</p>
      <Link href={`/${otherLocale}`} className="mt-6 underline text-blue-600">
        {t('language_toggle')}
      </Link>
    </main>
  );
}
