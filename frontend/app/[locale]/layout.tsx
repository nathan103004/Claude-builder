import { NextIntlClientProvider } from 'next-intl';
import { getMessages } from 'next-intl/server';
import { OnboardingProvider } from '@/context/OnboardingContext';
import '../globals.css';

export default async function LocaleLayout({
  children,
  params: { locale }
}: {
  children: React.ReactNode;
  params: { locale: string };
}) {
  const messages = await getMessages();
  return (
    <html lang={locale}>
      <body>
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-[9999] focus:bg-white focus:px-4 focus:py-2 focus:rounded focus:shadow focus:text-blue-700 focus:font-semibold"
        >
          {locale === 'fr' ? 'Aller au contenu principal' : 'Skip to main content'}
        </a>
        <NextIntlClientProvider messages={messages}>
          <OnboardingProvider>
            {children}
          </OnboardingProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
