'use client';

import { useRef, useEffect, useState } from 'react';
import { useTranslations } from 'next-intl';

export interface EmergencyPromptProps {
  prefillName: string;
  prefillRamq: string;
  onBack: () => void;
}

export default function EmergencyPrompt({
  prefillName,
  prefillRamq,
  onBack,
}: EmergencyPromptProps) {
  const t = useTranslations('dashboard.emergency');
  const callButtonRef = useRef<HTMLAnchorElement>(null);

  const [name, setName] = useState(prefillName);
  const [location, setLocation] = useState('');
  const [ramq, setRamq] = useState(prefillRamq);

  useEffect(() => {
    callButtonRef.current?.focus();
  }, []);

  return (
    <div className="max-w-lg mx-auto">
      <div
        role="alert"
        aria-live="assertive"
        className="bg-red-600 text-white p-6 rounded-t-lg flex items-center gap-3"
      >
        <span aria-hidden="true" className="text-3xl">📞</span>
        <h1 className="text-2xl font-bold">{t('heading')}</h1>
      </div>

      <div className="border border-t-0 border-gray-200 rounded-b-lg p-6 bg-white flex flex-col gap-6">
        <p className="text-gray-700">{t('subheading')}</p>

        <a
          ref={callButtonRef}
          href="tel:911"
          className="block w-full bg-red-600 text-white text-center py-4 rounded-lg text-xl font-bold hover:bg-red-700 focus:outline-none focus:ring-4 focus:ring-red-300"
        >
          {t('call_button')}
        </a>

        <section>
          <h2 className="text-lg font-semibold mb-2">{t('script_heading')}</h2>
          <p className="text-gray-600 mb-4">{t('script_intro')}</p>

          <div className="flex flex-col gap-4">
            <div>
              <label htmlFor="emergency-name" className="block text-sm font-medium text-gray-700 mb-1">
                {t('label_name')}
              </label>
              <input
                id="emergency-name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder={t('placeholder_name')}
                className="border border-gray-300 rounded p-2 w-full"
              />
            </div>

            <div>
              <label htmlFor="emergency-location" className="block text-sm font-medium text-gray-700 mb-1">
                {t('label_location')}
              </label>
              <input
                id="emergency-location"
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder={t('placeholder_location')}
                className="border border-gray-300 rounded p-2 w-full"
              />
            </div>

            <div>
              <label htmlFor="emergency-ramq" className="block text-sm font-medium text-gray-700 mb-1">
                {t('label_ramq')}
              </label>
              <input
                id="emergency-ramq"
                type="text"
                value={ramq}
                onChange={(e) => setRamq(e.target.value)}
                placeholder={t('placeholder_ramq')}
                className="border border-gray-300 rounded p-2 w-full"
              />
            </div>
          </div>
        </section>

        <p role="note" className="text-sm text-gray-500 mt-4">
          {t('disclaimer')}
        </p>

        <button
          type="button"
          onClick={onBack}
          className="text-blue-600 underline hover:text-blue-800 self-start"
        >
          {t('back')}
        </button>
      </div>
    </div>
  );
}
