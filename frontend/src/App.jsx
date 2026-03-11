import { Routes, Route, Navigate } from "react-router-dom";
import { useSelector } from "react-redux";
import Layout from "./components/layout/Layout";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Clients from "./pages/Clients";
import Vehicules from "./pages/Vehicules";
import OrdresTravail from "./pages/OrdresTravail";
import Devis from "./pages/Devis";
import DevisForm from "./pages/DevisForm";

function PrivateRoute({ children }) {
  const token = useSelector((s) => s.auth.token);
  return token ? children : <Navigate to="/login" />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <PrivateRoute>
            <Layout />
          </PrivateRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="clients" element={<Clients />} />
        <Route path="vehicules" element={<Vehicules />} />
        <Route path="ordres" element={<OrdresTravail />} />
        <Route path="devis" element={<Devis />} />
        <Route path="devis/nouveau" element={<DevisForm />} />
        <Route path="devis/:id" element={<DevisForm />} />
      </Route>
    </Routes>
  );
}
