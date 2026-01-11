import React, { useState } from 'react';
import PhoneInput, { isValidPhoneNumber } from 'react-phone-number-input';
import 'react-phone-number-input/style.css';
import { AlertCircle } from 'lucide-react';

interface Props {
  value: string;
  onChange: (val: string) => void;
}

export default function GlobalPhoneInput({ value, onChange }: Props) {
  const [isFocused, setIsFocused] = useState(false);
  
  // Real-time validation check
  const isValid = value ? isValidPhoneNumber(value) : true; 

  return (
    <div className="relative group">
      <style>{`
        .PhoneInput {
          display: flex;
          align-items: center;
        }
        /* Fix the dropdown visual */
        .PhoneInputCountry {
          margin-right: 12px;
          padding: 8px 12px;
          background: rgba(255, 255, 255, 0.05);
          border-radius: 8px 0 0 8px;
          border-right: 1px solid rgba(255, 255, 255, 0.1);
        }
        .PhoneInputCountrySelect {
          background: #000;
          color: #fff;
          cursor: pointer;
        }
        /* Make the country list dark mode compatible */
        .PhoneInputCountrySelect option {
          background-color: #111;
          color: white;
        }
        .PhoneInputInput {
          background: transparent;
          border: none;
          color: white;
          font-family: monospace;
          font-size: 14px;
          outline: none;
          height: 100%;
          width: 100%;
        }
        .PhoneInputInput::placeholder {
          color: #6b7280;
        }
      `}</style>

      <div 
        className={`
          flex bg-black border rounded-lg overflow-hidden transition-all duration-300
          ${!isValid && value 
            ? 'border-red-500/50 shadow-[0_0_15px_rgba(239,68,68,0.2)]' 
            : isFocused 
              ? 'border-emerald-500/50 shadow-[0_0_15px_rgba(16,185,129,0.2)]' 
              : 'border-white/10 hover:border-white/20'
          }
        `}
      >
        <PhoneInput
          defaultCountry="GH" 
          // 🟢 UX FIX: Limit to key markets only to prevent "Doom Scrolling"
          countries={["GH", "NG", "US", "GB", "CA", "DE", "FR", "ZA", "AE", "CN"]}
          international
          withCountryCallingCode
          value={value}
          onChange={(val) => onChange(val || '')}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder="Enter phone number"
          className="w-full"
          numberInputProps={{
            className: "w-full bg-transparent text-white text-sm px-3 py-2.5 focus:outline-none font-mono placeholder-gray-600 h-full"
          }}
        />
        
        <div className="flex items-center px-3">
          {!isValid && value && (
            <div className="text-red-500 animate-pulse" title="Invalid Number Format">
              <AlertCircle size={16} />
            </div>
          )}
          {isValid && value && (
            <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]" />
          )}
        </div>
      </div>
      
      {!isValid && value && (
        <div className="absolute -bottom-5 left-0 text-[10px] text-red-400 font-bold flex items-center gap-1">
          Invalid format for this country
        </div>
      )}
    </div>
  );
}
