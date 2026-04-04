'use client';
import { useTranslations } from 'next-intl';
import { RvsqServiceType } from './ServiceTypeSelector';

export interface BookingConfirmationProps {
  confirmationNumber: string;
  serviceType: RvsqServiceType;
  clinicName: string;
  slotDate: string;
  slotTime: string;
  onDismiss: () => void;
}

export default function BookingConfirmation({
  confirmationNumber,
  serviceType,
  clinicName,
  slotDate,
  slotTime,
  onDismiss,
}: BookingConfirmationProps) {
  const t = useTranslations('booking');

  return (
    <div className="max-w-lg mx-auto bg-white rounded-2xl shadow overflow-hidden">
      {/* Green success banner */}
      <div className="bg-green-600 text-white p-6 rounded-t-lg">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <span aria-hidden="true">✓</span>
          {t('confirmed')}
        </h1>
      </div>

      {/* Card body */}
      <div className="p-6 space-y-4">
        {/* Confirmation number */}
        <div>
          <p className="text-sm text-gray-500">{t('confirmation_number')}</p>
          <p className="font-mono font-bold text-lg mt-1">{confirmationNumber}</p>
        </div>

        {/* Clinic, date, time */}
        {clinicName && (
          <p className="text-sm text-gray-700">
            <span className="font-medium">{clinicName}</span>
          </p>
        )}
        {(slotDate || slotTime) && (
          <p className="text-sm text-gray-700">
            {slotDate}
            {slotDate && slotTime ? ' · ' : ''}
            {slotTime}
          </p>
        )}

        <hr className="border-gray-200" />

        {/* Instructions */}
        <div>
          <h2 className="text-base font-semibold mb-2">{t('instructions_heading')}</h2>
          <p className="text-sm text-gray-700 leading-relaxed">
            {t(`instructions.${serviceType}`)}
          </p>
        </div>
      </div>

      {/* Dismiss button */}
      <div className="px-6 pb-6">
        <button
          type="button"
          onClick={onDismiss}
          className="w-full bg-blue-600 text-white rounded-xl px-4 py-3 font-medium hover:bg-blue-700 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition-colors"
        >
          {t('dismiss')}
        </button>
      </div>
    </div>
  );
}
