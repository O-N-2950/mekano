import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import Skeleton from "../components/ui/Skeleton";
import Badge from "../components/ui/Badge";
import Pagination from "../components/ui/Pagination";
import ConfirmDialog from "../components/ui/ConfirmDialog";

const STATUTS = [
  { value: "", label: "Tous" },
  { value: "brouillon", label: "Brouillon" },
  { value: "envoye", label: "Envoyé" },
  { value: "accepte", label: "Accepté" },
  { value: "refuse", label: "Refusé" },
  { value: "expire", label: "Expiré" },
];

const BADGE_COLORS = {
  brouillon: "gray",
  envoye: "blue",
  accepte: "green",
  refuse: "red",
  expire: "orange",
};

export default function Devis() {
  const navigate = useNavigate();
  const [devis, setDevis] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statut, setStatut] = useState("");
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [confirmDup, setConfirmDup] = useState(null);

  async function load() {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page, per_page: 20 });
      if (statut) params.set("statut", statut);
      const data = await api.get(`/api/devis?${params}`);
      setDevis(data.items || []);
      setPages(data.pages || 1);
      setTotal(data.total || 0);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [statut, page]);

  async function handleDupliquer(id) {
    await api.post(`/api/devis/${id}/dupliquer`);
    load();
    setConfirmDup(null);
  }

  async function handlePdf(id, numero) {
    const token = localStorage.getItem("token");
    const res = await fetch(`${import.meta.env.VITE_API_URL}/api/devis/${id}/pdf`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return;
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${numero}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function formatChf(val) {
    return `CHF ${(val || 0).toLocaleString("fr-CH", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }

  function formatDate(iso) {
    if (!iso) return "-";
    return new Date(iso).toLocaleDateString("fr-CH");
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Devis</h1>
          <p className="text-sm text-gray-500 mt-0.5">{total} devis au total</p>
        </div>
        <button
          onClick={() => navigate("/devis/nouveau")}
          className="bg-accent text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-accent/90 transition-colors"
        >
          + Nouveau devis
        </button>
      </div>

      {/* Filtres statut */}
      <div className="flex gap-2 mb-4 flex-wrap">
        {STATUTS.map((s) => (
          <button
            key={s.value}
            onClick={() => { setStatut(s.value); setPage(1); }}
            className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
              statut === s.value
                ? "bg-accent text-white"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Numéro</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Client</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Véhicule</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Statut</th>
              <th className="px-4 py-3 text-right font-medium text-gray-600">Total TTC</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Créé le</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Valide jusqu'au</th>
              <th className="px-4 py-3 text-right font-medium text-gray-600">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i} className="border-b border-gray-100">
                  {Array.from({ length: 8 }).map((_, j) => (
                    <td key={j} className="px-4 py-3"><Skeleton className="h-4 w-full" /></td>
                  ))}
                </tr>
              ))
            ) : devis.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-4 py-10 text-center text-gray-400">
                  Aucun devis trouvé
                </td>
              </tr>
            ) : (
              devis.map((d) => (
                <tr key={d.id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 font-mono font-medium text-accent">{d.numero}</td>
                  <td className="px-4 py-3 text-gray-800">{d.client_nom || "-"}</td>
                  <td className="px-4 py-3 text-gray-600 text-xs">{d.vehicule_desc || "-"}</td>
                  <td className="px-4 py-3">
                    <Badge color={BADGE_COLORS[d.statut] || "gray"}>
                      {d.statut}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-right font-semibold text-gray-900">
                    {formatChf(d.total_ttc)}
                  </td>
                  <td className="px-4 py-3 text-gray-500">{formatDate(d.date_creation)}</td>
                  <td className="px-4 py-3 text-gray-500">{formatDate(d.date_validite)}</td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex gap-1 justify-end">
                      <button
                        onClick={() => navigate(`/devis/${d.id}`)}
                        className="px-2 py-1 text-xs rounded bg-gray-100 hover:bg-gray-200 text-gray-700"
                        title="Modifier"
                      >
                        ✏️
                      </button>
                      <button
                        onClick={() => handlePdf(d.id, d.numero)}
                        className="px-2 py-1 text-xs rounded bg-gray-100 hover:bg-gray-200 text-gray-700"
                        title="Télécharger PDF"
                      >
                        📄
                      </button>
                      <button
                        onClick={() => setConfirmDup(d)}
                        className="px-2 py-1 text-xs rounded bg-gray-100 hover:bg-gray-200 text-gray-700"
                        title="Dupliquer"
                      >
                        📋
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {pages > 1 && (
        <div className="mt-4">
          <Pagination page={page} pages={pages} onChange={setPage} />
        </div>
      )}

      {confirmDup && (
        <ConfirmDialog
          title="Dupliquer le devis"
          message={`Créer une copie du devis ${confirmDup.numero} ?`}
          onConfirm={() => handleDupliquer(confirmDup.id)}
          onCancel={() => setConfirmDup(null)}
        />
      )}
    </div>
  );
}
