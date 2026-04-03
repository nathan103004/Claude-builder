'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { useRouter } from 'next/navigation';
import { useOnboarding } from '@/context/OnboardingContext';

export default function AccountPage({ params: { locale } }: { params: { locale: string } }) {
  const t = useTranslations('onboarding.account');
  const router = useRouter();
  const { setMode, setToken } = useOnboarding();

  const [showForm, setShowForm] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  function continueAsGuest() {
    setMode('guest');
    router.push(`/${locale}/onboarding/text-size`);
  }

  async function handleRegister(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (res.status === 409) { setError(t('error_duplicate')); return; }
      if (!res.ok) { setError(t('error_generic')); return; }
      setMode('account');
      setToken(data.token);
      router.push(`/${locale}/onboarding/text-size`);
    } catch {
      setError(t('error_generic'));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold text-center">{t('title')}</h1>

      {!showForm ? (
        <div className="flex flex-col gap-4">
          <button
            type="button"
            onClick={() => setShowForm(true)}
            className="w-full py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
          >
            {t('create')}
          </button>
          <button
            type="button"
            onClick={continueAsGuest}
            className="w-full py-3 border-2 border-gray-300 rounded-xl font-semibold hover:border-gray-400 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
          >
            {t('guest')}
          </button>
        </div>
      ) : (
        <form onSubmit={handleRegister} className="flex flex-col gap-4">
          <div>
            <label className="block text-sm font-medium mb-1" htmlFor="email">{t('email')}</label>
            <input
              id="email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1" htmlFor="password">{t('password')}</label>
            <input
              id="password"
              type="password"
              required
              minLength={6}
              autoComplete="new-password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          {error && <p role="alert" className="text-red-600 text-sm">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
          >
            {loading ? '...' : t('submit')}
          </button>
          <button type="button" onClick={() => setShowForm(false)} className="text-sm text-gray-500 underline focus-visible:ring-2 focus-visible:ring-blue-500 rounded">
            ← {t('guest')}
          </button>
        </form>
      )}
    </div>
  );
}
