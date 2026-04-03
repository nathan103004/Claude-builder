import { redirect } from 'next/navigation';

export default function OnboardingIndex({ params: { locale } }: { params: { locale: string } }) {
  redirect(`/${locale}/onboarding/language`);
}
