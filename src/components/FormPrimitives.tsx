import { AlertCircle, Cloud } from "lucide-react";
import type { IconType } from "../types";

export function Input({
  label,
  icon: Icon,
  placeholder,
  type = "text",
  error,
  value,
  onChange,
}: {
  label: string;
  icon: IconType;
  placeholder: string;
  type?: string;
  error?: string;
  value?: string;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
}) {
  return (
    <label className="block">
      <span className="mb-2 block text-sm font-semibold text-slate-700">
        {label}
      </span>
      <div
        className={`flex items-center gap-3 rounded-xl border bg-white px-4 py-3 transition focus-within:ring-4 ${error ? "border-red-300 focus-within:ring-red-100" : "border-slate-200 focus-within:border-cyan-400 focus-within:ring-cyan-100"}`}
      >
        <Icon className="h-5 w-5 text-slate-400" />
        <input
            type={type}
            placeholder={placeholder}
            value={value}
            onChange={onChange}
          className="w-full bg-transp
          arent text-sm text-slate-900 outline-none placeholder:text-slate-400"
        />
      </div>
      {error && (
        <p className="mt-2 flex items-center gap-1.5 text-sm font-medium text-red-600">
          <AlertCircle className="h-4 w-4" />
          {error}
        </p>
      )}
    </label>
  );
}

export function ErrorMessage({ text }: { text: string }) {
  return (
    <div className="mt-4 flex items-start gap-3 rounded-2xl border border-red-100 bg-red-50 p-3 text-sm text-red-700">
      <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
      <span>{text}</span>
    </div>
  );
}

export function EmptyState({
  title,
  text,
  action,
  onAction,
}: {
  title: string;
  text: string;
  action: string;
  onAction: () => void;
}) {
  return (
    <div className="flex min-h-[360px] flex-col items-center justify-center rounded-3xl border border-dashed border-slate-200 bg-white p-8 text-center shadow-sm">
      <div className="rounded-3xl bg-blue-50 p-5 text-blue-800">
        <Cloud className="h-10 w-10" />
      </div>
      <h2 className="mt-5 text-2xl font-bold text-slate-950">{title}</h2>
      <p className="mt-2 max-w-md text-slate-500">{text}</p>
      <button
        onClick={onAction}
        className="mt-6 rounded-xl bg-[#1E3A8A] px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-900/20"
      >
        {action}
      </button>
    </div>
  );
}

export function ToggleRow({
  title,
  active,
}: {
  title: string;
  active: boolean;
}) {
  return (
    <div className="flex items-center justify-between rounded-2xl border border-slate-200 p-4">
      <p className="font-semibold text-slate-800">{title}</p>
      <div
        className={`flex h-7 w-12 items-center rounded-full p-1 ${active ? "bg-cyan-500" : "bg-slate-200"}`}
      >
        <span
          className={`h-5 w-5 rounded-full bg-white shadow ${active ? "translate-x-5" : ""}`}
        />
      </div>
    </div>
  );
}
