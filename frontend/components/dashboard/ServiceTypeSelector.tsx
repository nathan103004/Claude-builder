'use client';

import { useTranslations } from 'next-intl';

export type RvsqServiceType =
  | 'consultation_urgente'
  | 'consultation_semi_urgente'
  | 'suivi'
  | 'suivi_pediatrique'
  | 'suivi_grossesse';

export interface ServiceTypeSelectorProps {
  selectedServiceType: RvsqServiceType;
  onServiceTypeChange: (type: RvsqServiceType) => void;
  onEmergencySelect: () => void;
}

const RVSQ_SERVICE_TYPES = [
  'consultation_urgente',
  'consultation_semi_urgente',
  'suivi',
  'suivi_pediatrique',
  'suivi_grossesse',
] as const satisfies readonly RvsqServiceType[];

export default function ServiceTypeSelector({
  selectedServiceType,
  onServiceTypeChange,
  onEmergencySelect,
}: ServiceTypeSelectorProps) {
  const t = useTranslations('dashboard.serviceType');

  return (
    <div className="flex flex-col gap-3">
      <h2 id="service-type-heading" className="text-lg font-semibold">{t('heading')}</h2>

      <div role="group" aria-labelledby="service-type-heading" className="flex flex-col gap-3">
        {RVSQ_SERVICE_TYPES.map((type) => {
          const isSelected = selectedServiceType === type;
          return (
            <button
              key={type}
              type="button"
              onClick={() => onServiceTypeChange(type)}
              aria-pressed={isSelected}
              className={[
                'w-full text-left border rounded-lg p-4 transition-colors',
                isSelected
                  ? 'border-blue-600 bg-blue-50 text-blue-700'
                  : 'border-gray-300 bg-white hover:bg-gray-50',
              ].join(' ')}
            >
              <span className="block font-medium">{t(type)}</span>
              <span
                className={[
                  'block text-sm',
                  isSelected ? 'text-blue-600' : 'text-gray-500',
                ].join(' ')}
              >
                {t(`${type}_desc`)}
              </span>
            </button>
          );
        })}

        <button
          type="button"
          onClick={onEmergencySelect}
          className="w-full text-left border rounded-lg p-4 transition-colors border-red-500 text-red-700 hover:bg-red-50 bg-white"
        >
          <span className="block font-medium">{t('emergency')}</span>
          <span className="block text-sm text-gray-500">{t('emergency_desc')}</span>
        </button>
      </div>
    </div>
  );
}
