import { useSelector } from "react-redux";

export default function Header() {
  const user = useSelector((s) => s.auth.user);

  return (
    <header className="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-6">
      <div />
      <div className="flex items-center gap-3">
        {user && (
          <span className="text-sm text-gray-600">
            {user.prenom} {user.nom}
          </span>
        )}
        <div className="w-8 h-8 rounded-full bg-accent text-white flex items-center justify-center text-xs font-medium">
          {user ? (user.prenom?.[0] || "") + (user.nom?.[0] || "") : "?"}
        </div>
      </div>
    </header>
  );
}
