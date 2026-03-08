import { useState, useEffect, useCallback } from "react";
import { Car, Search, Pencil } from "lucide-react";
import { api } from "../api";
import Modal from "../components/ui/Modal";
import Pagination from "../components/ui/Pagination";
import Input, { TextArea, Select } from "../components/ui/Input";

const EMPTY = {
  client_id: "", marque: "", modele: "", annee: "", plaque: "",
  vin: "", couleur: "", carburant: "", km_actuel: "", date_mct: "", notes: "",
};

const CARBURANTS = ["essence", "diesel", "electrique", "hybride", "gaz"];

export default function Vehicules() {
  const [data, setData] = useState({ items: [], total: 0, page: 1, pages: 1 });
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);

  const [clients, setClients] = useState([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(EMPTY);
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page, per_page: 25 });
      if (search) params.set("search", search);
      const res = await api.get(`/api/vehicules?${params}`);
      setData(res);
    } catch { /* */ }
    setLoading(false);
  }, [page, search]);

  useEffect(() => { load(); }, [load]);

  const loadClients = async () => {
    try {
      const res = await api.get("/api/clients?per_page=500");
      setClients(res.items);
    } catch { /* */ }
  };

  const openCreate = () => {
    setEditing(null);
    setForm(EMPTY);
    setErrors({});
    loadClients();
    setModalOpen(true);
  };

  const openEdit = (v) => {
    setEditing(v);
    setForm({
      client_id: v.client_id || "",
      marque: v.marque || "",
      modele: v.modele || "",
      annee: v.annee || "",
      plaque: v.plaque || "",
      vin: v.vin || "",
      couleur: v.couleur || "",
      carburant: v.carburant || "",
      km_actuel: v.km_actuel || "",
      date_mct: v.date_mct || "",
      notes: v.notes || "",
    });
    setErrors({});
    loadClients();
    setModalOpen(true);
  };

  const handleSave = async () => {
    setSaving(true);
    setErrors({});
    const payload = {
      ...form,
      client_id: form.client_id ? Number(form.client_id) : null,
      annee: form.annee ? Number(form.annee) : null,
      km_actuel: form.km_actuel ? Number(form.km_actuel) : null,
    };
    try {
      if (editing) {
        await api.put(`/api/vehicules/${editing.id}`, payload);
      } else {
        await api.post("/api/vehicules", payload);
      }
      setModalOpen(false);
      load();
    } catch (err) {
      if (err.errors) setErrors(err.errors);
    }
    setSaving(false);
  };

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold">Vehicules</h2>
        <button onClick={openCreate} className="bg-accent hover:bg-accent-hover text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors">
          + Nouveau vehicule
        </button>
      </div>

      <div className="bg-white rounded-xl border border-gray-200">
        <div className="p-4 border-b border-gray-200">
          <div className="relative max-w-sm">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Rechercher (marque, modele, plaque)..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent"
            />
          </div>
        </div>

        {loading ? (
          <div className="p-12 text-center text-gray-400 text-sm">Chargement...</div>
        ) : data.items.length === 0 ? (
          <div className="p-12 text-center">
            <Car size={40} className="text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500 text-sm">Aucun vehicule trouve</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left text-gray-500 text-xs uppercase tracking-wider">
                <th className="px-4 py-3">Vehicule</th>
                <th className="px-4 py-3">Plaque</th>
                <th className="px-4 py-3">Client</th>
                <th className="px-4 py-3">Km</th>
                <th className="px-4 py-3">MCT</th>
                <th className="px-4 py-3 w-12"></th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((v) => (
                <tr key={v.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <span className="font-medium">{v.marque} {v.modele}</span>
                    {v.annee && <span className="text-gray-400 ml-1">({v.annee})</span>}
                    {v.couleur && <span className="text-gray-400 ml-1">- {v.couleur}</span>}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs font-medium">{v.plaque || "-"}</td>
                  <td className="px-4 py-3 text-gray-600">{v.client_nom || "-"}</td>
                  <td className="px-4 py-3 font-mono text-xs">{v.km_actuel ? v.km_actuel.toLocaleString() : "-"}</td>
                  <td className="px-4 py-3 text-xs">{v.date_mct || "-"}</td>
                  <td className="px-4 py-3">
                    <button onClick={() => openEdit(v)} className="p-1.5 rounded hover:bg-gray-100 text-gray-400 hover:text-accent">
                      <Pencil size={14} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        <Pagination page={data.page} pages={data.pages} total={data.total} onChange={setPage} />
      </div>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={editing ? "Modifier le vehicule" : "Nouveau vehicule"} wide>
        {!editing && (
          <div className="mb-4">
            <Select label="Client *" value={form.client_id} onChange={set("client_id")} error={errors.client_id}>
              <option value="">-- Choisir un client --</option>
              {clients.map((c) => (
                <option key={c.id} value={c.id}>{c.prenom} {c.nom}{c.entreprise ? ` (${c.entreprise})` : ""}</option>
              ))}
            </Select>
          </div>
        )}
        <div className="grid grid-cols-2 gap-4">
          <Input label="Marque *" value={form.marque} onChange={set("marque")} error={errors.marque} />
          <Input label="Modele *" value={form.modele} onChange={set("modele")} error={errors.modele} />
          <Input label="Annee" type="number" value={form.annee} onChange={set("annee")} />
          <Input label="Couleur" value={form.couleur} onChange={set("couleur")} />
          <Input label="Plaque CH (ex: VD 345678)" value={form.plaque} onChange={set("plaque")} error={errors.plaque} placeholder="VD 345678" />
          <Input label="VIN" value={form.vin} onChange={set("vin")} maxLength={17} className="font-mono" />
          <Select label="Carburant" value={form.carburant} onChange={set("carburant")}>
            <option value="">--</option>
            {CARBURANTS.map((c) => <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>)}
          </Select>
          <Input label="Km actuel" type="number" value={form.km_actuel} onChange={set("km_actuel")} />
          <Input label="Prochain MCT" type="date" value={form.date_mct} onChange={set("date_mct")} />
        </div>
        <div className="mt-4">
          <TextArea label="Notes" value={form.notes} onChange={set("notes")} />
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
    </div>
  );
}
