import { useState, useEffect, useCallback, useRef } from "react";
import { Users, Search, Pencil, Trash2 } from "lucide-react";
import { api, debounce, validators } from "../api";
import Modal from "../components/ui/Modal";
import ConfirmDialog from "../components/ui/ConfirmDialog";
import Pagination from "../components/ui/Pagination";
import Input, { TextArea } from "../components/ui/Input";
import { SkeletonTable } from "../components/ui/Skeleton";

const EMPTY = {
  prenom: "", nom: "", entreprise: "", adresse: "", npa: "",
  localite: "", telephone: "", email: "", date_naissance: "", notes: "",
};

function validateForm(form) {
  const errors = {};
  if (!form.prenom.trim()) errors.prenom = "Prénom requis";
  if (!form.nom.trim()) errors.nom = "Nom requis";
  if (form.email && !validators.email(form.email))
    errors.email = "Format email invalide";
  if (form.notes && !validators.maxLength(form.notes, 5000))
    errors.notes = "Maximum 5000 caractères";
  if (form.npa && form.npa.length > 10)
    errors.npa = "Maximum 10 caractères";
  return errors;
}

export default function Clients() {
  const [data, setData] = useState({ items: [], total: 0, page: 1, pages: 1 });
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(EMPTY);
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);

  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const load = useCallback(async (q = search, p = page) => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page: p, per_page: 25 });
      if (q) params.set("search", q);
      const res = await api.get(`/api/clients?${params}`);
      setData(res);
    } catch { /* handled by api.js */ }
    setLoading(false);
  }, [search, page]);

  // Debounced search — 300ms
  const debouncedLoad = useRef(debounce((q) => {
    setPage(1);
    load(q, 1);
  }, 300)).current;

  useEffect(() => { load(); }, [page]);

  const handleSearch = (e) => {
    setSearch(e.target.value);
    debouncedLoad(e.target.value);
  };

  const openCreate = () => {
    setEditing(null);
    setForm(EMPTY);
    setErrors({});
    setModalOpen(true);
  };

  const openEdit = (client) => {
    setEditing(client);
    setForm({
      prenom: client.prenom || "",
      nom: client.nom || "",
      entreprise: client.entreprise || "",
      adresse: client.adresse || "",
      npa: client.npa || "",
      localite: client.localite || "",
      telephone: client.telephone || "",
      email: client.email || "",
      date_naissance: client.date_naissance || "",
      notes: client.notes || "",
    });
    setErrors({});
    setModalOpen(true);
  };

  const handleSave = async () => {
    // Frontend validation before sending
    const frontErrors = validateForm(form);
    if (Object.keys(frontErrors).length > 0) {
      setErrors(frontErrors);
      return;
    }
    setSaving(true);
    setErrors({});
    try {
      if (editing) {
        await api.put(`/api/clients/${editing.id}`, form);
      } else {
        await api.post("/api/clients", form);
      }
      setModalOpen(false);
      load();
    } catch (err) {
      if (err.errors) setErrors(err.errors);
    }
    setSaving(false);
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await api.delete(`/api/clients/${deleteTarget.id}`);
      setDeleteTarget(null);
      load();
    } catch { /* */ }
    setDeleting(false);
  };

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold">Clients</h2>
        <button onClick={openCreate} className="bg-accent hover:bg-accent-hover text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors">
          + Nouveau client
        </button>
      </div>

      <div className="bg-white rounded-xl border border-gray-200">
        <div className="p-4 border-b border-gray-200">
          <div className="relative max-w-sm">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Rechercher un client..."
              value={search}
              onChange={handleSearch}
              className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent"
            />
          </div>
        </div>

        {loading ? (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left text-gray-500 text-xs uppercase tracking-wider">
                <th className="px-4 py-3">Nom</th>
                <th className="px-4 py-3">Email</th>
                <th className="px-4 py-3">Téléphone</th>
                <th className="px-4 py-3">Localité</th>
                <th className="px-4 py-3 w-20"></th>
              </tr>
            </thead>
            <SkeletonTable rows={5} cols={5} />
          </table>
        ) : data.items.length === 0 ? (
          <div className="p-12 text-center">
            <Users size={40} className="text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500 text-sm">Aucun client trouvé</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left text-gray-500 text-xs uppercase tracking-wider">
                <th className="px-4 py-3">Nom</th>
                <th className="px-4 py-3">Email</th>
                <th className="px-4 py-3">Téléphone</th>
                <th className="px-4 py-3">Localité</th>
                <th className="px-4 py-3 w-20"></th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((c) => (
                <tr key={c.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">
                    {c.prenom} {c.nom}
                    {c.entreprise && <span className="text-gray-400 ml-1">({c.entreprise})</span>}
                  </td>
                  <td className="px-4 py-3 text-gray-600">{c.email || "-"}</td>
                  <td className="px-4 py-3 text-gray-600 font-mono text-xs">{c.telephone || "-"}</td>
                  <td className="px-4 py-3 text-gray-600">{c.npa} {c.localite}</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-1">
                      <button onClick={() => openEdit(c)} className="p-1.5 rounded hover:bg-gray-100 text-gray-400 hover:text-accent">
                        <Pencil size={14} />
                      </button>
                      <button onClick={() => setDeleteTarget(c)} className="p-1.5 rounded hover:bg-gray-100 text-gray-400 hover:text-red-500">
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        <Pagination page={data.page} pages={data.pages} total={data.total} onChange={setPage} />
      </div>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={editing ? "Modifier le client" : "Nouveau client"} wide>
        <div className="grid grid-cols-2 gap-4">
          <Input label="Prénom *" value={form.prenom} onChange={set("prenom")} error={errors.prenom} />
          <Input label="Nom *" value={form.nom} onChange={set("nom")} error={errors.nom} />
          <Input label="Entreprise" value={form.entreprise} onChange={set("entreprise")} />
          <Input label="Email" type="email" value={form.email} onChange={set("email")} error={errors.email} />
          <Input label="Téléphone" value={form.telephone} onChange={set("telephone")} />
          <Input label="Date de naissance" type="date" value={form.date_naissance} onChange={set("date_naissance")} />
          <Input label="Adresse" value={form.adresse} onChange={set("adresse")} />
          <div className="grid grid-cols-2 gap-2">
            <Input label="NPA" value={form.npa} onChange={set("npa")} error={errors.npa} />
            <Input label="Localité" value={form.localite} onChange={set("localite")} />
          </div>
        </div>
        <div className="mt-4">
          <TextArea label="Notes" value={form.notes} onChange={set("notes")} error={errors.notes} maxLength={5000} />
          {form.notes && <p className="text-xs text-gray-400 mt-1 text-right">{form.notes.length}/5000</p>}
        </div>
        <div className="flex justify-end gap-3 mt-6">
          <button onClick={() => setModalOpen(false)} className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50">
            Annuler
          </button>
          <button onClick={handleSave} disabled={saving} className="px-4 py-2 text-sm bg-accent text-white rounded-lg hover:bg-accent-hover disabled:opacity-50">
            {saving ? "Enregistrement..." : editing ? "Enregistrer" : "Créer"}
          </button>
        </div>
      </Modal>

      <ConfirmDialog
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        loading={deleting}
        title="Supprimer le client"
        message={deleteTarget ? `Supprimer ${deleteTarget.prenom} ${deleteTarget.nom} ? Les véhicules associés ne seront plus visibles.` : ""}
      />
    </div>
  );
}
