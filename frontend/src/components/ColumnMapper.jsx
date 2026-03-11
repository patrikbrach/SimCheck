import React from "react";

const FIELD_CONFIGS = {
  1: [
    { key: "org_nr", label: "Organisation Number", required: true,
      hint: "Column containing organisation/company registration number" },
  ],
  2: [
    { key: "company_name", label: "Company Name", required: true,
      hint: "Column containing the company name to match" },
    { key: "city", label: "City", required: true,
      hint: "Column containing the city for disambiguation" },
    { key: "org_nr", label: "Organisation Number", required: false,
      hint: "Optional — for reference/display in results" },
  ],
  3: [
    { key: "company_name", label: "Company Name", required: true,
      hint: "Column containing the company name to match" },
    { key: "org_nr", label: "Organisation Number", required: false,
      hint: "Optional — for reference/display in results" },
  ],
};

export default function ColumnMapper({ tier, columns, mappings, onChange }) {
  const fields = FIELD_CONFIGS[tier] || [];

  function handleChange(key, value) {
    onChange({ ...mappings, [key]: value || undefined });
  }

  return (
    <div className="space-y-4">
      {fields.map((field) => (
        <div key={field.key} className="flex items-start gap-4">
          <div className="w-48 flex-shrink-0 pt-2">
            <label className="block text-sm font-medium text-gray-700">
              {field.label}
              {field.required ? (
                <span className="ml-1 text-red-500">*</span>
              ) : (
                <span className="ml-1 text-gray-400 font-normal text-xs">(optional)</span>
              )}
            </label>
            <p className="text-xs text-gray-400 mt-0.5">{field.hint}</p>
          </div>
          <div className="flex-1">
            <select
              value={mappings[field.key] || ""}
              onChange={(e) => handleChange(field.key, e.target.value)}
              className={`w-full px-3 py-2 text-sm bg-white border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors ${
                !mappings[field.key] && field.required
                  ? "border-gray-300"
                  : mappings[field.key]
                  ? "border-green-400 bg-green-50"
                  : "border-gray-300"
              }`}
            >
              <option value="">— Select column —</option>
              {columns.map((col) => (
                <option key={col} value={col}>
                  {col}
                </option>
              ))}
            </select>
          </div>
          <div className="pt-2.5 flex-shrink-0">
            {mappings[field.key] ? (
              <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            ) : field.required ? (
              <div className="w-5 h-5 rounded-full border-2 border-gray-300" />
            ) : (
              <div className="w-5 h-5" />
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
