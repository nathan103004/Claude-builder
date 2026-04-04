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
        <NextIntlClientProvider messages={messages}>
          <OnboardingProvider>
            {children}
          </OnboardingProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
