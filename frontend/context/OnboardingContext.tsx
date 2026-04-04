'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';

export type TextSize = 'sm' | 'md' | 'lg' | 'xl';
export type AccountMode = 'guest' | 'account';

export interface RamqData {
  prenom: string;
  nom: string;
  numero: string;
  sequentiel: string;
  dob_day: string;
  dob_month: string;
  dob_year: string;
}

interface OnboardingState {
  locale: string;
  mode: AccountMode | null;
  token: string | null;
  textSize: TextSize;
  postalCode: string;
  ramq: RamqData | null;
}

interface OnboardingContextValue extends OnboardingState {
  setLocale: (v: string) => void;
  setMode: (v: AccountMode) => void;
  setToken: (v: string) => void;
  setTextSize: (v: TextSize) => void;
  setPostalCode: (v: string) => void;
  setRamq: (v: RamqData | null) => void;
}

const KEY = 'santenav_onboarding';

function load(): OnboardingState {
  if (typeof window === 'undefined') {
    return { locale: 'fr', mode: null, token: null, textSize: 'md', postalCode: '', ramq: null };
  }
  try {
    const raw = sessionStorage.getItem(KEY);
    if (raw) return { locale: 'fr', mode: null, token: null, textSize: 'md', postalCode: '', ramq: null, ...JSON.parse(raw) };
  } catch {}
  return { locale: 'fr', mode: null, token: null, textSize: 'md', postalCode: '', ramq: null };
}

const OnboardingContext = createContext<OnboardingContextValue | null>(null);

export function OnboardingProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<OnboardingState>(load);

  useEffect(() => {
    sessionStorage.setItem(KEY, JSON.stringify(state));
    document.documentElement.setAttribute('data-text-size', state.textSize);
  }, [state]);

  useEffect(() => {
    if (!state.token) return;
    fetch('/api/auth/me/preferences', {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${state.token}`,
      },
      body: JSON.stringify({
        email_notifications: false,
        locale: state.locale,
        text_size: state.textSize,
        postal_code: state.postalCode,
      }),
    }).catch(() => {});
  }, [state.token, state.locale, state.textSize, state.postalCode]);

  const set = <K extends keyof OnboardingState>(key: K) =>
    (value: OnboardingState[K]) => setState(prev => ({ ...prev, [key]: value }));

  return (
    <OnboardingContext.Provider value={{
      ...state,
      setLocale: set('locale'),
      setMode: set('mode'),
      setToken: set('token'),
      setTextSize: set('textSize'),
      setPostalCode: set('postalCode'),
      setRamq: set('ramq'),
    }}>
      {children}
    </OnboardingContext.Provider>
  );
}

export function useOnboarding(): OnboardingContextValue {
  const ctx = useContext(OnboardingContext);
  if (!ctx) throw new Error('useOnboarding must be used inside OnboardingProvider');
  return ctx;
}
