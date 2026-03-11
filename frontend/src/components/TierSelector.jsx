import React from "react";

const TIERS = [
  {
    id: 1,
    label: "Tier 1",
    title: "Organisation Number",
    description: "Deterministic match on organisation number. Fastest and highest confidence.",
    badge: "Exact match",
    badgeColor: "bg-green-100 text-green-700",
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    ),
  },
  {
    id: 2,
    label: "Tier 2",
    title: "Name + City",
    description: "Fuzzy match on company name with city as a disambiguation boost.",
    badge: "Fuzzy + boost",
    badgeColor: "bg-blue-100 text-blue-700",
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
  },
  {
    id: 3,
    label: "Tier 3",
    title: "Name Only",
    description: "Fuzzy match on company name only. Lowest confidence — most manual review needed.",
    badge: "Fuzzy only",
    badgeColor: "bg-amber-100 text-amber-700",
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
      </svg>
    ),
  },
];

export default function TierSelector({ selected, onSelect }) {
  return (
    <div className="grid grid-cols-3 gap-5">
      {TIERS.map((tier) => {
        const isSelected = selected === tier.id;
        return (
          <button
            key={tier.id}
            onClick={() => onSelect(tier.id)}
            className={`relative text-left p-6 rounded-xl border-2 transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
              isSelected
                ? "border-blue-500 bg-blue-50 shadow-md"
                : "border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm"
            }`}
          >
            <div className="flex items-start justify-between mb-3">
              <div className={`p-2 rounded-lg ${isSelected ? "bg-blue-100 text-blue-600" : "bg-gray-100 text-gray-500"}`}>
                {tier.icon}
              </div>
              <span className={`text-xs font-medium px-2 py-1 rounded-full ${tier.badgeColor}`}>
                {tier.badge}
              </span>
            </div>
            <div className="mb-1">
              <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                {tier.label}
              </span>
            </div>
            <h3 className="text-base font-semibold text-gray-900 mb-2">{tier.title}</h3>
            <p className="text-sm text-gray-500 leading-relaxed">{tier.description}</p>
            {isSelected && (
              <div className="absolute top-4 right-4">
                <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center">
                  <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                </div>
              </div>
            )}
          </button>
        );
      })}
    </div>
  );
}
