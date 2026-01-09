import React from 'react';
import { ShieldCheck, Calendar, Info } from 'lucide-react';

interface AdvisorCardProps {
  type: 'rent' | 'sale';
  location: string;
  price: number;
}

export default function AdvisorCard({ type, location, price }: AdvisorCardProps) {
  // Logic: Custom advice based on property type
  const getAdvice = () => {
    if (type === 'rent') {
      return {
        title: "Renting in Ghana",
        text: `Standard practice in ${location} involves 1-2 years rent advance. Use Asta to help negotiate terms.`,
        icon: <Calendar className="text-orange-400" size={14} />,
        style: "border-orange-500/30 bg-orange-500/5"
      };
    }
    return {
      title: "Buying in Accra",
      text: "Always verify the Indenture and Land Title Commission records before making any deposit.",
      icon: <ShieldCheck className="text-emerald-400" size={14} />,
      style: "border-emerald-500/30 bg-emerald-500/5"
    };
  };

  const advice = getAdvice();

  return (
    <div className={`border rounded-lg p-4 relative overflow-hidden ${advice.style} my-4`}>
      <div className="flex items-start gap-3 relative z-10">
        <div className="mt-0.5">{advice.icon}</div>
        <div>
          <h4 className="text-xs font-bold text-white mb-1 uppercase tracking-wide">
            Asta Advisor
          </h4>
          <p className="text-xs text-gray-300 leading-relaxed font-medium">
            {advice.text}
          </p>
        </div>
      </div>
    </div>
  );
}
