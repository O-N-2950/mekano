import { useSelector } from "react-redux";
import { Users, Car, Wrench, FileText } from "lucide-react";

const stats = [
  { label: "Clients", value: "--", icon: Users, color: "bg-blue-50 text-blue-600" },
  { label: "Vehicules", value: "--", icon: Car, color: "bg-green-50 text-green-600" },
  { label: "OT en cours", value: "--", icon: Wrench, color: "bg-orange-50 text-orange-600" },
  { label: "Factures", value: "--", icon: FileText, color: "bg-purple-50 text-purple-600" },
];

export default function Dashboard() {
  const garage = useSelector((s) => s.auth.garage);

  return (
    <div>
      <h2 className="text-xl font-semibold mb-6">
        Tableau de bord
        {garage && <span className="text-gray-400 font-normal text-base ml-2">- {garage.nom}</span>}
      </h2>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="bg-white rounded-xl border border-gray-200 p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-gray-500">{label}</span>
              <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${color}`}>
                <Icon size={18} />
              </div>
            </div>
            <p className="text-2xl font-semibold font-mono">{value}</p>
          </div>
        ))}
      </div>

      <div className="mt-8 bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="font-medium mb-3">Phase 1 - MVP</h3>
        <p className="text-sm text-gray-500">
          Les statistiques et graphiques seront affiches ici une fois les donnees connectees.
          Le dashboard affichera les OT en cours, les vehicules en attente de MFK,
          et le chiffre d'affaires du mois.
        </p>
      </div>
    </div>
  );
}
