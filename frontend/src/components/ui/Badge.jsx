const COLORS = {
  ouvert: "bg-blue-50 text-blue-700 border-blue-200",
  en_cours: "bg-orange-50 text-orange-700 border-orange-200",
  termine: "bg-green-50 text-green-700 border-green-200",
  facture: "bg-purple-50 text-purple-700 border-purple-200",
};

const LABELS = {
  ouvert: "Ouvert",
  en_cours: "En cours",
  termine: "Termine",
  facture: "Facture",
};

export default function Badge({ statut }) {
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${COLORS[statut] || "bg-gray-50 text-gray-700 border-gray-200"}`}>
      {LABELS[statut] || statut}
    </span>
  );
}
