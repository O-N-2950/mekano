import { useState, useEffect, useCallback } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import Skeleton from "../components/ui/Skeleton";

const TYPE_OPTIONS = [
  { value: "piece", label: "Pièce" },
  { value: "main_oeuvre", label: "Main d'œuvre" },
  { value: "peinture", label: "Peinture" },
  { value: "forfait", label: "Forfait" },
];

const TYPE_COLORS = {
  piece: "bg-blue-50 text-blue-700",
  main_oeuvre: "bg-orange-50 text-orange-700",
  peinture: "bg-purple-50 text-purple-700",
  forfait: "bg-green-50 text-green-700",
};

function newLigne(type = "piece") {
  return { _key: Math.random(), type, reference: "", designation: "", quantite: 1, prix_unitaire: 0, remise_pct: 0 };
}

function calcLigne(l) {
  const qty = parseFloat(l.quantite) || 0;
  const pu = parseFloat(l.prix_unitaire) || 0;
  const remise = parseFloat(l.remise_pct) || 0;
  return Math.round(qty * pu * (1 - remise / 100) * 100) / 100;
}

function calcTotaux(lignes, pfPct, tvaPct) {
  let pieces = 0, mo = 0, peinture = 0, forfait = 0;
  for (const l of lignes) {
    const t = calcLigne(l);
    if (l.type === "piece") pieces += t;
    else if (l.type === "main_oeuvre") mo += t;
    else if (l.type === "peinture") peinture += t;
    else forfait += t;
  }
  const pf = Math.round(pieces * (parseFloat(pfPct) || 0) / 100 * 100) / 100;
  const totalHt = Math.round((pieces + mo + peinture + forfait + pf) * 100) / 100;
  const tva = Math.round(totalHt * (parseFloat(tvaPct) || 8.1) / 100 * 100) / 100;
  return { pieces, mo, peinture, forfait, pf, totalHt, tva, totalTtc: Math.round((totalHt + tva) * 100) / 100 };
}

