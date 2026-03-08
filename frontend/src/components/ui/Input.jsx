export default function Input({ label, error, ...props }) {
  return (
    <div>
      {label && <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>}
      <input
        className={`w-full px-3 py-2 border rounded-lg text-sm outline-none transition-colors
          ${error ? "border-red-300 focus:ring-2 focus:ring-red-200" : "border-gray-300 focus:ring-2 focus:ring-accent/20 focus:border-accent"}`}
        {...props}
      />
      {error && <p className="text-xs text-red-500 mt-1">{error}</p>}
    </div>
  );
}

export function TextArea({ label, error, ...props }) {
  return (
    <div>
      {label && <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>}
      <textarea
        className={`w-full px-3 py-2 border rounded-lg text-sm outline-none transition-colors resize-none
          ${error ? "border-red-300 focus:ring-2 focus:ring-red-200" : "border-gray-300 focus:ring-2 focus:ring-accent/20 focus:border-accent"}`}
        rows={3}
        {...props}
      />
      {error && <p className="text-xs text-red-500 mt-1">{error}</p>}
    </div>
  );
}

export function Select({ label, error, children, ...props }) {
  return (
    <div>
      {label && <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>}
      <select
        className={`w-full px-3 py-2 border rounded-lg text-sm outline-none transition-colors
          ${error ? "border-red-300" : "border-gray-300 focus:ring-2 focus:ring-accent/20 focus:border-accent"}`}
        {...props}
      >
        {children}
      </select>
      {error && <p className="text-xs text-red-500 mt-1">{error}</p>}
    </div>
  );
}
