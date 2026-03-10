import { NavLink } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { logout } from "../../features/auth/authSlice";
import {
  LayoutDashboard,
  Users,
  Car,
  Wrench,
  LogOut,
} from "lucide-react";

const links = [
  { to: "/", icon: LayoutDashboard, label: "Tableau de bord" },
  { to: "/clients", icon: Users, label: "Clients" },
  { to: "/vehicules", icon: Car, label: "Vehicules" },
  { to: "/ordres", icon: Wrench, label: "Ordres de travail" },
];

export default function Sidebar() {
  const dispatch = useDispatch();
  const garage = useSelector((s) => s.auth.garage);

  return (
    <aside className="fixed left-0 top-0 h-screen w-60 bg-sidebar flex flex-col text-white">
      <div className="px-5 py-6 border-b border-white/10">
        <h1 className="text-lg font-semibold tracking-tight">
          Me<span className="text-accent">kano</span>
        </h1>
        {garage && (
          <p className="text-xs text-gray-400 mt-1 truncate">{garage.nom}</p>
        )}
      </div>

      <nav className="flex-1 py-4 px-3 space-y-1">
        {links.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                isActive
                  ? "bg-sidebar-active text-white font-medium"
                  : "text-gray-400 hover:bg-sidebar-hover hover:text-white"
              }`
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="p-3 border-t border-white/10">
        <button
          onClick={() => dispatch(logout())}
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-400 hover:bg-sidebar-hover hover:text-white w-full transition-colors"
        >
          <LogOut size={18} />
          Deconnexion
        </button>
      </div>
    </aside>
  );
}
