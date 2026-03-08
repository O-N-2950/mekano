import { useState, useEffect, useCallback, useRef } from "react";
import { Wrench, Search } from "lucide-react";
import { api, validators } from "../api";
import Modal from "../components/ui/Modal";
import ConfirmDialog from "../components/ui/ConfirmDialog";
import Badge from "../components/ui/Badge";
import Pagination from "../components/ui/Pagination";
import Input, { TextArea, Select } from "../components/ui/Input";
import { SkeletonTable } from "../components/ui/Skeleton";

const EMPTY = {
  client_id: "", vehicule_id: "", description_travaux: "",
  km_entree: "", date_sortie_prevue: "", notes_internes: "",
};

const STATUT_FILTERS = [
  { value: "", label: "Tous" },
  { value: "ouvert", label: "Ouverts" },
  { value: "en_cours", label: "En cours" },
  { value: "termine", label: "Termines" },
  { value: "facture", label: "Factures" },
];

export default function OrdresTravail() {
  const [data, setData] = useState({ items: [], total: 0, page: 1, pages: 1 });
  const [statutFilter, setStatutFilter] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);

  const [clients, setClients] = useState([]);
  const [vehicules, setVehicules] = useState([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(EMPTY);
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);
  const [statutConfirm, setStatutConfirm] = useState(null); // {ordre, newStatut}
  const [changingStatut, setChangingStatut] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page, per_page: 25 });
      if (statutFilter) params.set("statut", statutFilter);
      const res = await api.get(`/api/ordres?${params}`);
      setData(res);
    } catch { /* */ }
    setLoading(false);
  }, [page, statutFilter]);

  useEffect(() => { load(); }, [load]);

  const loadRefs = async () => {
    try {
      const [c, v] = await Promise.all([
        api.get("/api/clients?per_page=500"),
        api.get("/api/vehicules?per_page=500"),
      ]);
      setClients(c.items);
      setVehicules(v.items);
    } catch { /* */ }
  };

  const openCreate = () => {
    setEditing(null);
    setForm(EMPTY);
    setErrors({});
    loadRefs();
    setModalOpen(true);
  };

  const openEdit = (o) => {
    setEditing(o);
    setForm({
      client_id: o.client_id || "",
      vehicule_id: o.vehicule_id || "",
      description_travaux: o.description_travaux || "",
      km_entree: o.km_entree || "",
      date_sortie_prevue: o.date_sortie_prevue ? o.date_sortie_prevue.slice(0, 16) : "",
      notes_internes: o.notes_internes || "",
    });
    setErrors({});
    loadRefs();
    setModalOpen(true);
  };

  const handleSave = async () => {
    setSaving(true);
    setErrors({});
    const payload = {
      ...form,
      client_id: form.client_id ? Number(form.client_id) : null,
      vehicule_id: form.vehicule_id ? Number(form.vehicule_id) : null,
      km_entree: form.km_entree ? Number(form.km_entree) : null,
      date_sortie_prevue: form.date_sortie_prevue || null,
    };
    try {
      if (editing) {
        await api.put(`/api/ordres/${editing.id}`, payload);
      } else {
        await api.post("/api/ordres", payload);
      }
      setModalOpen(false);
      load();
    } catch (err) {
      if (err.errors) setErrors(err.errors);
    }
    setSaving(false);
  };

  const changeStatut = (ordre, newStatut) => {
    setStatutConfirm({ ordre, newStatut });
  };

  const confirmChangeStatut = async () => {
    if (!statutConfirm) return;
    setChangingStatut(true);
    try {
      await api.patch(`/api/ordres/${statutConfirm.ordre.id}/statut`, { statut: statutConfirm.newStatut });
      setStatutConfirm(null);
      load();
    } catch { /* */ }
    setChangingStatut(false);
  };

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const filteredVehicules = form.client_id
    ? vehicules.filter((v) => v.client_id === Number(form.client_id))
    : vehicules;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold">Ordres de travail</h2>
        <button onClick={openCreate} className="bg-accent hover:bg-accent-hover text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors">
          + Nouvel ordre
        </button>
      </div>

      <div className="bg-white rounded-xl border border-gray-200">
        <div className="p-4 border-b border-gray-200 flex gap-2">
          {STATUT_FILTERS.map((f) => (
            <button
              key={f.value}
              onClick={() => { setStatutFilter(f.value); setPage(1); }}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                statutFilter === f.value
                  ? "bg-accent text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        {loading ? (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left text-gray-500 text-xs uppercase tracking-wider">
                <th className="px-4 py-3">N°</th>
                <th className="px-4 py-3">Statut</th>
                <th className="px-4 py-3">Véhicule</th>
                <th className="px-4 py-3">Client</th>
                <th className="px-4 py-3">Description</th>
                <th className="px-4 py-3">Entrée</th>
                <th className="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <SkeletonTable rows={5} cols={7} />
          </table>
        ) : data.items.length === 0 ? (
          <div className="p-12 text-center">
            <Wrench size={40} className="text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500 text-sm">Aucun ordre de travail</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left text-gray-500 text-xs uppercase tracking-wider">
                <th className="px-4 py-3">N</th>
                <th className="px-4 py-3">Statut</th>
                <th className="px-4 py-3">Vehicule</th>
                <th className="px-4 py-3">Client</th>
                <th className="px-4 py-3">Description</th>
                <th className="px-4 py-3">Entree</th>
                <th className="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((o) => (
                <tr key={o.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono text-xs font-medium">{o.numero}</td>
                  <td className="px-4 py-3"><Badge statut={o.statut} /></td>
                  <td className="px-4 py-3 text-gray-600 text-xs">{o.vehicule_desc || "-"}</td>
                  <td className="px-4 py-3 text-gray-600">{o.client_nom || "-"}</td>
                  <td className="px-4 py-3 text-gray-600 max-w-xs truncate">{o.description_travaux}</td>
                  <td className="px-4 py-3 text-xs text-gray-500">
                    {o.date_entree ? new Date(o.date_entree).toLocaleDateString("fr-CH") : "-"}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1">
                      <button onClick={() => openEdit(o)} className="px-2 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50">
                        Modifier
                      </button>
                      {o.transitions_possibles?.map((t) => (
                        <button
                          key={t}
                          onClick={() => changeStatut(o, t)}
                          className="px-2 py-1 text-xs bg-accent/10 text-accent rounded hover:bg-accent/20 font-medium"
                        >
                          {t === "en_cours" ? "Demarrer" : t === "termine" ? "Terminer" : t === "facture" ? "Facturer" : t === "ouvert" ? "Rouvrir" : t}
                        </button>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        <Pagination page={data.page} pages={data.pages} total={data.total} onChange={setPage} />
      </div>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={editing ? `Modifier ${editing.numero}` : "Nouvel ordre de travail"} wide>
        {!editing && (
          <div className="grid grid-cols-2 gap-4 mb-4">
            <Select label="Client *" value={form.client_id} onChange={set("client_id")} error={errors.client_id}>
              <option value="">-- Choisir --</option>
              {clients.map((c) => (
                <option key={c.id} value={c.id}>{c.prenom} {c.nom}</option>
              ))}
            </Select>
            <Select label="Vehicule *" value={form.vehicule_id} onChange={set("vehicule_id")} error={errors.vehicule_id}>
              <option value="">-- Choisir --</option>
              {filteredVehicules.map((v) => (
                <option key={v.id} value={v.id}>{v.marque} {v.modele} {v.plaque ? `(${v.plaque})` : ""}</option>
              ))}
            </Select>
          </div>
        )}
        <div className="space-y-4">
          <TextArea label="Description des travaux *" value={form.description_travaux} onChange={set("description_travaux")} error={errors.description_travaux} />
          <div className="grid grid-cols-2 gap-4">
            <Input label="Km entree" type="number" value={form.km_entree} onChange={set("km_entree")} />
            <Input label="Date sortie prevue" type="datetime-local" value={form.date_sortie_prevue} onChange={set("date_sortie_prevue")} />
          </div>
          <TextArea label="Notes internes" value={form.notes_internes} onChange={set("notes_internes")} />
        </div>
        <div className="flex justify-end gap-3 mt-6">
          <button onClick={() => setModalOpen(false)} className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50">
            Annuler
          </button>
          <button onClick={handleSave} disabled={saving} className="px-4 py-2 text-sm bg-accent text-white rounded-lg hover:bg-accent-hover disabled:opacity-50">
            {saving ? "..." : editing ? "Enregistrer" : "Creer"}
          </button>
        </div>
      </Modal>
      <ConfirmDialog
        open={!!statutConfirm}
        onClose={() => setStatutConfirm(null)}
        onConfirm={confirmChangeStatut}
        loading={changingStatut}
        title="Confirmer le changement de statut"
        message={statutConfirm
          ? `Passer l'ordre ${statutConfirm.ordre.numero} en "${statutConfirm.newStatut}" ?`
          : ""}
      />
    </div>
  );
}
