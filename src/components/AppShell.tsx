import {
  Bell,
  ChevronDown,
  LogOut,
  Menu,
  Search,
  Settings,
  User,
  WandSparkles,
} from "lucide-react";
import { motion } from "framer-motion";
import { BrandMark } from "./BrandMark";
import type { IconType, Screen } from "../types";

export function Sidebar({
  navItems,
  active,
  setScreen,
}: {
  navItems: { label: string; icon: IconType; target: Screen }[];
  active: Screen;
  setScreen: (screen: Screen) => void;
}) {
  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("selectedAlbum");
    
    setScreen("login");
  };
  return (
    <aside className="fixed inset-y-0 left-0 z-30 hidden w-72 border-r border-slate-200/80 bg-white/85 p-5 shadow-sm backdrop-blur-xl lg:block">
      <BrandMark />
      <nav className="mt-10 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive =
            active === item.target ||
            (active === "album" && item.label === "Albums");
          return (
            <button
              key={item.label}
              onClick={() => setScreen(item.target)}
              className={`flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm font-semibold transition ${isActive ? "bg-blue-50 text-[#1E3A8A] shadow-sm ring-1 ring-blue-100" : "text-slate-600 hover:bg-slate-50 hover:text-slate-950"}`}
            >
              <Icon className="h-5 w-5" /> {item.label}
            </button>
          );
        })}
      </nav>
      <div className="absolute bottom-5 left-5 right-5 rounded-2xl border border-blue-100 bg-gradient-to-br from-blue-50 to-cyan-50 p-4">
        <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-white text-blue-800 shadow-sm">
          <WandSparkles className="h-5 w-5" />
        </div>
        <p className="font-semibold text-slate-950">AI credits</p>
        <p className="mt-1 text-sm text-slate-500">
          18,420 faces indexed this month
        </p>
        <div className="mt-4 h-2 rounded-full bg-white">
          <div className="h-full w-3/4 rounded-full bg-cyan-500" />
        </div>
        <button
          onClick={handleLogout}
          className="mt-5 flex items-center gap-2 text-sm font-semibold text-slate-500 hover:text-red-600"
        >
          <LogOut className="h-5 w-5 shrink-0" /> Logout
        </button>
      </div>
    </aside>
  );
}

export function Topbar({
  setScreen,
  profileOpen,
  setProfileOpen,
}: {
  setScreen: (screen: Screen) => void;
  profileOpen: boolean;
  setProfileOpen: (open: boolean) => void;
}) {
  return (
    <header className="sticky top-0 z-20 border-b border-slate-200/80 bg-white/75 backdrop-blur-xl">
      <div className="flex h-20 items-center justify-between px-5 sm:px-8 lg:px-10">
        <div className="flex items-center gap-3">
          <button className="rounded-xl border border-slate-200 bg-white p-2 text-slate-600 lg:hidden">
            <Menu className="h-5 w-5" />
          </button>
          <div className="hidden rounded-full border border-slate-200 bg-white px-3 py-2 text-sm text-slate-500 sm:flex sm:items-center sm:gap-2">
            <Search className="h-4 w-4" /> Search albums, faces, clients...
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button className="relative rounded-xl border border-slate-200 bg-white p-2.5 text-slate-600 shadow-sm hover:text-blue-800">
            <Bell className="h-5 w-5" />
            <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-cyan-500" />
          </button>
          <div className="relative">
            <button
              onClick={() => setProfileOpen(!profileOpen)}
              className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white px-3 py-2 shadow-sm transition hover:border-blue-200"
            >
              <div className="h-9 w-9 overflow-hidden rounded-full bg-blue-100">
                <img
                  src="https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=120&q=80"
                  alt="Profile avatar"
                  className="h-full w-full object-cover"
                />
              </div>
              <div className="hidden text-left sm:block">
                <p className="text-sm font-semibold text-slate-900">
                  Maya Studio
                </p>
                <p className="text-xs text-slate-500">Owner</p>
              </div>
              <ChevronDown className="h-4 w-4 text-slate-400" />
            </button>
            {profileOpen && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="absolute right-0 mt-3 w-56 overflow-hidden rounded-2xl border border-slate-200 bg-white p-2 shadow-2xl shadow-slate-900/10"
              >
                <button
                  onClick={() => setScreen("dashboard")}
                  className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-50"
                >
                  <User className="h-4 w-4" /> Profile
                </button>
                <button
                  onClick={() => setScreen("settings")}
                  className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-50"
                >
                  <Settings className="h-4 w-4" /> Settings
                </button>
                <button
                  onClick={() => setScreen("login")}
                  className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-50"
                >
                  <LogOut className="h-4 w-4" /> Logout
                </button>
              </motion.div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