function fmtChf(val) {
  return `CHF ${(val || 0).toLocaleString("fr-CH", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export default function DevisForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isNew = !id;

  const [loading, setLoading] = useState(!isNew);
  const [saving, setSaving] = useState(false);
  const [clients, setClients] = useState([]);
  const [vehicules, setVehicules] = useState([]);
  const [error, setError] = useState("");

  const [clientId, setClientId] = useState("");
  const [vehiculeId, setVehiculeId] = useState("");
  const [vehiculeKm, setVehiculeKm] = useState("");
  const [pfPct, setPfPct] = useState(4);
  const [tvaPct] = useState(8.1);
  const [notesClient, setNotesClient] = useState("");
  const [conditions, setConditions] = useState("Devis valable 30 jours. Prix sous réserve de modification.");
  const [lignes, setLignes] = useState([newLigne("main_oeuvre")]);
  const [statut, setStatut] = useState("brouillon");
  const [numero, setNumero] = useState("");

  const totaux = calcTotaux(lignes, pfPct, tvaPct);

  // Load clients
  useEffect(() => {
    api.get("/api/clients?per_page=200").then((d) => setClients(d.items || [])).catch(() => {});
  }, []);

  // Load vehicules when client changes
  useEffect(() => {
    if (!clientId) { setVehicules([]); setVehiculeId(""); return; }
    api.get(`/api/vehicules?client_id=${clientId}&per_page=50`)
      .then((d) => setVehicules(d.items || []))
      .catch(() => {});
  }, [clientId]);

  // Load existing devis
  useEffect(() => {
    if (isNew) return;
    api.get(`/api/devis/${id}`).then((d) => {
      setClientId(String(d.client_id || ""));
      setVehiculeId(String(d.vehicule_id || ""));
      setVehiculeKm(d.vehicule_km || "");
      setPfPct(d.petites_fournitures_pct || 4);
      setNotesClient(d.notes_client || "");
      setConditions(d.conditions || "");
      setStatut(d.statut || "brouillon");
      setNumero(d.numero || "");
      setLignes(d.lignes.map((l) => ({ ...l, _key: Math.random() })));
      setLoading(false);
    }).catch(() => navigate("/devis"));
  }, [id]);

  function updateLigne(key, field, value) {
    setLignes((prev) => prev.map((l) => l._key === key ? { ...l, [field]: value } : l));
  }

  function removeLigne(key) {
    setLignes((prev) => prev.filter((l) => l._key !== key));
  }

  function moveLigne(key, dir) {
    setLignes((prev) => {
      const idx = prev.findIndex((l) => l._key === key);
      if (idx < 0) return prev;
      const next = [...prev];
      const swap = idx + dir;
      if (swap < 0 || swap >= next.length) return prev;
      [next[idx], next[swap]] = [next[swap], next[idx]];
      return next;
    });
  }

  async function handleSave(newStatut) {
    setError("");
    if (!clientId) { setError("Veuillez sélectionner un client"); return; }
    if (lignes.length === 0) { setError("Ajoutez au moins une ligne"); return; }
    setSaving(true);
    try {
      const payload = {
        client_id: parseInt(clientId),
        vehicule_id: vehiculeId ? parseInt(vehiculeId) : null,
        vehicule_km: vehiculeKm ? parseInt(vehiculeKm) : null,
        petites_fournitures_pct: parseFloat(pfPct),
        taux_tva: parseFloat(tvaPct),
        notes_client: notesClient,
        conditions,
        lignes: lignes.map((l, i) => ({
          ordre: i,
          type: l.type,
          reference: l.reference,
          designation: l.designation,
          quantite: parseFloat(l.quantite) || 1,
          prix_unitaire: parseFloat(l.prix_unitaire) || 0,
          remise_pct: parseFloat(l.remise_pct) || 0,
        })),
      };

      let saved;
      if (isNew) {
        saved = await api.post("/api/devis", payload);
      } else {
        saved = await api.put(`/api/devis/${id}`, payload);
      }

      if (newStatut && newStatut !== saved.statut) {
        await api.patch(`/api/devis/${saved.id}/statut`, { statut: newStatut });
      }

      navigate("/devis");
    } catch (e) {
      setError(e.message || "Erreur lors de la sauvegarde");
    } finally {
      setSaving(false);
    }
  }

  async function handlePdf() {
    if (isNew) { setError("Sauvegardez d'abord le devis pour générer le PDF"); return; }
    const token = localStorage.getItem("token");
    const res = await fetch(`${import.meta.env.VITE_API_URL}/api/devis/${id}/pdf`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return;
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    window.open(url, "_blank");
  }

  if (loading) return (
    <div className="space-y-4">
      {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}
    </div>
  );

  return (
    <div className="max-w-5xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <button onClick={() => navigate("/devis")} className="text-sm text-gray-500 hover:text-gray-700 mb-1">
            ← Retour aux devis
          </button>
          <h1 className="text-xl font-semibold text-gray-900">
            {isNew ? "Nouveau devis" : `Devis ${numero}`}
          </h1>
        </div>
        <div className="flex gap-2">
          {!isNew && (
            <button onClick={handlePdf} className="px-4 py-2 rounded-lg text-sm border border-gray-200 hover:bg-gray-50">
              📄 PDF
            </button>
          )}
          <button
            onClick={() => handleSave("brouillon")}
            disabled={saving}
            className="px-4 py-2 rounded-lg text-sm border border-gray-300 hover:bg-gray-50"
          >
            Sauvegarder brouillon
          </button>
          <button
            onClick={() => handleSave("envoye")}
            disabled={saving}
            className="px-4 py-2 rounded-lg text-sm bg-accent text-white font-medium hover:bg-accent/90"
          >
            {saving ? "..." : "Envoyer"}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      <div className="space-y-6">
        {/* Client + Véhicule */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="font-medium text-gray-900 mb-4">Client & Véhicule</h2>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Client *</label>
              <select
                value={clientId}
                onChange={(e) => setClientId(e.target.value)}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/30"
              >
                <option value="">Sélectionner un client</option>
                {clients.map((c) => (
                  <option key={c.id} value={c.id}>{c.prenom} {c.nom}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Véhicule</label>
              <select
                value={vehiculeId}
                onChange={(e) => setVehiculeId(e.target.value)}
                disabled={!clientId}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/30 disabled:bg-gray-50"
              >
                <option value="">Aucun</option>
                {vehicules.map((v) => (
                  <option key={v.id} value={v.id}>{v.marque} {v.modele} — {v.plaque || "sans plaque"}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Kilométrage</label>
              <input
                type="number"
                value={vehiculeKm}
                onChange={(e) => setVehiculeKm(e.target.value)}
                placeholder="ex: 84000"
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/30"
              />
            </div>
          </div>
        </div>

        {/* Lignes */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-medium text-gray-900">Lignes du devis</h2>
            <div className="flex gap-2">
              {TYPE_OPTIONS.map((t) => (
                <button
                  key={t.value}
                  onClick={() => setLignes((prev) => [...prev, newLigne(t.value)])}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium ${TYPE_COLORS[t.value]}`}
                >
                  + {t.label}
                </button>
              ))}
            </div>
          </div>

          {lignes.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-6">Aucune ligne — ajoutez des éléments ci-dessus</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100">
                    <th className="pb-2 text-left text-xs font-medium text-gray-500 w-8"></th>
                    <th className="pb-2 text-left text-xs font-medium text-gray-500 w-24">Type</th>
                    <th className="pb-2 text-left text-xs font-medium text-gray-500 w-28">Réf.</th>
                    <th className="pb-2 text-left text-xs font-medium text-gray-500">Désignation *</th>
                    <th className="pb-2 text-right text-xs font-medium text-gray-500 w-20">Qté</th>
                    <th className="pb-2 text-right text-xs font-medium text-gray-500 w-24">PU HT</th>
                    <th className="pb-2 text-right text-xs font-medium text-gray-500 w-20">Remise%</th>
                    <th className="pb-2 text-right text-xs font-medium text-gray-500 w-24">Total HT</th>
                    <th className="pb-2 w-16"></th>
                  </tr>
                </thead>
                <tbody>
                  {lignes.map((l, idx) => (
                    <tr key={l._key} className="border-b border-gray-50 hover:bg-gray-50/50">
                      <td className="py-2">
                        <div className="flex flex-col gap-0.5">
                          <button onClick={() => moveLigne(l._key, -1)} disabled={idx === 0} className="text-gray-300 hover:text-gray-500 disabled:opacity-20 text-xs">▲</button>
                          <button onClick={() => moveLigne(l._key, 1)} disabled={idx === lignes.length - 1} className="text-gray-300 hover:text-gray-500 disabled:opacity-20 text-xs">▼</button>
                        </div>
                      </td>
                      <td className="py-2 pr-2">
                        <select
                          value={l.type}
                          onChange={(e) => updateLigne(l._key, "type", e.target.value)}
                          className={`w-full text-xs rounded px-1.5 py-1 border-0 font-medium ${TYPE_COLORS[l.type]}`}
                        >
                          {TYPE_OPTIONS.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                        </select>
                      </td>
                      <td className="py-2 pr-2">
                        <input
                          value={l.reference}
                          onChange={(e) => updateLigne(l._key, "reference", e.target.value)}
                          placeholder="Réf."
                          className="w-full border border-gray-200 rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-accent/30"
                        />
                      </td>
                      <td className="py-2 pr-2">
                        <input
                          value={l.designation}
                          onChange={(e) => updateLigne(l._key, "designation", e.target.value)}
                          placeholder="Description de la prestation"
                          className="w-full border border-gray-200 rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-accent/30"
                        />
                      </td>
                      <td className="py-2 pr-2">
                        <input
                          type="number"
                          value={l.quantite}
                          min="0"
                          step="0.5"
                          onChange={(e) => updateLigne(l._key, "quantite", e.target.value)}
                          className="w-full border border-gray-200 rounded px-2 py-1 text-xs text-right focus:outline-none focus:ring-1 focus:ring-accent/30"
                        />
                      </td>
                      <td className="py-2 pr-2">
                        <input
                          type="number"
                          value={l.prix_unitaire}
                          min="0"
                          step="0.05"
                          onChange={(e) => updateLigne(l._key, "prix_unitaire", e.target.value)}
                          className="w-full border border-gray-200 rounded px-2 py-1 text-xs text-right focus:outline-none focus:ring-1 focus:ring-accent/30"
                        />
                      </td>
                      <td className="py-2 pr-2">
                        <input
                          type="number"
                          value={l.remise_pct}
                          min="0"
                          max="100"
                          step="1"
                          onChange={(e) => updateLigne(l._key, "remise_pct", e.target.value)}
                          className="w-full border border-gray-200 rounded px-2 py-1 text-xs text-right focus:outline-none focus:ring-1 focus:ring-accent/30"
                        />
                      </td>
                      <td className="py-2 pr-2 text-right font-semibold text-xs text-gray-800">
                        {calcLigne(l).toFixed(2)}
                      </td>
                      <td className="py-2 text-right">
                        <button
                          onClick={() => removeLigne(l._key)}
                          className="text-red-400 hover:text-red-600 text-xs px-1"
                        >✕</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Totaux + paramètres */}
        <div className="grid grid-cols-2 gap-6">
          {/* Paramètres */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="font-medium text-gray-900 mb-4">Paramètres</h2>
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Petites fournitures (%)</label>
                <input
                  type="number"
                  value={pfPct}
                  min="0" max="20" step="0.5"
                  onChange={(e) => setPfPct(e.target.value)}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/30"
                />
                <p className="text-xs text-gray-400 mt-1">Appliqué sur le sous-total pièces</p>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">TVA (%)</label>
                <input
                  type="number"
                  value={tvaPct}
                  disabled
                  className="w-full border border-gray-100 rounded-lg px-3 py-2 text-sm bg-gray-50 text-gray-500"
                />
              </div>
            </div>
          </div>

          {/* Totaux */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="font-medium text-gray-900 mb-4">Récapitulatif</h2>
            <div className="space-y-1.5 text-sm">
              {totaux.pieces > 0 && (
                <div className="flex justify-between text-gray-600">
                  <span>Pièces HT</span>
                  <span>{fmtChf(totaux.pieces)}</span>
                </div>
              )}
              {totaux.pf > 0 && (
                <div className="flex justify-between text-gray-500 text-xs">
                  <span>+ {pfPct}% petites fournitures</span>
                  <span>{fmtChf(totaux.pf)}</span>
                </div>
              )}
              {totaux.mo > 0 && (
                <div className="flex justify-between text-gray-600">
                  <span>Main d'œuvre HT</span>
                  <span>{fmtChf(totaux.mo)}</span>
                </div>
              )}
              {totaux.peinture > 0 && (
                <div className="flex justify-between text-gray-600">
                  <span>Peinture HT</span>
                  <span>{fmtChf(totaux.peinture)}</span>
                </div>
              )}
              {totaux.forfait > 0 && (
                <div className="flex justify-between text-gray-600">
                  <span>Forfaits HT</span>
                  <span>{fmtChf(totaux.forfait)}</span>
                </div>
              )}
              <div className="flex justify-between font-semibold text-gray-800 pt-1 border-t border-gray-100">
                <span>Total HT</span>
                <span>{fmtChf(totaux.totalHt)}</span>
              </div>
              <div className="flex justify-between text-gray-600">
                <span>TVA {tvaPct}%</span>
                <span>{fmtChf(totaux.tva)}</span>
              </div>
              <div className="flex justify-between text-lg font-bold text-accent pt-2 border-t-2 border-accent/20">
                <span>Total TTC</span>
                <span>{fmtChf(totaux.totalTtc)}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Notes + Conditions */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="font-medium text-gray-900 mb-4">Notes & Conditions</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Notes pour le client</label>
              <textarea
                value={notesClient}
                onChange={(e) => setNotesClient(e.target.value)}
                maxLength={3000}
                rows={4}
                placeholder="Remarques visibles sur le devis..."
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/30 resize-none"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Conditions générales</label>
              <textarea
                value={conditions}
                onChange={(e) => setConditions(e.target.value)}
                rows={4}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/30 resize-none"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
